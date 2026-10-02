import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import threading
import pytest
from arp.adapters import AdapterConfig, cli_command, event_result
from arp.linux_runtime import Docker, DockerStop, agent_command, snapshot, validate_agent
from arp import m2

spec = importlib.util.spec_from_file_location('arp_proxy',Path(__file__).resolve().parents[1]/'docker/proxy.py')
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

@pytest.mark.parametrize('authority', ['github.com:443','pypi.org:443','1.1.1.1:443','chatgpt.com.evil.org:443',
    'chatgpt.com:80','user@chatgpt.com:443','chatgpt.com:0443','CHATGPT.COM:443','[::1]:443'])
def test_exact_proxy_allowlist(authority):
    assert proxy.permitted(authority) is None

def test_deny_before_dns(monkeypatch):
    monkeypatch.setattr(proxy.socket,'getaddrinfo',lambda *a,**k:pytest.fail('denied host reached DNS'))
    with proxy.Server(('127.0.0.1',0),proxy.Handler) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            with socket.socket() as client:
                client.connect(server.server_address)
                client.sendall(b'CONNECT github.com:443 HTTP/1.1\r\n\r\n')
                assert client.recv(1024).startswith(b'HTTP/1.1 403')
        finally: server.shutdown(); thread.join(timeout=2)

def test_snapshot_discards_all_history(tmp_path):
    base=tmp_path/'base'; (base/'.git/objects').mkdir(parents=True)
    (base/'.git/objects/secret').write_text('old history')
    (base/'TASK.md').write_text('task')
    (base/'a.py').write_bytes(b'buggy')
    dest=tmp_path/'input'; snapshot(base,dest)
    assert not (dest/'.git').exists()
    assert {p.name for p in dest.iterdir()}=={'TASK.md','a.py'}
    assert (dest/'a.py').read_bytes()==b'buggy'

def test_snapshot_rejects_links(tmp_path):
    base=tmp_path/'base'; base.mkdir(); (base/'TASK.md').write_text('task')
    try: (base/'link').symlink_to(base/'TASK.md')
    except OSError: pytest.skip('host symlink privilege unavailable')
    with pytest.raises(ValueError): snapshot(base,tmp_path/'input')

def test_agent_mounts_only_snapshot_and_readonly_auth(tmp_path):
    base=tmp_path/'input'; base.mkdir()
    auth=tmp_path/'auth.json'; auth.write_text('not a real credential')
    command=agent_command('image','agent','internal','172.30.0.10',base,auth)
    mounts=[command[i+1] for i,arg in enumerate(command) if arg=='--mount']
    assert len(mounts)==2 and all(m.endswith(',readonly') for m in mounts)
    assert not any('docker.sock' in m or '.git' in m for m in mounts)
    assert command[command.index('--network')+1]=='internal'
    assert command[command.index('--dns')+1]=='127.0.0.1'
    assert '--read-only' in command and '--cap-drop' in command

def inspected(tmp_path):
    workspace=tmp_path/'input'; auth=tmp_path/'auth.json'
    return workspace,auth,{'Mounts':[
        {'Type':'bind','Source':str(workspace.resolve()),'Destination':'/input','RW':False},
        {'Type':'bind','Source':str(auth.resolve()),'Destination':'/auth/auth.json','RW':False}],
        'Config':{'User':'1000:1000','Env':[]},'NetworkSettings':{'Networks':{'internal':{}}},
        'HostConfig':{'ReadonlyRootfs':True,'Privileged':False,'CapAdd':None,'CapDrop':['ALL'],
            'NetworkMode':'internal','Dns':['127.0.0.1'],'PortBindings':{}}}

@pytest.mark.parametrize('change',['extra_mount','writable_auth','another_network','root','privileged','provider_key'])
def test_inspection_rejects_boundary_changes(tmp_path,change):
    workspace,auth,info=inspected(tmp_path)
    validate_agent(info,workspace,auth,'internal')
    if change=='extra_mount': info['Mounts'].append({'Type':'bind','Destination':'/private'})
    elif change=='writable_auth': info['Mounts'][1]['RW']=True
    elif change=='another_network': info['NetworkSettings']['Networks']['egress']={}
    elif change=='root': info['Config']['User']='root'
    elif change=='privileged': info['HostConfig']['Privileged']=True
    elif change=='provider_key': info['Config']['Env']=['OPENAI_API_KEY=injected']
    with pytest.raises(ValueError): validate_agent(info,workspace,auth,'internal')

