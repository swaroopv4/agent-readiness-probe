"""Inside-container task operations. This file is mounted read-only."""
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

ROOT = Path('/workspace')
LIMIT = 2 * 1024 * 1024

def scoped(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError('Path must identify a file inside /workspace')
    return path

def dispatch(request):
    operation = request['operation']
    if operation == 'read':
        path = scoped(request['path'])
        if path.stat().st_size > LIMIT:
            raise ValueError('File exceeds 2 MiB read limit')
        return {'content': path.read_text(encoding='utf-8')}
    if operation == 'write':
        path = scoped(request['path'])
        text = request['content']
        if len(text.encode('utf-8')) > LIMIT:
            raise ValueError('File exceeds 2 MiB write limit')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return {'written': request['path']}
    if operation == 'shell':
        command = request['command']
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(['/bin/sh', '-c', command], cwd=ROOT,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            timed_out = False
            try:
                code = process.wait(timeout=min(120, max(1, request.get('timeout', 120))))
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
            output.seek(0)
            data = output.read(32769)
        return {'returncode': code, 'timed_out': timed_out,
                'output': data[:32768].decode('utf-8', errors='replace'),
                'truncated': len(data) > 32768}
    if operation == 'collect':
        files = {}
        total = 0
        for path in ROOT.rglob('*'):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith('.git/') or not (path.is_file() or path.is_symlink()):
                continue
            if path.is_symlink():
                raise ValueError('Symlink submission is forbidden: ' + relative)
            if path.stat().st_size > LIMIT:
                raise ValueError('Oversized submission file: ' + relative)
            # Return only file hashes outside production to detect edits, never their contents.
            import hashlib
            data = path.read_bytes()
            if relative.startswith('src/click/') and relative.endswith('.py'):
                total += len(data)
                if total > 10 * LIMIT:
                    raise ValueError('Oversized source submission')
                files[relative] = {'data': base64.b64encode(data).decode(),
                                   'sha256': hashlib.sha256(data).hexdigest()}
            else:
                files[relative] = {'sha256': hashlib.sha256(data).hexdigest()}
        return {'files': files}
    raise ValueError('Unknown operation')

if __name__ == '__main__':
    try:
        request = json.loads(sys.stdin.buffer.read(LIMIT + 1))
        print(json.dumps(dispatch(request)))
    except Exception as error:
        print(json.dumps({'error': type(error).__name__ + ': ' + str(error)}))
        sys.exit(1)
