"""Local pre-publish audit. Reports locations/counts only, never matched credential bytes.

Scans tracked working files and every blob reachable from local refs. Private files
are comparison inputs held in memory, not copied into the report or Git.
"""
import html
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    'OpenAI-shaped key': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b'),
    'GitHub-shaped token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'AWS access key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'JWT-shaped credential': re.compile(rb'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'),
    'Private key block': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'Literal bearer credential': re.compile(rb'\bBearer [A-Za-z0-9_.-]{40,}'),
    'Literal secret assignment': re.compile(rb'''(?i)["']?(?:api_key|access_token|refresh_token|client_secret|password)["']?\s*[:=]\s*["']([A-Za-z0-9_./+=-]{32,})["']'''),
}


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def forbidden_path(path: str) -> bool:
    parts = path.replace('\\', '/').lower().split('/')
    basename = parts[-1]
    return (path.replace('\\', '/').lower().startswith(('artifacts/private/', 'workspaces/'))
            or basename in ('auth.json', 'credentials.json', 'gold.patch', 'oracle.patch')
            or (basename == '.env' or basename.startswith('.env.')) and basename != '.env.example'
            or any(p in ('.ssh', '.aws') or p.startswith('.pytest-tmp-') for p in parts))


def scan_bytes(data: bytes, credentials: list[bytes], private_payloads: list[bytes]) -> list[str]:
    """Return finding categories only. Never return a regex match or compared bytes."""
    hits = [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(data)]
    if any(value in data for value in credentials):
        hits.append('Known local credential value')
    if any(value in data for value in private_payloads):
        hits.append('Known full private gold/oracle payload')
    return hits


def credential_values(value: object, key: str = '') -> list[bytes]:
    if isinstance(value, dict):
        return [b for k, v in value.items() for b in credential_values(v, k)]
    if isinstance(value, list):
        return [b for v in value for b in credential_values(v, key)]
    if isinstance(value, str) and len(value) >= 16 and re.search('token|secret|key|password', key, re.I):
        return [value.encode()]
    return []


def payload_forms(text: str) -> list[bytes]:
    text = text.replace('\r\n', '\n').strip()
    return [text.encode(), text.replace('\n', '\r\n').encode(),
            json.dumps(text)[1:-1].encode(), html.escape(text).encode()]


def added_test_blocks(text: str) -> list[str]:
    blocks, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('+') and not line.startswith('+++'):
            current.append(line[1:])
        else:
            block = '\n'.join(current)
            if len(block) >= 120 and re.search(r'^def test_', block, re.M):
                blocks.append(block)
            current = []
    return blocks


def audit() -> dict:
    tracked = [p.decode('utf-8') for p in git('ls-files', '-z').split(b'\0') if p]
    objects = []
    for line in git('rev-list', '--all', '--objects').decode().splitlines():
        oid, _, path = line.partition(' ')
        objects.append((oid, path))
    # rev-list gives only one name per object, so check every commit tree's paths too.
    historical_paths = set()
    for commit in git('rev-list', '--all').decode().splitlines():
        historical_paths.update(p.decode('utf-8') for p in git('ls-tree', '-r', '--name-only', '-z', commit).split(b'\0') if p)
    # A batch stream avoids spawning a Git process for every historical blob.
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    blobs, messages = [], []
    try:
        for oid, path in objects:
            proc.stdin.write((oid+'\n').encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().strip().split()
            payload = proc.stdout.read(int(header[2]))
            assert proc.stdout.read(1) == b'\n'
            if header[1] == 'blob':
                blobs.append((oid, path, payload))
            elif header[1] in ('commit', 'tag'):
                messages.append((oid, header[1], payload))
    finally:
        proc.stdin.close()
        proc.stdout.close()
        proc.wait(timeout=10)

    auth_path = Path.home()/'.codex/auth.json'
    credentials = credential_values(json.loads(auth_path.read_text(encoding='utf-8')))
    assert credentials, 'Known credential comparison is unavailable'
    env_paths = [p for p in ROOT.glob('.env*') if p.name != '.env.example' and p.is_file()]
    for env in env_paths:
        for line in env.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.partition('=')
            value = value.strip().strip('"\'')
            if sep and len(value) >= 16 and re.search('token|secret|key|password', key, re.I):
                credentials.append(value.encode())

    private = list((ROOT/'artifacts/private/m1-v7/candidates').glob('*/gold.patch')) + list(
        (ROOT/'artifacts/private/m1-v7/candidates').glob('*/oracle.patch'))
    assert private, 'Private artifact comparison corpus is unavailable'
    payloads, blocks = [], []
    for path in private:
        text = path.read_text(encoding='utf-8')
        payloads.extend(payload_forms(text))
        if path.name == 'oracle.patch':
            blocks.extend(added_test_blocks(text))
    payloads.extend(value for block in blocks for value in payload_forms(block))
    findings = []
    for path in tracked:
        if forbidden_path(path):
            findings.append({'scope': 'tracked working file', 'path': path, 'kind': 'Forbidden path'})
        for kind in scan_bytes((ROOT/path).read_bytes(), credentials, payloads):
            findings.append({'scope': 'tracked working file', 'path': path, 'kind': kind})
    for oid, path, data in blobs:
        if forbidden_path(path):
            findings.append({'scope': 'reachable history', 'path': path, 'object': oid, 'kind': 'Forbidden path'})
        for kind in scan_bytes(data, credentials, payloads):
            findings.append({'scope': 'reachable history', 'path': path, 'object': oid, 'kind': kind})
    for path in sorted(historical_paths):
        if forbidden_path(path):
            findings.append({'scope': 'reachable commit tree', 'path': path, 'kind': 'Forbidden path'})
    for oid, kind, data in messages:
        for hit in scan_bytes(data, credentials, payloads):
            findings.append({'scope': 'reachable '+kind+' object', 'object': oid, 'kind': hit})
    ignore_probes = ['.env', '.env.local', 'artifacts/private/auth.json', 'artifacts/private/gold.patch', 'workspaces/task/.env', '.pytest-tmp-local-001/result.json']
    ignored = git('check-ignore', '--no-index', '--', *ignore_probes).decode().splitlines()
    assert set(ignored) == set(ignore_probes)
    return {'status': 'passed' if not findings else 'review_required', 'head_at_scan': git('rev-parse', 'HEAD').decode().strip(),
            'reachable_commits': int(git('rev-list', '--all', '--count')),
            'tracked_working_files': len(tracked), 'reachable_blobs': len(blobs),
            'unique_historical_paths_checked': len(historical_paths), 'commit_tag_objects_checked': len(messages),
            'auth_comparison': 'Current local auth token values compared in memory; no values copied or reported.',
            'known_credential_values_compared': len(credentials), 'local_env_files_checked': len(env_paths),
            'private_gold_oracle_payloads_compared': len(private), 'added_hidden_test_blocks_compared': len(blocks),
            'ignore_probes_passed': ignored,
            'findings': findings,
            'scope': 'Tracked working files and all blobs reachable from local refs; no publication or remote push.',
            'limitations': 'Pattern and known-value scanning is not a proof against every possible secret encoding. Private raw traces and task/oracle stores remain ignored on disk. Public metadata includes commit IDs, test names, aggregate verdicts and reviewed agent evidence. Public historical fixes can be recovered from upstream history, so this dataset is not a reusable untouched held-out benchmark after disclosure.'}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
