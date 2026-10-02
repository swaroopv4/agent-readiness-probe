"""Validate source-only submissions against an immutable task snapshot."""
from __future__ import annotations
import base64
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import subprocess

class InvalidSubmission(ValueError):
    pass

def production_path(name: str) -> bool:
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts and '\\' not in name
            and ':' not in name and not any(ord(c) < 32 for c in name)
            and not any(p.lower() in {'.git', '.hg', '.svn'} for p in path.parts)
            and len(path.parts) >= 3 and path.parts[:2] == ('src', 'click') and path.suffix == '.py')

def capture_patch(base: Path, report: dict, destination: Path) -> bytes:
    files = report['files']
    for name in files:
        if name.startswith('src/click/') and name.endswith('.py') and not production_path(name):
            raise InvalidSubmission('Unsafe source path: ' + name)
    originals = {p.relative_to(base).as_posix(): p for p in base.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(base).parts}
    for name, original in originals.items():
        if production_path(name):
            continue
        expected = hashlib.sha256(original.read_bytes()).hexdigest()
        if files.get(name, {}).get('sha256') != expected:
            raise InvalidSubmission('Immutable task file changed or deleted: ' + name)
    source = {}
    for name, entry in files.items():
        if production_path(name):
            try:
                data = base64.b64decode(entry['data'], validate=True)
            except (ValueError, KeyError) as error:
                raise InvalidSubmission('Malformed source submission') from error
            if hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise InvalidSubmission('Source hash mismatch: ' + name)
            source[name] = data
        elif name not in originals and (name.startswith('tests/') or name in {'pyproject.toml', 'setup.cfg', 'conftest.py'}):
            raise InvalidSubmission('Unauthorized added evaluator file: ' + name)
    shutil.copytree(base, destination)
    for name in originals:
        if production_path(name) and name not in source:
            (destination / name).unlink()
    for name, data in source.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    # The fresh Git history comes from the trusted snapshot, never the agent's .git.
    subprocess.run(['git', 'add', '--intent-to-add', '--', 'src/click'], cwd=destination, capture_output=True, check=True)
    patch = subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--binary', '--full-index', '--', 'src/click'], cwd=destination, capture_output=True, check=True).stdout
    return patch
