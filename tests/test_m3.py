import hashlib
import json
from pathlib import Path
import pytest
from arp import experiment, m2
from arp.rules import label


def fixture_attempt(root, state, command, output, code=0):
    root.mkdir()
    (root/'events.jsonl').write_text(json.dumps({'type':'item.completed','item':{'id':'item_1','type':'command_execution','command':command,'aggregated_output':output,'exit_code':code}})+'\n')
    (root/'result.json').write_text(json.dumps({'task_id':'fixture','split':'development','arm':'baseline','repeat':0,'state':state,
        'adapter':{'model':'fixture','seconds':1,'inference_settings':{'reasoning_effort':'low'},'usage':'not measured'},
        'evaluation':{'passed':1 if state=='resolved' else 0,'failures':[] if state=='resolved' else ['private-name'],'errors':[]}}))
    return root


def test_rules_do_not_label_displayed_source_as_traceback(tmp_path):
    p=fixture_attempt(tmp_path/'display','resolved','cat tests/test_a.py','raise AssertionError\nraise ImportError: example')
    r=label(p)
    assert r['rule_primary']=='no_failure' and not r['rule_secondary']


def test_intermediate_setup_is_secondary_for_evaluator_pass(tmp_path):
    p=fixture_attempt(tmp_path/'setup','resolved','python -m pytest -q','ERROR collecting tests/test_a.py\n1 error during collection',2)
    r=label(p)
    assert r['rule_primary']=='no_failure' and r['rule_secondary']==['env_setup']


def test_masked_python_assertion_is_observable_behavior_not_gold(tmp_path):
    p=fixture_attempt(tmp_path/'behavior','test_failure',"python - <<'PY'; tail other.txt",'Traceback (most recent call last):\nAssertionError\n',0)
    r=label(p)
    assert r['rule_primary']=='reasoning_error'
    assert 'private-name' not in json.dumps(r['evidence'])


def test_unseen_oracle_failure_alone_abstains(tmp_path):
    p=fixture_attempt(tmp_path/'unclassified','test_failure','echo done','done')
    assert label(p)['rule_primary']=='unclassified'


def test_identical_prompt_and_overlay_enforced(tmp_path,monkeypatch):
    monkeypatch.setattr(experiment,'ROOT',tmp_path)
    base=tmp_path/'base'; base.mkdir(); (base/'TASK.md').write_text('Task')
    (base/'src/click').mkdir(parents=True); (base/'src/click/a.py').write_text('a=1')
    (tmp_path/'AGENTS.txt').write_bytes(b'Generic setup\n')
    (tmp_path/'prompt.txt').write_bytes(b'Read AGENTS if present.\n\n')
    freeze={'intervention_path':'AGENTS.txt','intervention_sha256':hashlib.sha256(b'Generic setup\n').hexdigest(),
            'common_prompt_path':'prompt.txt','common_prompt_sha256':hashlib.sha256(b'Read AGENTS if present.\n\n').hexdigest()}
    experiment.stage_task(base,tmp_path/'baseline','baseline',freeze)
    experiment.stage_task(base,tmp_path/'intervention','intervention',freeze)
    assert not (tmp_path/'baseline/AGENTS.md').exists()
    assert (tmp_path/'intervention/AGENTS.md').read_bytes()==b'Generic setup\n'
    assert experiment.common_prompt('Task',freeze)=='Read AGENTS if present.\n\nTask'
    from arp.submissions import InvalidSubmission
    with pytest.raises(InvalidSubmission): experiment.validate_overlay({'files':{}},'intervention',freeze)


def test_m3_cannot_add_repeat_or_wrong_split_before_docker(tmp_path,monkeypatch):
    root=tmp_path/'root'; dataset=root/'artifacts/private/m1-v7'; dataset.mkdir(parents=True)
    tasks=[{'task_id':str(i),'split':'confirmation','human_acceptance':'accepted'} for i in range(8)]
    (dataset/'tasks.json').write_text(json.dumps(tasks)); (root/'prompt.txt').write_text('Shared')
    monkeypatch.setattr(m2,'ROOT',root)
    monkeypatch.setattr(m2,'Docker',lambda *a:pytest.fail('Docker must not launch'))
    freeze={'common_prompt_path':'prompt.txt','m3_plan':[{'task_id':str(i),'repeat':2} for i in range(8)]}
    with pytest.raises(ValueError,match='repeat 1'):
        m2.run_batch(dataset,root/'artifacts/private/output',tmp_path/'auth','agent','proxy',confirmation_freeze=freeze)


def test_m3_existing_baseline_prevents_rerun_before_auth_or_docker(tmp_path,monkeypatch):
    root=tmp_path/'root'; dataset=root/'artifacts/private/m1-v7'; dataset.mkdir(parents=True)
    tasks=[{'task_id':str(i),'split':'confirmation','human_acceptance':'accepted'} for i in range(8)]
    (dataset/'tasks.json').write_text(json.dumps(tasks)); (root/'prompt.txt').write_text('Shared')
    evidence=root/'artifacts/private/m3-confirmation-001/01-fixture-baseline-1'
    evidence.mkdir(parents=True); (evidence/'result.json').write_text('{}')
    monkeypatch.setattr(m2,'ROOT',root)
    monkeypatch.setattr(m2,'Docker',lambda *a:pytest.fail('Never rerun existing baseline'))
    freeze={'common_prompt_path':'prompt.txt','m3_plan':[{'task_id':str(i),'repeat':1} for i in range(8)]}
    with pytest.raises(ValueError,match='do not rerun'):
        m2.run_batch(dataset,root/'artifacts/private/new-output',tmp_path/'absent-auth','agent','proxy',confirmation_freeze=freeze)
