import base64
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import urllib.error
import pytest
from arp.adapters import AdapterConfig, DevinAdapter, Limits, UnsupportedAdapterError, event_result
from arp.submissions import InvalidSubmission, capture_patch, production_path
from arp import task_worker

@pytest.mark.parametrize('cap', [1, -1, 100])
def test_paid_budget_refused(cap):
    with pytest.raises(ValueError): Limits(paid_api_dollars=cap)

def test_devin_never_launches(monkeypatch):
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **kw: pytest.fail('Unsupported adapter must not launch'))
    with pytest.raises(UnsupportedAdapterError): DevinAdapter().prepare()

def test_usage_limit_distinct_from_task_failure():
    raw = b'{"type":"turn.failed","error":{"message":"You have hit your usage limit"}}\n'
    assert event_result(raw, '', 1) == ('usage_limit', 'not measured')

def test_limit_words_in_success_message_do_not_trigger_provider_stop():
    raw = b'{"type":"item.completed","item":{"text":"This change fixes usage limit handling"}}\n{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":3}}\n'
    assert event_result(raw, '', 0) == ('completed', {'turns': [{'input_tokens':10, 'output_tokens':3}]})

def test_exit_zero_without_completed_turn_is_not_success():
    assert event_result(b'{"type":"thread.started"}\n', '', 0)[0] == 'provider_or_transport_failure'

def test_cancel_is_not_repository_failure():
    assert event_result(b'', '', 1, True)[0] == 'cancelled'

@pytest.fixture
def snapshot(tmp_path):
    base = tmp_path/'base'
    (base/'src/click').mkdir(parents=True)
    (base/'tests').mkdir()
    (base/'src/click/a.py').write_bytes(b'value = 1\n')
    (base/'tests/test_a.py').write_bytes(b'assert True\n')
    (base/'TASK.md').write_bytes(b'Task\n')
    for arguments in [('init',),('add','.'),('-c','user.name=Probe','-c','user.email=probe@localhost','-c','commit.gpgsign=false','commit','-m','initial')]:
        subprocess.run(['git', *arguments], cwd=base, capture_output=True, check=True)
    files = {}
    for p in base.rglob('*'):
        if not p.is_file() or '.git' in p.relative_to(base).parts: continue
        name = p.relative_to(base).as_posix()
        data = p.read_bytes()
        files[name] = {'sha256':hashlib.sha256(data).hexdigest()}
        if production_path(name): files[name]['data'] = base64.b64encode(data).decode()
    return base, {'files':files}

def test_patch_applies_only_source_and_preserves_immutable_base(snapshot, tmp_path):
    base, report = snapshot
    data = b'value = 2\n'
    report['files']['src/click/a.py'] = {'data':base64.b64encode(data).decode(), 'sha256':hashlib.sha256(data).hexdigest()}
    patch = capture_patch(base, report, tmp_path/'captured')
    assert b'+++ b/src/click/a.py' in patch
    assert (base/'src/click/a.py').read_bytes() == b'value = 1\n'
    assert (tmp_path/'captured/tests/test_a.py').read_bytes() == b'assert True\n'

@pytest.mark.parametrize('name', ['tests/test_a.py', 'TASK.md'])
def test_immutable_file_deletion_rejected(snapshot, tmp_path, name):
    base, report = snapshot
    del report['files'][name]
    with pytest.raises(InvalidSubmission): capture_patch(base, report, tmp_path/'captured')

def test_source_hash_mismatch_rejected(snapshot, tmp_path):
    base, report = snapshot
    report['files']['src/click/a.py']['sha256'] = 'incorrect'
    with pytest.raises(InvalidSubmission): capture_patch(base, report, tmp_path/'captured')

@pytest.mark.parametrize('name', ['src/click/../../evil.py', 'src/click/C:/evil.py', 'src/click/.git/evil.py'])
def test_unsafe_source_paths_rejected(snapshot, tmp_path, name):
    base, report = snapshot
    report['files'][name] = report['files']['src/click/a.py']
    with pytest.raises(InvalidSubmission): capture_patch(base, report, tmp_path/'captured')

def test_worker_read_write_cannot_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(task_worker, 'ROOT', tmp_path)
    with pytest.raises(ValueError): task_worker.dispatch({'operation':'read','path':'../secret'})
    with pytest.raises(ValueError): task_worker.dispatch({'operation':'write','path':'../secret','content':'x'})
    task_worker.dispatch({'operation':'write','path':'src/a.py','content':'test'})
    assert task_worker.dispatch({'operation':'read','path':'src/a.py'}) == {'content':'test'}
