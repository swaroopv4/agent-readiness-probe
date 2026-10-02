"""Read-only audit of the eight non-repeated M3 confirmation baseline inputs and outcomes."""
import hashlib
import json
from pathlib import Path
from .m3 import ROOT, validate_freeze
from .check_m1 import file_hashes
from .linux_runtime import validate_agent
from .validation import parse_junit
from .attempt_metrics import metrics


def load(path): return json.loads(path.read_text(encoding='utf-8'))


def audit(output):
    freeze=validate_freeze(); config=load(output/'config.json'); summary=load(output/'summary.json')
    assert summary['status']=='M3_baselines_complete_pending_human_labels'
    assert config['purpose']=='M3_confirmation_baseline_repeat_1'
    assert config['intervention_sha256']==freeze['intervention_sha256']
    assert config['rubric_sha256']==freeze['rubric_sha256']
    assert config['common_prompt_sha256']==freeze['common_prompt_sha256']
    for key in ['agent_image_id','proxy_image_id','evaluator_image_id']:
        assert config[key]==freeze[key]
    assert (config['model'],config['reasoning_effort'])==('gpt-5.6-luna','low')
    assert load(output/'probes/gate.json')['passed'] and config['native_tool_probe_passed']
    records=summary['attempts']; assert len(records)==8
    assert [(r['task_id'],r['arm'],r['repeat']) for r in records]==[(r['task_id'],'baseline',1) for r in freeze['m3_plan']]
    tasks={t['task_id']:t for t in load(ROOT/'artifacts/private/m1-v7/tasks.json')}
    public=[]
    for r in records:
        p=output/r['run_id']; task=tasks[r['task_id']]
        assert r['split']=='confirmation' and task['split']=='confirmation'
        assert r['state'] in {'resolved','test_failure','invalid_submission','cancelled'}
        assert not (p/'task_input/AGENTS.md').exists() and not (p/'task_input/.git').exists()
        assert file_hashes(p/'task_input')==file_hashes(ROOT/task['agent_workspace'])
        info=load(p/'inspect.json'); container=load(p/'container_command.json')
        auth_arg=next(a for a in container if 'target=/auth/auth.json' in a)
        auth=Path(auth_arg.split('source=',1)[1].split(',target=',1)[0])
        validate_agent(info,p/'task_input',auth,info['HostConfig']['NetworkMode'])
        assert (p/'prompt.txt').read_text(encoding='utf-8')==(ROOT/freeze['common_prompt_path']).read_text(encoding='utf-8')+(p/'task_input/TASK.md').read_text(encoding='utf-8')
        cli=load(p/'cli_command.json')
        for required in ['model="gpt-5.6-luna"','model_reasoning_effort="low"','web_search="disabled"','forced_login_method="chatgpt"','features.code_mode_host=true']:
            assert required in cli
        assert hashlib.sha256((p/'events.jsonl').read_bytes()).hexdigest()==r['adapter']['events_sha256']
        events=[json.loads(l) for l in (p/'events.jsonl').read_bytes().splitlines()]
        assert not any(e.get('item',{}).get('type')=='web_search' for e in events)
        if r['state']!='cancelled':
            assert r['adapter']['model']=='gpt-5.6-luna' and r['adapter']['inference_settings']['reasoning_effort']=='low'
        if r['state'] in {'resolved','test_failure'}:
            assert hashlib.sha256((p/'submission.patch').read_bytes()).hexdigest()==r['patch_sha256']
            ev=r['evaluation']
            parsed=parse_junit(p/'evaluation/junit.xml','agent',1,ev['returncode'],ev['seconds'],ev['timed_out'])
            assert json.loads(json.dumps(parsed.record()))==ev
            assert not parsed.errors and not parsed.timed_out and parsed.collected>0
            assert (r['state']=='resolved')==(parsed.returncode==0)
            ec=load(p/'evaluation/command.json')
            assert ec[ec.index('--network')+1]=='none' and freeze['evaluator_image_id'] in ec
            candidate=(ROOT/task['evidence']).parent/'buggy'
            original=file_hashes(candidate); observed=file_hashes(p/'evaluation_workspace')
            for name,value in original.items():
                if not name.startswith('src/click/'): assert observed.get(name)==value
        public.append(metrics(p))
    return {'status':'baselines_complete_label_sheet_pending_or_ready','attempts':public,'baseline_repeat':1,
            'no_baseline_retries':True,'no_intervention_overlays_in_baseline':True,
            'intervention_sha256':freeze['intervention_sha256'],'rubric_sha256':freeze['rubric_sha256'],
            'common_prompt_sha256':freeze['common_prompt_sha256'],'docker_timeouts':summary['docker_timeouts'],
            'incremental_paid_api_spend':0,'dollar_cost':'not measured','human_labels_supplied':0}


def main():
    output=ROOT/'artifacts/private/m3-confirmation-001'
    result=audit(output)
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'audited_attempts':8,'successes':sum(r['state']=='resolved' for r in result['attempts'])}))


if __name__=='__main__': main()
