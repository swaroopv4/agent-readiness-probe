"""Run the user-approved M5 remaining slots, reusing all eight M3 baselines."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

from .m3 import ROOT, validate_freeze, digest
from .m2 import run_batch, ledger
from .adapters import AdapterConfig, CodexCLIAdapter, utc_now
from .linux_runtime import Docker, DockerStop, ProxyNetwork, AgentContainer
from .experiment import stage_task, common_prompt, validate_overlay
from .submissions import capture_patch, InvalidSubmission
from .miner import apply_patch
from .validation import execute
from .attempt_metrics import metrics
from .rules import label
from .m5_analysis import analyze

PLAN_PATH = ROOT/'results/m5_plan.json'
OUTPUT = ROOT/'artifacts/private/m5-run-001'
TERMINAL = {'resolved','test_failure','invalid_submission','cancelled'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
    temporary.replace(path)


def make_order(tasks, seed):
    rng = random.Random(seed)
    blocks = sorted(tasks,key=lambda t:t['task_id'])
    rng.shuffle(blocks)
    order = []
    for task in blocks:
        items = [{'task_id':task['task_id'],'arm':arm,'repeat':repeat,'split':task['split']}
                 for arm in ['baseline','intervention'] for repeat in [1,2]
                 if not (task['split']=='confirmation' and arm=='baseline' and repeat==1)]
        rng.shuffle(items)
        order.extend(items)
    return order


def prepare_plan():
    if PLAN_PATH.exists() or OUTPUT.exists():
        raise ValueError('M5 plan/evidence already exists; never replace a plan or attempt')
    freeze=validate_freeze()
    tasks=load(ROOT/'artifacts/private/m1-v7/tasks.json')
    if len(tasks)!=12 or any(t['human_acceptance']!='accepted' for t in tasks):
        raise ValueError('Twelve accepted tasks required')
    reused=[]
    for r in load(ROOT/'artifacts/private/m3-confirmation-001/summary.json')['attempts']:
        path=ROOT/'artifacts/private/m3-confirmation-001'/r['run_id']
        if r['state'] not in TERMINAL or (r['arm'],r['repeat'],r['split'])!=('baseline',1,'confirmation'):
            raise ValueError('M3 retained slot differs')
        reused.append({'task_id':r['task_id'],'arm':'baseline','repeat':1,'split':'confirmation',
                       'path':path.relative_to(ROOT).as_posix(),'result_sha256':digest(path/'result.json'),
                       'events_sha256':digest(path/'events.jsonl'),'patch_sha256':digest(path/'submission.patch')})
    if len(reused)!=8: raise ValueError('Eight retained baselines required')
    seed=20261002
    plan={'status':'user_authorized_M5_before_M4','created':utc_now(),'seed':seed,
          'randomization':'Python Random(seed): shuffle sorted task blocks, then shuffle remaining arm/repeat slots inside each block.',
          'order_amendment':'Latest user instruction supersedes the global 24-slot confirmation-only M3 future-order list; original M3 freeze remains intact. Twelve-task scope adds sixteen development slots, preserving the identical treatment and confirmation reuse.',
          'model':freeze['model'],'reasoning_effort':freeze['reasoning_effort'],'cli_version':freeze['cli_version'],
          **{k:freeze[k] for k in ['agent_image_id','proxy_image_id','evaluator_image_id','intervention_path','intervention_sha256','common_prompt_path','common_prompt_sha256','rubric_sha256','manifest_sha256']},
          'm3_freeze_sha256':digest(ROOT/'results/m3_freeze.json'),'remaining_order':make_order(tasks,seed),
          'reused_baselines':reused,'new_scored_slots':40,'total_scored_slots':48,
          'historical_development_excluded':'M2 uses another model; Luna development calibration uses the earlier prompt and repeat 0. Neither is pooled into the new 48 slots.',
          'limits':{'agent_wall_seconds':900,'evaluator_seconds':300,'paid_api_cap':0,'stop_on_usage_limit':True,'stop_on_two_docker_timeouts':True,'no_automatic_retry_or_fallback':True},
          'accounting':{'prior_cli_invocations':28,'new_scored_invocations_planned':40,'native_gate_invocations_planned':1,'projected_total':69,'ceiling_revision':'User explicitly authorized all remaining 12-task scored slots; replaces the earlier approximate 50 planning ceiling, retaining the $0 cap.'},
          'analysis':{'primary':'mean intervention-minus-baseline task success difference on eight confirmation tasks, two attempts each arm',
                      'bootstrap_resamples':10000,'bootstrap_seed':seed,'interval':'paired task-cluster percentile 95%; Hoeffding fallback if degenerate, also report Hoeffding always',
                      'key_secondary':'paired task mean agent-wall-seconds difference, including failed task attempts; paired cluster bootstrap 95%',
                      'all_tasks':'descriptive only','infrastructure':'missing outcome/exclusion; never silently score as failure or replace; no comparable final estimate if incomplete',
                      'zero_in_interval':'inconclusive'},
          'arm_order_limitation':freeze['arm_order_limitation'],
          'stop_checkpoint':'M5 analysis committed; do not start M4',
          'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in ['arp/m5.py','arp/m5_analysis.py']}}
    assert len(plan['remaining_order'])==40
    save(PLAN_PATH,plan)
    return plan


def validate_plan():
    freeze=validate_freeze(); plan=load(PLAN_PATH)
    stored=subprocess.run(['git','show','HEAD:results/m5_plan.json'],cwd=ROOT,capture_output=True,check=True).stdout
    if json.loads(stored)!=plan: raise ValueError('M5 plan must be committed before launch')
    if digest(ROOT/'results/m3_freeze.json')!=plan['m3_freeze_sha256']: raise ValueError('Original freeze differs')
    for k in ['model','reasoning_effort','intervention_sha256','common_prompt_sha256','rubric_sha256','agent_image_id','proxy_image_id','evaluator_image_id']:
        if plan[k]!=freeze[k]: raise ValueError('M5 configuration differs: '+k)
    for name,expected in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=expected: raise ValueError('M5 analysis/runner changed after freeze')
    tasks=load(ROOT/'artifacts/private/m1-v7/tasks.json')
    if plan['remaining_order']!=make_order(tasks,plan['seed']): raise ValueError('Randomized order differs')
    for item in plan['reused_baselines']:
        for name,key in [('result.json','result_sha256'),('events.jsonl','events_sha256'),('submission.patch','patch_sha256')]:
            if digest(ROOT/item['path']/name)!=item[key]: raise ValueError('Retained M3 evidence differs')
    return freeze,plan,tasks


def sanitized(path,source):
    r=load(path/'result.json')
    success=r['state']=='resolved' if r['state'] in TERMINAL else None
    out={'run_id':r['run_id'],'task_id':r['task_id'],'split':r['split'],'arm':r['arm'],'repeat':r['repeat'],
         'state':r['state'],'success':success,'source':source,'started':r.get('started'),'agent_wall_seconds':r.get('adapter',{}).get('seconds')}
    if 'adapter' in r:
        out.update(metrics(path))
        out.update(success=success,source=source,arm=r['arm'],repeat=r['repeat'])
        if success is not None:
            prediction=label(path)
            out.update(rule_primary=prediction['rule_primary'],rule_secondary=prediction['rule_secondary'])
    return out


def publish(plan,progress,status):
    records=[sanitized(ROOT/r['path'],'M3 retained baseline repeat 1') for r in plan['reused_baselines']]
    records.extend(sanitized(OUTPUT/r['run_id'],'M5 new attempt') for r in progress['attempts'] if (OUTPUT/r['run_id']/'result.json').exists())
    analysis=analyze(records,load(ROOT/'artifacts/private/m1-v7/tasks.json'),plan['analysis']['bootstrap_seed'])
    summary={'milestone':'M5','status':status,'config':{k:plan[k] for k in ['seed','model','reasoning_effort','intervention_sha256','common_prompt_sha256','rubric_sha256','arm_order_limitation']},
             'plan_sha256':digest(PLAN_PATH),'retained_M3_baselines':8,'new_launched':len(progress['attempts']),
             'new_scored_completed':sum(r['state'] in TERMINAL for r in progress['attempts']),
             'unlaunched_attempts_remaining':40-len(progress['attempts']),
             'scored_outcomes_still_missing':48-sum(r['success'] is not None for r in records),
             'attempts':records,'analysis':analysis,'docker_timeouts':progress['docker_timeouts'],
             'accounting':{**plan['accounting'],'new_cli_invocations_observed':progress['cli_invocations'],
                           'total_cli_invocations_observed':28+progress['cli_invocations'],'incremental_paid_api_spend':0,'dollar_cost':'not measured'},
             'M4_started':False,'human_labels_changed':False,'stop_reason':progress.get('stop_reason')}
    save(ROOT/'results/m5_summary.json',summary)
    return summary


def run():
    freeze,plan,tasks=validate_plan()
    if OUTPUT.exists(): raise ValueError('M5 evidence exists; do not rerun started/completed slots')
    auth=Path.home()/'.codex/auth.json'
    auth_data=load(auth)
    if auth_data.get('auth_mode')!='chatgpt' or auth_data.get('OPENAI_API_KEY') or not auth_data.get('tokens'): raise ValueError('Saved ChatGPT auth required; no API keys')
    del auth_data
    if shutil.disk_usage(ROOT).free < 10*1024**3: raise ValueError('Less than 10 GiB free')
    OUTPUT.mkdir()
    save(OUTPUT/'config.json',plan)
    progress={'status':'started','attempts':[],'docker_timeouts':0,'cli_invocations':0,'started':utc_now()}
    docker=Docker(OUTPUT)
    by_id={r['task_id']:r for r in tasks}
    def checkpoint(status):
        progress['status']=status; progress['docker_timeouts']=docker.timeouts
        save(OUTPUT/'progress.json',progress)
        return publish(plan,progress,status)
    checkpoint('started')
    current=None
    try:
        # The unchanged M2 probes-only path runs an empty native gate, no task.
        checkpoint('gate_running')
        run_batch(ROOT/'artifacts/private/m1-v7',OUTPUT/'gate',auth,freeze['agent_image_id'],freeze['proxy_image_id'],
                  probes_only=True,ceiling_config=AdapterConfig(freeze['model'],freeze['reasoning_effort']))
        progress['cli_invocations']=1
        gate=load(OUTPUT/'gate/config.json')
        for key in ['agent_image_id','proxy_image_id','evaluator_image_id','model','reasoning_effort','cli_version']:
            if gate[key]!=freeze[key]: raise ValueError('Gate differs from frozen '+key)
        if not gate['all_probes_passed'] or not gate['native_tool_probe_passed']: raise ValueError('Gate not passed')
        save(OUTPUT/'gate_passed.json',{'passed':True,'finished':utc_now()})
        print(json.dumps({'gate':'passed','new_scored_slots':40}),flush=True)
        with ProxyNetwork(docker,freeze['proxy_image_id']) as network:
            for number,slot in enumerate(plan['remaining_order'],1):
                if docker.timeouts>=2: raise DockerStop('Two Docker timeouts; stop')
                task=by_id[slot['task_id']]
                if task['image_id']!=freeze['evaluator_image_id']: raise ValueError('Evaluator image differs')
                attempt=OUTPUT/f"{number:02d}-{slot['task_id']}-{slot['arm']}-{slot['repeat']}"
                attempt.mkdir()
                current={'kind':'M5_scored_slot','run_id':attempt.name,**slot,'started':utc_now(),'state':'started'}
                progress['attempts'].append(current)
                save(attempt/'result.json',current); ledger(OUTPUT,current); checkpoint('running')
                base=ROOT/task['agent_workspace']; clean=attempt/'task_input'
                stage_task(base,clean,slot['arm'],freeze)
                result=None
                with AgentContainer(docker,freeze['agent_image_id'],network,clean,auth,attempt) as container:
                    adapter=CodexCLIAdapter(AdapterConfig(freeze['model'],freeze['reasoning_effort']))
                    adapter.prepare(container,common_prompt((clean/'TASK.md').read_text(encoding='utf-8'),freeze),attempt)
                    progress['cli_invocations']+=1
                    checkpoint('running')
                    result=adapter.run()
                    current.update(state=result.status,adapter=asdict(result))
                    save(attempt/'result.json',current)
                    if result.status=='completed':
                        report=json.loads(container.exec(['python','-I','-c',(ROOT/'arp/task_worker.py').read_text(encoding='utf-8')],input=b'{"operation":"collect"}',timeout=30).stdout)
                        save(attempt/'collection_hashes.json',{k:{'sha256':v['sha256']} for k,v in report['files'].items()})
                        try:
                            validate_overlay(report,slot['arm'],freeze)
                            patch=capture_patch(base,report,attempt/'captured_source')
                            (attempt/'submission.patch').write_bytes(patch)
                            current.update(patch_sha256=hashlib.sha256(patch).hexdigest(),patch_bytes=len(patch))
                        except (InvalidSubmission,ValueError) as error:
                            current.update(state='invalid_submission',submission_error=str(error))
                if current['state']=='completed':
                    evaluation=attempt/'evaluation_workspace'
                    shutil.copytree((ROOT/task['evidence']).parent/'buggy',evaluation)
                    if patch: apply_patch(evaluation,patch)
                    try:
                        verdict=execute(task['image_id'],evaluation,attempt/'evaluation','agent',slot['repeat'])
                    except subprocess.TimeoutExpired as error:
                        docker.timeouts+=2
                        raise DockerStop('Evaluator and cleanup timed out; stop') from error
                    current['evaluation']=verdict.record()
                    if verdict.timed_out:
                        docker.timeouts+=1; current['state']='evaluator_infrastructure_error'
                    else:
                        current['state']='resolved' if verdict.returncode==0 and verdict.collected and not verdict.errors else 'evaluator_infrastructure_error' if not verdict.collected or verdict.errors or verdict.returncode not in (0,1) else 'test_failure'
                save(attempt/'result.json',current); ledger(OUTPUT,current); checkpoint('running')
                print(json.dumps({'attempt':number,'of':40,'task':slot['task_id'],'arm':slot['arm'],'repeat':slot['repeat'],'state':current['state'],'seconds':result.seconds if result else None}),flush=True)
                if result.status=='usage_limit': raise RuntimeError('Codex usage limits interrupted batch; stop')
                if result.status not in {'completed','cancelled'}: raise RuntimeError('CLI infrastructure failed; stop without retry/fallback')
                if current['state']=='evaluator_infrastructure_error': raise RuntimeError('Evaluator infrastructure failed; stop')
                current=None
        checkpoint('M5_complete_pending_review')
    except BaseException as error:
        gate_summary=OUTPUT/'gate/summary.json'
        if gate_summary.exists(): docker.timeouts=max(docker.timeouts,load(gate_summary)['docker_timeouts'])
        if not progress['attempts']:
            gate_ledger=OUTPUT/'gate/ledger.jsonl'
            progress['cli_invocations']=sum(json.loads(line).get('kind')=='endpoint_probe' and json.loads(line).get('state')=='started'
                                            for line in gate_ledger.read_text(encoding='utf-8').splitlines()) if gate_ledger.exists() else 0
        if current and current['state'] in {'started','completed'}:
            current.update(state='infrastructure_abort',infrastructure_error=str(error))
            save(OUTPUT/current['run_id']/'result.json',current); ledger(OUTPUT,current)
        progress['stop_reason']={'type':type(error).__name__,'error':str(error),'at':utc_now()}
        checkpoint('stopped')
        print(json.dumps({'status':'stopped','reason':str(error),'unlaunched_remaining':40-len(progress['attempts'])}),flush=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--analyze-only',action='store_true')
    args=parser.parse_args()
    if args.prepare:
        plan=prepare_plan(); print(json.dumps({'prepared_slots':len(plan['remaining_order']),'seed':plan['seed']}))
    elif args.analyze_only:
        _,plan,_=validate_plan(); progress=load(OUTPUT/'progress.json'); publish(plan,progress,progress['status'])
    else: run()


if __name__=='__main__': main()
