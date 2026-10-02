"""Run the committed eight M3 baseline repeat-1 attempts, without replacements."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT/'results/m3_freeze.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_freeze():
    freeze=json.loads(FREEZE.read_text(encoding='utf-8'))
    if freeze['status'] != 'frozen_user_approved_before_confirmation': raise ValueError('M3 freeze absent')
    if (freeze['model'],freeze['reasoning_effort']) != ('gpt-5.6-luna','low'): raise ValueError('Model freeze differs')
    from .experiment import frozen_bytes
    frozen_bytes(freeze['intervention_path'],freeze['intervention_sha256'])
    frozen_bytes(freeze['common_prompt_path'],freeze['common_prompt_sha256'])
    frozen_bytes(freeze['rubric_path'],freeze['rubric_sha256'])
    if digest(ROOT/'artifacts/private/m1-v7/tasks.json') != freeze['manifest_sha256']: raise ValueError('Accepted manifest changed')
    for name, expected in freeze['source_sha256'].items():
        # Normalize source line endings to Git's stored LF representation.
        actual=hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        if actual != expected: raise ValueError('Frozen source differs: '+name)
    stored=subprocess.run(['git','show','HEAD:results/m3_freeze.json'],cwd=ROOT,capture_output=True,check=True).stdout
    if json.loads(stored) != freeze: raise ValueError('Freeze must be committed before confirmation launch')
    return freeze


def main():
    from .m2 import run_batch
    freeze=validate_freeze()
    run_batch(ROOT/'artifacts/private/m1-v7',ROOT/'artifacts/private/m3-confirmation-001',
              Path.home()/'.codex/auth.json',freeze['agent_image_id'],freeze['proxy_image_id'],
              confirmation_freeze=freeze)


if __name__=='__main__': main()
