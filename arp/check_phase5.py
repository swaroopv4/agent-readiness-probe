"""Validate a plain-folder public snapshot without Git or private-store writes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
from urllib.parse import unquote
from .check_m4 import Snapshot
from .m4_report import render
from .check_publication import (forbidden_path, scan_bytes, credential_values,
                                payload_forms, added_test_blocks)

ROOT = Path(__file__).resolve().parents[1]

# Exact document/target pairs approved as withheld private dependencies.
KNOWN_UNAVAILABLE_LINKS = {
    ('docs/m1_results.md', '../artifacts/private/isolation-probe-v1/result.json'),
    ('docs/m1_results.md', '../artifacts/private/m1-v7/review_packet.md'),
    ('docs/m1_results.md', '../artifacts/private/m1-v7/human_review.csv'),
    ('docs/m3_human_review.md', '../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/testing.py'),
    ('docs/m3_human_review.md', '../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/_compat.py'),
    ('docs/m3_human_review.md', '../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/globals.py'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def document_links():
    count, unavailable = 0, set()
    for path in sorted(ROOT.rglob('*.md')):
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'^```.*?^```[^\n]*$', '', text, flags=re.M | re.S)
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            target = target.strip('<>')
            pair = (path.relative_to(ROOT).as_posix(), target)
            if pair in KNOWN_UNAVAILABLE_LINKS:
                unavailable.add(pair)
                continue
            filename, _, anchor = target.partition('#')
            destination = (path.parent/unquote(filename)).resolve() if filename else path
            assert destination.is_relative_to(ROOT) and destination.exists(), (pair[0], target)
            if anchor and destination.suffix == '.md':
                headings = re.findall(r'^#+ (.+)$', destination.read_text(encoding='utf-8'), re.M)
                slugs = {re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings}
                assert unquote(anchor) in slugs, (pair[0], target)
            count += 1
    assert unavailable == KNOWN_UNAVAILABLE_LINKS, 'Approved dependency links changed'
    return {'resolved_local_links_checked': count,
            'known_unavailable_dependencies': [{'document': doc, 'target': target}
                                               for doc, target in sorted(unavailable)],
            'unexpected_unresolved_links': 0}


def report_consistency():
    def load(name):
        return json.loads((ROOT/name).read_text(encoding='utf-8'))
    d, s, p = (load(name) for name in ('results/m4_diagnostics.json', 'results/m5_summary.json', 'results/m5_plan.json'))
    h, a, m1 = (load(name) for name in ('review/m3_human_labels.json', 'results/m3_agreement.json', 'results/m1_summary.json'))
    agents = (ROOT/p['intervention_path']).read_text(encoding='utf-8')
    report = ROOT/'reports/click_readiness.html'
    text = report.read_text(encoding='utf-8')
    assert text == render(d, s, p, h, a, m1, agents), 'Report differs from recorded inputs'
    parser = Snapshot()
    parser.feed(text)
    embedded = json.loads(parser.data)
    assert embedded['M5'] == s and embedded['human_labels'] == h and embedded['diagnostics'] == d
    assert not parser.external_assets and not parser.active_scripts
    assert len(d['attempts']) == len({(r['task_id'], r['arm'], r['repeat']) for r in d['attempts']}) == 48
    for name, expected in d['sources'].items():
        assert digest(ROOT/name) == expected, ('Recorded report source changed', name)
    freeze = load('results/m3_freeze.json')
    for record in (freeze, p):
        for name, expected in record['source_sha256'].items():
            actual = hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            assert actual == expected, ('Frozen experiment source changed', name)
        for prefix in ('intervention', 'common_prompt'):
            assert digest(ROOT/record[prefix+'_path']) == record[prefix+'_sha256']
    assert digest(ROOT/freeze['rubric_path']) == freeze['rubric_sha256']
    assert digest(ROOT/'results/m3_freeze.json') == p['m3_freeze_sha256']
    assert digest(ROOT/'review/m3_human_labels.json') == a['human_labels_sha256']
    return {'status': 'passed', 'attempts': 48, 'report_sha256': digest(report),
            'frozen_source_hashes': 'passed',
            'raw_trace_audit': 'Not performed: raw traces remain private.'}


def folder_scan(comparison_root=None):
    credentials, payloads, blocks, private, env_paths = [], [], [], [], []
    if comparison_root is not None:
        comparison_root = Path(comparison_root).resolve()
        assert comparison_root != ROOT, 'Comparison corpus must stay outside the snapshot'
        auth = Path.home()/'.codex/auth.json'
        credentials = credential_values(json.loads(auth.read_text(encoding='utf-8')))
        assert credentials, 'Known credential comparison unavailable'
        env_paths = [p for p in comparison_root.glob('.env*') if p.name != '.env.example' and p.is_file()]
        for env in env_paths:
            for line in env.read_text(encoding='utf-8').splitlines():
                key, sep, value = line.partition('=')
                value = value.strip().strip(chr(34)+chr(39))
                if sep and len(value) >= 16 and re.search('token|secret|key|password', key, re.I):
                    credentials.append(value.encode())
        candidates = comparison_root/'artifacts/private/m1-v7/candidates'
        private = list(candidates.glob('*/gold.patch')) + list(candidates.glob('*/oracle.patch'))
        assert private, 'Private comparison corpus unavailable'
        for path in private:
            text = path.read_text(encoding='utf-8')
            payloads.extend(payload_forms(text))
            if path.name == 'oracle.patch':
                blocks.extend(added_test_blocks(text))
        payloads.extend(value for block in blocks for value in payload_forms(block))
    findings, count = [], 0
    for path in sorted(ROOT.rglob('*')):
        name = path.relative_to(ROOT).as_posix()
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
            findings.append({'path': name, 'kind': 'Link or junction'})
        if '.git' in path.parts or forbidden_path(name):
            findings.append({'path': name, 'kind': 'Forbidden path'})
        if path.is_file():
            count += 1
            for kind in scan_bytes(path.read_bytes(), credentials, payloads):
                findings.append({'path': name, 'kind': kind})
    return {'status': 'passed' if not findings else 'review_required', 'files_scanned': count,
            'known_credential_values_compared': len(credentials), 'local_env_files_checked': len(env_paths),
            'private_gold_oracle_payloads_compared': len(private), 'added_hidden_test_blocks_compared': len(blocks),
            'comparison_inputs': 'Read-only external inputs; values never printed or copied.' if comparison_root else 'Unavailable; pattern/path scan only.',
            'findings': findings, 'git_history': 'Absent: plain folder, no Git operations performed.'}


def check(comparison_root=None):
    links = document_links()
    findings = (ROOT/'docs/findings.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^## [1-5]\. ', findings, re.M)) == 5
    script = (ROOT/'docs/demo_script.md').read_text(encoding='utf-8')
    spoken = re.findall('\u201c(.*?)\u201d', script, re.S)
    words = len(' '.join(spoken).split())
    assert len(spoken) == 6 and 220 <= words <= 280
    report = report_consistency()
    scan = folder_scan(comparison_root)
    return {'status': scan['status'], 'document_links': links, 'findings': 5,
            'spoken_script_words': words, 'spoken_segments': len(spoken),
            'report_consistency': report, 'folder_scan': scan,
            'new_agent_calls': 0, 'new_evaluator_calls': 0, 'paid_api_spend': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison-root', type=Path)
    args = parser.parse_args()
    result = check(args.comparison_root)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)
