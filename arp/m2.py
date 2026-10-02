"""M2 Linux-only probe gate and five development attempts. Stops for review."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from .adapters import AdapterConfig, CodexCLIAdapter, CLI_VERSION, Limits, utc_now
from .linux_runtime import Docker, DockerStop, ProxyNetwork, AgentContainer, snapshot
from .miner import apply_patch
from .submissions import capture_patch, InvalidSubmission
from .validation import execute

ROOT = Path(__file__).resolve().parents[1]
PLAN = (('click-002',0),('click-003',0),('click-009',0),('click-010',0),('click-002',1))
CEILING_PLAN = tuple((task,0) for task in ('click-002','click-003','click-009','click-010'))
EVALUATOR = 'sha256:506974e3505483d01d749cfc2cffc6bae2e3d375f2f5ff69d241bc353b630cb7'

PROBES = r"""
import json, os, socket, time, urllib.request, urllib.error
from pathlib import Path
proxy = os.environ['HTTPS_PROXY']
host = proxy.split('//')[1].split(':')[0]
for i in range(20):
    try:
        with socket.create_connection((host,3128),timeout=1): pass
        break
    except OSError: time.sleep(.25)
else: raise AssertionError('proxy not ready')
handler = urllib.request.build_opener(urllib.request.ProxyHandler({'https':proxy}))
results = {}
for url in ('https://github.com','https://pypi.org','https://1.1.1.1'):
    try:
        handler.open(url,timeout=15)
        raise AssertionError('unapproved domain reachable')
    except urllib.error.URLError as e:
        assert '403 Forbidden' in str(e), str(e)
        results[url] = 'proxy CONNECT 403'
for ip in ('1.1.1.1','8.8.8.8'):
    try:
        with socket.create_connection((ip,443),timeout=3): pass
    except OSError as e: results['direct '+ip] = type(e).__name__ + ': ' + str(e)
    else: raise AssertionError('direct IP reachable')
try:
    socket.getaddrinfo('github.com',443)
except socket.gaierror: results['external_dns'] = 'blocked'
else: raise AssertionError('external DNS bypass reachable')
try:
    response = handler.open('https://chatgpt.com/backend-api/codex/models?client_version=0.153.1',timeout=20)
    status = response.status
except urllib.error.HTTPError as e: status = e.code
assert status in (200,401), status
results['codex_endpoint_tls'] = status
assert os.getuid() == 1000
assert Path('/codex/auth.json').is_file()
assert not any(Path(p).exists() for p in ('/var/run/docker.sock','/input/.git','/workspace/.git','/artifacts','/datasets'))
# The original auth bytes are neither parsed nor emitted by this probe.
try:
    with open('/auth/auth.json','ab') as f: pass
