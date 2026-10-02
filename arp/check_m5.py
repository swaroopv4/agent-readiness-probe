"""Audit saved M5 evidence without launching tasks, evaluators, or inference."""
import hashlib
import json
from pathlib import Path

from .m5 import ROOT, OUTPUT, TERMINAL, load, validate_plan
from .check_m1 import file_hashes
from .check_m3 import audit as audit_m3
from .linux_runtime import validate_agent
from .validation import parse_junit


def audit():
    freeze,plan,tasks=validate_plan()
    original=audit_m3(ROOT/'artifacts/private/m3-confirmation-001')
    progress=load(OUTPUT/'progress.json')
    by_id={t['task_id']:t for t in tasks}
    assert load(OUTPUT/'config.json')==plan
    assert load(OUTPUT/'gate_passed.json')['passed']
    assert load(OUTPUT/'gate/probes/gate.json')['passed']
    assert load(OUTPUT/'gate/summary.json')['attempts']==[]
    network=load(OUTPUT/'internal_network.json')
    proxy=load(OUTPUT/'proxy_inspect.json')
    assert network['Internal'] and len(proxy['NetworkSettings']['Networks'])==2
    assert proxy['Image']==freeze['proxy_image_id']
    owned_containers=[proxy['Name'].lstrip('/')]
    owned_networks=list(proxy['NetworkSettings']['Networks'])
    audited=[]
    agents_text=(ROOT/freeze['intervention_path']).read_text(encoding='utf-8').strip()
    intervention_reads=[]
    for number,record in enumerate(progress['attempts'],1):
        slot=plan['remaining_order'][number-1]
        for key in ['task_id','arm','repeat','split']: assert record[key]==slot[key]
        p=OUTPUT/record['run_id']; assert load(p/'result.json')==record
        task=by_id[record['task_id']]
        if not (p/'task_input').exists():
            assert record['state'] not in TERMINAL
            continue
        observed=file_hashes(p/'task_input')
        expected=file_hashes(ROOT/task['agent_workspace'])
        if record['arm']=='intervention': expected['AGENTS.md']=freeze['intervention_sha256']
        assert observed==expected
        assert not (p/'task_input/.git').exists()
        if (p/'inspect.json').exists():
            info=load(p/'inspect.json'); command=load(p/'container_command.json')
            auth_arg=next(a for a in command if 'target=/auth/auth.json' in a)
            auth=Path(auth_arg.split('source=',1)[1].split(',target=',1)[0])
            validate_agent(info,p/'task_input',auth,info['HostConfig']['NetworkMode'])
            assert info['Image']==freeze['agent_image_id']
            owned_containers.append(info['Name'].lstrip('/'))
        if (p/'cli_command.json').exists():
            cli=load(p/'cli_command.json')
            for value in ['model="gpt-5.6-luna"','model_reasoning_effort="low"','web_search="disabled"','forced_login_method="chatgpt"','features.code_mode_host=true']:
                assert value in cli
            assert (p/'prompt.txt').read_text(encoding='utf-8')==(ROOT/freeze['common_prompt_path']).read_text(encoding='utf-8')+(p/'task_input/TASK.md').read_text(encoding='utf-8')
        if 'adapter' in record:
            raw=(p/'events.jsonl').read_bytes()
            assert hashlib.sha256(raw).hexdigest()==record['adapter']['events_sha256']
            events=[json.loads(l) for l in raw.splitlines()]
            assert not any(e.get('item',{}).get('type')=='web_search' for e in events)
            if record['arm']=='intervention':
                read_seen=any(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution'
                              and e['item'].get('exit_code')==0 and agents_text in e['item'].get('aggregated_output','').replace('\r\n','\n') for e in events)
                intervention_reads.append({'run_id':record['run_id'],'visible_full_AGENTS_read':read_seen})
            if record['adapter']['status']=='completed':
                assert record['adapter']['model']==freeze['model']
                assert record['adapter']['inference_settings']['reasoning_effort']==freeze['reasoning_effort']
        if (p/'collection_hashes.json').exists() and record['state'] in {'resolved','test_failure'}:
            collection=load(p/'collection_hashes.json')
            if record['arm']=='intervention': assert collection['AGENTS.md']['sha256']==freeze['intervention_sha256']
        if record['state'] in {'resolved','test_failure'}:
            assert hashlib.sha256((p/'submission.patch').read_bytes()).hexdigest()==record['patch_sha256']
            ev=record['evaluation']
            parsed=parse_junit(p/'evaluation/junit.xml','agent',record['repeat'],ev['returncode'],ev['seconds'],ev['timed_out'])
            assert json.loads(json.dumps(parsed.record()))==ev
            assert (parsed.returncode==0)==(record['state']=='resolved')
            assert parsed.collected and not parsed.errors and not parsed.timed_out
            ec=load(p/'evaluation/command.json')
            assert ec[ec.index('--network')+1]=='none' and freeze['evaluator_image_id'] in ec
            owned_containers.append(ec[ec.index('--name')+1])
            before=file_hashes((ROOT/task['evidence']).parent/'buggy')
            after=file_hashes(p/'evaluation_workspace')
            for name,digest in before.items():
                if not name.startswith('src/click/'): assert after.get(name)==digest
            assert 'AGENTS.md' not in after
        audited.append({'run_id':record['run_id'],'state':record['state'],'arm':record['arm'],'repeat':record['repeat']})
    # The unchanged gate was separately cleaned up by the frozen M2 runtime.
    for path in (OUTPUT/'gate').rglob('inspect.json'):
        info=load(path); owned_containers.append(info['Name'].lstrip('/'))
    if (OUTPUT/'gate/proxy_inspect.json').exists():
        info=load(OUTPUT/'gate/proxy_inspect.json')
        owned_containers.append(info['Name'].lstrip('/')); owned_networks.extend(info['NetworkSettings']['Networks'])
    return {'status':'saved_evidence_audit_passed','retained_M3_baselines':len(original['attempts']),
            'new_attempts_audited':len(audited),'attempts':audited,'docker_timeouts':progress['docker_timeouts'],
            'owned_container_names':sorted(set(owned_containers)),'owned_network_names':sorted(set(owned_networks)),
            'frozen_artifacts_unchanged':True,'same_offline_evaluator':True,'new_agent_calls':0,
            'intervention_read_evidence':intervention_reads}


if __name__=='__main__':
    result=audit()
    print(json.dumps({k:v for k,v in result.items() if k not in ['attempts','owned_container_names','owned_network_names']}))
