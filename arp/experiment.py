"""Frozen input/prompt delivery shared by prospective experiment arms."""
import hashlib
from pathlib import Path
from .linux_runtime import snapshot
from .submissions import InvalidSubmission

ROOT = Path(__file__).resolve().parents[1]


def frozen_bytes(path, digest):
    data = (ROOT/path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Frozen artifact hash differs: '+path)
    return data


def stage_task(base, destination, arm, freeze):
    if arm not in {'baseline','intervention'}: raise ValueError('Unknown arm')
    snapshot(base,destination)
    if (destination/'AGENTS.md').exists(): raise ValueError('Unexpected pre-existing AGENTS file')
    if arm == 'intervention':
        (destination/'AGENTS.md').write_bytes(frozen_bytes(freeze['intervention_path'],freeze['intervention_sha256']))


def common_prompt(task_text, freeze):
    return frozen_bytes(freeze['common_prompt_path'],freeze['common_prompt_sha256']).decode('utf-8')+task_text


def validate_overlay(report, arm, freeze):
    entry=report['files'].get('AGENTS.md')
    if arm == 'intervention' and (not entry or entry.get('sha256') != freeze['intervention_sha256']):
        raise InvalidSubmission('Frozen AGENTS overlay changed or deleted')