except OSError: results['auth_mount'] = 'read-only'
else: raise AssertionError('auth mount writable')
results['identity'] = '1000:1000'
print(json.dumps(results))
"""

def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')

def ledger(output, record):
    with (output/'ledger.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')

def runtime_check(docker, image, evaluator):
    info = docker.inspect(image)
    base = docker.inspect(evaluator)
    layers = base['RootFS']['Layers']
    if info['RootFS']['Layers'][:len(layers)] != layers:
        raise ValueError('Agent image is not based on the frozen evaluator')
    return info['Id']

def run_batch(dataset, output, auth, agent_image, proxy_image, probes_only=False, *, ceiling_config=None, confirmation_freeze=None):
    if ceiling_config is not None and confirmation_freeze is not None:
        raise ValueError('Cannot mix development ceiling and confirmation modes')
    confirmation = confirmation_freeze is not None
    plan = tuple((r['task_id'], r['repeat']) for r in confirmation_freeze['m3_plan']) if confirmation else CEILING_PLAN if ceiling_config is not None else PLAN
    pinned_config = AdapterConfig('gpt-5.6-luna', 'low') if confirmation else ceiling_config
    prefix = (ROOT/confirmation_freeze['common_prompt_path']).read_text(encoding='utf-8') if confirmation else None
    if ceiling_config is not None and ceiling_config != AdapterConfig("gpt-5.6-luna", "low"):
        raise ValueError("Ceiling check pins the login catalog smallest standard coding tier at low")
    if output.exists():
        raise ValueError('Use a fresh output directory; no attempt overwrite or retry')
    if dataset.resolve() != (ROOT/'artifacts/private/m1-v7').resolve():
        raise ValueError('M2 uses accepted m1-v7 only')
    if not output.resolve().is_relative_to((ROOT/'artifacts/private').resolve()):
        raise ValueError('M2 evidence must remain in the private artifact store')
    tasks = {t['task_id']:t for t in json.loads((dataset/'tasks.json').read_text(encoding='utf-8'))}
    expected_split = 'confirmation' if confirmation else 'development'
    if any(tasks[t]['split'] != expected_split or tasks[t]['human_acceptance'] != 'accepted' for t,_ in plan):
        raise ValueError('Only accepted '+expected_split+' tasks may run')
    if confirmation:
        expected = sorted(t for t,v in tasks.items() if v['split']=='confirmation')
        if list(plan) != [(t,1) for t in expected] or len(plan)!=8:
            raise ValueError('M3 requires exactly eight unique baseline repeat 1 attempts')
        if any((ROOT/'artifacts/private').glob('m3-confirmation-*/**/result.json')):
            raise ValueError('M3 confirmation evidence already exists; do not rerun baseline repeat 1')
    if shutil.disk_usage(ROOT).free < 10*1024**3: raise RuntimeError('Less than 10 GiB free')
    # Reject API-key authentication before any container/model launch, without logging contents.
    auth_data = json.loads(auth.read_text(encoding='utf-8'))
    if auth_data.get('auth_mode') != 'chatgpt' or auth_data.get('OPENAI_API_KEY') or not auth_data.get('tokens'):
        raise ValueError('Saved ChatGPT authentication required; API keys are prohibited')
    del auth_data
    output.mkdir(parents=True)
    docker = Docker(output)
    records = []
    frozen = {'dataset_version':'m1-v7','m1_commit':'f000b0b','paid_api_cap':0,'plan':plan,
        'purpose':'M3_confirmation_baseline_repeat_1' if confirmation else 'development_ceiling_check' if ceiling_config is not None else 'M2_smokes',
        'intervention_sha256':confirmation_freeze['intervention_sha256'] if confirmation else None,
        'common_prompt_sha256':confirmation_freeze['common_prompt_sha256'] if confirmation else None,
        'rubric_sha256':confirmation_freeze['rubric_sha256'] if confirmation else None,
        'started':utc_now(),'previous_cli_infrastructure_aborts':2,
        'previous_container_setup_aborts':1,'credentials_visible_in_ephemeral_agent':True}
    def summary(status):
        write(output/'summary.json',{'status':status,'config':frozen,'attempts':records,
            'completed_smoke_attempts':sum(r['state'] in {'resolved','test_failure','invalid_submission'} for r in records),
            'resolved':sum(r['state']=='resolved' for r in records),
            'docker_timeouts':docker.timeouts,'incremental_paid_api_spend':0,'dollar_cost':'not measured'})
    try:
        engine = docker.call(['info','--format','{{.ServerVersion}} {{.OSType}}']).stdout.decode().strip()
        if not engine.endswith('linux'): raise RuntimeError('Linux Docker engine required')
        frozen['engine'] = engine
        frozen['agent_image_id'] = runtime_check(docker, agent_image, EVALUATOR)
        frozen['proxy_image_id'] = docker.inspect(proxy_image)['Id']
        frozen['evaluator_image_id'] = EVALUATOR
        with ProxyNetwork(docker, frozen['proxy_image_id']) as network:
            probe = output/'probes'
            probe.mkdir()
            empty = output/'probe_input'
            empty.mkdir()
            (empty/'TASK.md').write_text('Connectivity probe only. No task.\n',encoding='utf-8')
            with AgentContainer(docker,frozen['agent_image_id'],network,empty,auth,probe) as container:
                observed = json.loads(container.exec(['python','-I','-c',PROBES],timeout=90).stdout)
                write(probe/'network.json',observed)
                versions = container.exec(['sh','-c','codex --version; node --version; cat /opt/agent-system-packages.txt']).stdout.decode()
                (probe/'versions.txt').write_text(versions,encoding='utf-8')
                if versions.splitlines()[0] != CLI_VERSION: raise RuntimeError('Wrong CLI version')
                login = container.exec(['codex','login','status'])
                (probe/'auth_status.txt').write_bytes(login.stdout+login.stderr)
                if b'Logged in using ChatGPT' not in login.stdout+login.stderr:
                    raise RuntimeError('Saved subscription authentication unavailable')
                # The clean CLI selects its login-supported default and proves native Linux task tools.
                adapter = CodexCLIAdapter(pinned_config or AdapterConfig())
                adapter.prepare(container,'Use your Linux execution tool to run Python that writes /workspace/ARP_TOOL_PROBE.txt containing exactly ARP_TOOL_OK, then use a shell command to read it back. Reply exactly ARP_ENDPOINT_OK after both commands succeed. This is a tool connectivity probe, not a coding task.',probe,Limits(wall_seconds=120))
                ledger(output,{'kind':'endpoint_probe','state':'started','started':utc_now()})
                result = adapter.run()
                ledger(output,{'kind':'endpoint_probe','state':result.status,'adapter':asdict(result)})
                if result.status == 'usage_limit': raise RuntimeError('Codex usage limits block progress. Stop')
                if result.status != 'completed': raise RuntimeError('Live Codex endpoint probe failed')
                events = [json.loads(line) for line in (probe/'events.jsonl').read_text(encoding='utf-8').splitlines()]
                messages = [e.get('item',{}).get('text','') for e in events if e.get('type')=='item.completed']
                if not any('ARP_ENDPOINT_OK' in message for message in messages):
                    raise RuntimeError('Endpoint probe reply missing')
                content = container.exec(['cat','/workspace/ARP_TOOL_PROBE.txt']).stdout
                if content != b'ARP_TOOL_OK': raise RuntimeError('Native Linux tool write/read probe failed')
                if any(e.get('item',{}).get('type') == 'web_search' for e in events):
                    raise RuntimeError('Web search unexpectedly enabled')
                frozen['native_tool_probe_passed'] = True
                frozen.update({'cli_version':CLI_VERSION,'model':result.model,
                    'reasoning_effort':result.inference_settings['reasoning_effort'],
                    'model_evidence':result.inference_settings['evidence'],
                    'endpoint_probe_usage':result.usage,'all_probes_passed':True})
            write(output/'config.json',frozen)
            write(probe/'gate.json',{'passed':True,'model':frozen['model'],'reasoning_effort':frozen['reasoning_effort'],'finished':utc_now()})
            if probes_only:
                summary('probes_passed_no_smokes_requested')
                return records
            config = AdapterConfig(frozen['model'],frozen['reasoning_effort'])
            for number,(task_id,repeat) in enumerate(plan,1):
                if docker.timeouts >= 2: raise DockerStop('Two Docker timeouts; stop')
                task = tasks[task_id]
                attempt = output/f'{number:02d}-{task_id}-baseline-{repeat}'
                attempt.mkdir()
                base = ROOT/task['agent_workspace']
                clean = attempt/'task_input'
                if confirmation:
                    from .experiment import stage_task
                    stage_task(base,clean,'baseline',confirmation_freeze)
                else:
                    snapshot(base,clean)
                record = {'kind':'confirmation_baseline' if confirmation else 'development_ceiling_attempt' if ceiling_config is not None else 'development_smoke','run_id':attempt.name,'task_id':task_id,
                    'split':expected_split,'arm':'baseline','repeat':repeat,'started':utc_now(),'state':'started'}
                records.append(record)
                ledger(output,record)
                with AgentContainer(docker,frozen['agent_image_id'],network,clean,auth,attempt) as container:
                    adapter = CodexCLIAdapter(config)
                    prompt = ('Complete the maintenance task in /workspace/TASK.md. Dependencies are preinstalled. '
                        'Change only production Python files under src/click. Preserve TASK.md, tests, and configuration. '
                        'Temporary diagnostics are allowed outside tests. Run the public test suite using PYTHONPATH=/workspace/src. '
                        'Use native Linux shell and file tools. Keep each shell command within 120 seconds. '
                        'Do not access credentials or the network. Leave the source changes in /workspace and explain the result.\n\n'
                        +(clean/'TASK.md').read_text(encoding='utf-8'))
                    if confirmation:
                        from .experiment import common_prompt
                        prompt = common_prompt((clean/'TASK.md').read_text(encoding='utf-8'),confirmation_freeze)
                    adapter.prepare(container,prompt,attempt)
                    result = adapter.run()
                    record.update({'state':result.status,'adapter':asdict(result)})
                    if result.status == 'completed':
                        # Host supplies the trusted collector as code, never mounts any private tools/artifacts.
                        report = json.loads(container.exec(['python','-I','-c',(ROOT/'arp/task_worker.py').read_text(encoding='utf-8')],
                            input=b'{"operation":"collect"}',timeout=30).stdout)
                        try:
                            patch = capture_patch(base,report,attempt/'captured_source')
                            (attempt/'submission.patch').write_bytes(patch)
                            record.update({'patch_sha256':hashlib.sha256(patch).hexdigest(),'patch_bytes':len(patch)})
                        except (InvalidSubmission,ValueError) as error:
                            record.update({'state':'invalid_submission','submission_error':str(error)})
                if record['state'] == 'completed':
                    candidate = (ROOT/task['evidence']).parent
                    evaluation = attempt/'evaluation_workspace'
                    shutil.copytree(candidate/'buggy',evaluation)
                    if patch: apply_patch(evaluation,patch)
                    try:
                        verdict = execute(task['image_id'],evaluation,attempt/'evaluation','agent',repeat)
                    except subprocess.TimeoutExpired as error:
                        # Evaluator run timed out and its bounded cleanup timed out too.
                        docker.timeouts += 2
                        raise DockerStop('Evaluator run and cleanup both timed out; stop live work') from error
                    record['evaluation'] = verdict.record()
                    if verdict.timed_out:
                        docker.timeouts += 1
                        record['state'] = 'evaluator_infrastructure_error'
                    else:
                        record['state'] = ('resolved' if verdict.returncode==0 and verdict.collected>0 and not verdict.errors else
                            'evaluator_infrastructure_error' if verdict.collected==0 or verdict.errors or verdict.returncode not in (0,1) else 'test_failure')
                write(attempt/'result.json',record)
                ledger(output,record)
                summary('running')
                print(json.dumps({'attempt':number,'task':task_id,'state':record['state'],'seconds':result.seconds,'usage':result.usage}),flush=True)
                if result.status=='usage_limit': raise RuntimeError('Codex usage limits block progress. Stop')
                if result.status!='completed' and not (confirmation and result.status=='cancelled'): raise RuntimeError('CLI transport failed. Stop without retry or fallback')
                if record['state']=='evaluator_infrastructure_error': raise RuntimeError('Offline evaluator failed. Stop')
        summary('M3_baselines_complete_pending_human_labels' if confirmation else 'development_ceiling_complete_pending_user_decision' if ceiling_config is not None else 'M2_complete_pending_user_review')
        return records
    except BaseException as error:
        if records and records[-1]['state'] == 'started':
            current = records[-1]
            current['state'] = 'infrastructure_abort' if (output/current['run_id']/'events.jsonl').exists() else 'container_setup_abort'
            current['infrastructure_error'] = str(error)
            write(output/current['run_id']/'result.json',current)
            ledger(output,current)
        summary('stopped')
        write(output/'stop.json',{'error':str(error),'type':type(error).__name__,'at':utc_now(),'docker_timeouts':docker.timeouts})
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=ROOT/'artifacts/private/m1-v7')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--auth-file',type=Path,default=Path.home()/'.codex/auth.json')
    parser.add_argument('--agent-image',default='arp-m2-agent:linux-v1')
    parser.add_argument('--proxy-image',default='arp-m2-proxy:linux-v1')
    parser.add_argument('--probes-only',action='store_true')
    args = parser.parse_args()
    run_batch(args.dataset,args.output,args.auth_file,args.agent_image,args.proxy_image,args.probes_only)

if __name__=='__main__': main()
