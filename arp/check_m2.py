"""Read-only evidence audit of the completed M2 Linux development batch."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .adapters import CLI_VERSION
from .linux_runtime import validate_agent
from .m2 import ROOT, PLAN, EVALUATOR
from .check_m1 import file_hashes
from .validation import parse_junit

def load(path): return json.loads(path.read_text(encoding='utf-8'))

def audit(output: Path):
    if not output.resolve().is_relative_to((ROOT/'artifacts/private').resolve()):
        raise ValueError('Audit only the private evidence store')
    config = load(output/'config.json')
    summary = load(output/'summary.json')
    gate = load(output/'probes/gate.json')
    if summary['status'] != 'M2_complete_pending_user_review':
        raise ValueError('Batch did not complete M2')
    if not gate['passed'] or not config.get('native_tool_probe_passed'):
        raise ValueError('Live network and Linux tools gate missing')
    if config['paid_api_cap'] != 0 or config['cli_version'] != CLI_VERSION or config['evaluator_image_id'] != EVALUATOR:
        raise ValueError('Frozen runtime or budget differs')
    records = summary['attempts']
    if [(r['task_id'],r['repeat']) for r in records] != list(PLAN):
        raise ValueError('Development plan differs')
    public = []
    for record in records:
        attempt = output/record['run_id']
        if record['split'] != 'development' or record['state'] not in {'resolved','test_failure','invalid_submission'}:
            raise ValueError('Unexpected task state')
        agent = load(attempt/'inspect.json')
        command = load(attempt/'container_command.json')
        auth_arg = next(a for a in command if 'target=/auth/auth.json' in a)
        auth = Path(auth_arg.split('source=',1)[1].split(',target=',1)[0])
        validate_agent(agent,attempt/'task_input',auth,agent['HostConfig']['NetworkMode'])
        tasks = load(ROOT/'artifacts/private/m1-v7/tasks.json')
        task = next(t for t in tasks if t['task_id'] == record['task_id'])
        frozen_hashes = file_hashes(ROOT/task['agent_workspace'])
        if file_hashes(attempt/'task_input') != frozen_hashes or (attempt/'task_input/.git').exists():
            raise ValueError('Task input changed or contains history')
        cli = load(attempt/'cli_command.json')
        for required in ('web_search="disabled"','forced_login_method="chatgpt"','model_provider="openai"',
                         'model='+json.dumps(config['model']),
                         'model_reasoning_effort='+json.dumps(config['reasoning_effort']),
                         'features.code_mode_host=true','mcp_servers={}'):
            if required not in cli: raise ValueError('Missing frozen CLI setting: '+required)
        raw = (attempt/'events.jsonl').read_bytes()
        adapter = record['adapter']
        if hashlib.sha256(raw).hexdigest() != adapter['events_sha256']:
            raise ValueError('Agent event hash differs')
        if adapter['model'] != config['model'] or adapter['inference_settings']['reasoning_effort'] != config['reasoning_effort']:
            raise ValueError('Recorded model pin differs')
        events = [json.loads(line) for line in raw.splitlines()]
        if any(e.get('item',{}).get('type') == 'web_search' for e in events):
            raise ValueError('Web search event observed')
        native = sum(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution' for e in events)
        row = {'task_id':record['task_id'],'repeat':record['repeat'],'state':record['state'],
               'agent_seconds':adapter['seconds'],'usage':adapter['usage'],'native_command_calls':native,
               'evidence':attempt.relative_to(ROOT).as_posix()}
        if record['state'] != 'invalid_submission':
            patch = (attempt/'submission.patch').read_bytes()
            if hashlib.sha256(patch).hexdigest() != record['patch_sha256']:
                raise ValueError('Submission hash differs')
            evaluation = record['evaluation']
            parsed = parse_junit(attempt/'evaluation/junit.xml','agent',record['repeat'],
                evaluation['returncode'],evaluation['seconds'],evaluation['timed_out'])
            if json.loads(json.dumps(parsed.record())) != evaluation:
                raise ValueError('Evaluator record differs from JUnit')
            cmd = load(attempt/'evaluation/command.json')
            if cmd[cmd.index('--network')+1] != 'none' or cmd[cmd.index('--user')+1] != '1000:1000':
                raise ValueError('Evaluator isolation differs')
            if EVALUATOR not in cmd or '--read-only' not in cmd or cmd[cmd.index('--cap-drop')+1]!='ALL':
                raise ValueError('Evaluator runtime differs')
            candidate = (ROOT/task['evidence']).parent
            expected = file_hashes(candidate/'buggy')
            observed = file_hashes(attempt/'evaluation_workspace')
            for name,digest in expected.items():
                if not name.startswith('src/click/') and observed.get(name) != digest:
                    raise ValueError('Immutable evaluator file differs')
            row.update({'passed':parsed.passed,'skipped':parsed.skipped,'failed':len(parsed.failures),
                        'errors':len(parsed.errors),'evaluator_seconds':parsed.seconds,
                        'patch_sha256':record['patch_sha256'],'patch_bytes':record['patch_bytes']})
        public.append(row)
    return {'milestone':'M2','status':'complete_pending_user_review','dataset_version':'m1-v7',
        'm1_commit':'f000b0b','model':config['model'],'reasoning_effort':config['reasoning_effort'],
        'cli_version':CLI_VERSION,'agent_image_id':config['agent_image_id'],
        'proxy_image_id':config['proxy_image_id'],'evaluator_image_id':EVALUATOR,
        'completed_smoke_attempts':5,'resolved':sum(r['state']=='resolved' for r in records),
        'all_probes_passed':True,'native_tool_probe_passed':True,
        'probes':load(output/'probes/network.json'),'attempts':public,
        'incremental_paid_api_spend':0,'dollar_cost':'not measured',
        'credentials_visible_in_ephemeral_agent':True,'docker_timeouts':summary['docker_timeouts'],
        'endpoint_probe_usage':config['endpoint_probe_usage'],'confirmation_attempts':0,
        'later_milestones_started':False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    result = audit(args.output.resolve())
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