def test_cli_pin_and_web_search_off():
    command=cli_command(AdapterConfig('actual-model','medium'))
    assert 'model="actual-model"' in command and 'model_reasoning_effort="medium"' in command
    assert 'web_search="disabled"' in command and 'forced_login_method="chatgpt"' in command
    assert '--ignore-user-config' in command and 'mcp_servers={}' in command
    assert '--dangerously-bypass-approvals-and-sandbox' in command
    assert not any('windows' in arg or 'ARP_MCP' in arg for arg in command)

def test_docker_second_timeout_is_recorded(tmp_path,monkeypatch):
    def timeout(command,**kwargs): raise subprocess.TimeoutExpired(command,kwargs['timeout'])
    monkeypatch.setattr(subprocess,'run',timeout)
    docker=Docker(tmp_path)
    with pytest.raises(DockerStop): docker.call(['info'])
    with pytest.raises(DockerStop,match='2/2'): docker.call(['info'])
    assert json.loads((tmp_path/'docker_timeouts.json').read_text())['count']==2
    with pytest.raises(DockerStop,match='2/2'): docker.call(['info'])
    assert docker.timeouts == 2 and len(docker.commands) == 2

def test_probe_failure_never_enters_development_plan(tmp_path,monkeypatch):
    root=tmp_path/'root'; dataset=root/'artifacts/private/m1-v7'; dataset.mkdir(parents=True)
    tasks=[{'task_id':task,'split':'development','human_acceptance':'accepted'} for task in {t for t,_ in m2.PLAN}]
    (dataset/'tasks.json').write_text(json.dumps(tasks))
    auth=tmp_path/'auth.json'; auth.write_text(json.dumps({'auth_mode':'chatgpt','tokens':{'fake':'fixture'}}))
    monkeypatch.setattr(m2,'ROOT',root)
    class FakeDocker:
        timeouts=0
        def __init__(self,*a): pass
        def call(self,*a,**k): return subprocess.CompletedProcess([],0,b'28.5.1 linux')
        def inspect(self,*a): return {'Id':'image','RootFS':{'Layers':['base']}}
    monkeypatch.setattr(m2,'Docker',FakeDocker)
    class FailedProxy:
        def __init__(self,*a): pass
        def __enter__(self): raise RuntimeError('probe gate failed')
        def __exit__(self,*a): pass
    monkeypatch.setattr(m2,'ProxyNetwork',FailedProxy)
    monkeypatch.setattr(m2,'AgentContainer',lambda *a,**k:pytest.fail('agent launched after failed gate'))
    output=root/'artifacts/private/run'
    with pytest.raises(RuntimeError,match='probe gate'): m2.run_batch(dataset,output,auth,'agent','proxy')
    assert json.loads((output/'summary.json').read_text())['completed_smoke_attempts']==0
    assert not any(output.glob('*baseline*'))

def test_missing_code_mode_runtime_is_infrastructure_not_completed_task():
    raw = b'{"type":"item.completed","item":{"type":"error","message":"Code Mode is unavailable because code-mode host is disabled."}}\n{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":1}}\n'
    status, usage = event_result(raw, '', 0)
    assert status == 'tool_runtime_unavailable'
    assert usage['turns'][0]['input_tokens'] == 10

def test_available_runtime_warning_does_not_classify_agent_text_as_failure():
    raw = b'{"type":"item.completed","item":{"type":"agent_message","text":"Code Mode is unavailable in the old version."}}\n{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":1}}\n'
    assert event_result(raw, '', 0)[0] == 'completed'

def test_item_error_usage_limit_stops_without_completed_turn():
    raw = b'{"type":"item.completed","item":{"type":"error","message":"You have hit your usage limit"}}\n'
    assert event_result(raw, '', 1) == ('usage_limit', 'not measured')
