"""Docker-owned Linux agent and exact-domain proxy; no native host task tools."""
from __future__ import annotations
from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

class DockerStop(RuntimeError):
    pass

class Docker:
    """Bound all control operations and persist timeouts across this run."""
    def __init__(self, evidence: Path):
        self.evidence = evidence
        self.timeouts = 0
        self.commands = []
    def call(self, args, *, timeout=30, check=True, input=None):
        if self.timeouts >= 2:
            raise DockerStop('Docker timed out (2/2); stop live work')
        command = ['docker', *args]
        self.commands.append(command)
        (self.evidence / 'docker_commands.json').write_text(json.dumps(self.commands, indent=2), encoding='utf-8')
        try:
            result = subprocess.run(command, input=input, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            self.timeouts += 1
            (self.evidence / 'docker_timeouts.json').write_text(json.dumps({'count': self.timeouts, 'command': command}), encoding='utf-8')
            raise DockerStop(f'Docker timed out ({self.timeouts}/2); stop live work' if self.timeouts >= 2 else 'Docker operation timed out; preserve evidence and attempt owned-resource cleanup') from error
        if check and result.returncode:
            raise RuntimeError(f'Docker command failed: {args[0]}: ' + result.stderr.decode(errors='replace')[:2000])
        return result
    def inspect(self, name):
        return json.loads(self.call(['inspect', name]).stdout)[0]

def snapshot(base: Path, destination: Path):
    """Copy only frozen buggy files and TASK.md, with no Git objects or links."""
    destination.mkdir()
    for source in base.rglob('*'):
        relative = source.relative_to(base)
        if '.git' in relative.parts:
            continue
        if source.is_symlink():
            raise ValueError('Frozen workspace has a symlink')
        target = destination / relative
        if source.is_dir(): target.mkdir(exist_ok=True)
        elif source.is_file(): shutil.copyfile(source, target)
    if (destination / '.git').exists() or not (destination / 'TASK.md').is_file():
        raise ValueError('Invalid task snapshot')

class ProxyNetwork(AbstractContextManager):
    def __init__(self, docker: Docker, image: str):
        self.docker, self.image = docker, image
        stem = 'arp-m2-' + uuid.uuid4().hex
        self.internal, self.egress, self.name = stem+'-internal', stem+'-egress', stem+'-proxy'
        self.resources = []
    def __enter__(self):
        try:
            self.resources.append(('network', self.internal))
            self.docker.call(['network', 'create', '--internal', '--subnet', '192.0.2.0/24', self.internal])
            self.resources.append(('network', self.egress))
            self.docker.call(['network', 'create', self.egress])
            import ipaddress
            net = json.loads(self.docker.call(['network', 'inspect', self.internal]).stdout)[0]
            subnet = ipaddress.ip_network(net['IPAM']['Config'][0]['Subnet'])
            self.ip = str(subnet.network_address + 10)
            self.resources.append(('container', self.name))
            self.docker.call(['create', '--name', self.name, '--network', self.internal,
                '--ip', self.ip, '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges', '--pids-limit', '64',
                '--memory', '128m', '--cpus', '0.25', '--sysctl', 'net.ipv4.ip_forward=0',
                self.image, self.ip])
            self.docker.call(['network', 'connect', self.egress, self.name])
            self.docker.call(['start', self.name])
            info = self.docker.inspect(self.name)
            assert len(info['NetworkSettings']['Networks']) == 2
            network = json.loads(self.docker.call(['network', 'inspect', self.internal]).stdout)[0]
            assert network['Internal'] is True
            (self.docker.evidence / 'proxy_inspect.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
            (self.docker.evidence / 'internal_network.json').write_text(json.dumps(network, indent=2), encoding='utf-8')
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise
    def __exit__(self, *args):
        errors = []
        if any(kind == 'container' for kind, _ in self.resources) and self.docker.timeouts < 2:
            try:
                logs = self.docker.call(['logs', self.name], check=False)
                (self.docker.evidence / 'proxy.jsonl').write_bytes(logs.stdout + logs.stderr)
            except (DockerStop, RuntimeError) as error: errors.append(str(error))
        for kind, name in reversed(self.resources):
            if self.docker.timeouts >= 2: break
            try:
                self.docker.call(['rm', '--force', name] if kind == 'container' else ['network', 'rm', name])
            except (DockerStop, RuntimeError) as error: errors.append(str(error))
        if errors:
            (self.docker.evidence / 'cleanup_errors.json').write_text(json.dumps(errors), encoding='utf-8')
            if args[0] is None: raise DockerStop('Owned proxy/network cleanup failed: ' + '; '.join(errors))

def agent_command(image, name, network, proxy_ip, workspace, auth):
    if not workspace.is_dir() or not auth.is_file():
        raise ValueError('Task input and saved ChatGPT authentication are required')
    proxy = f'http://{proxy_ip}:3128'
    command = ['run', '--detach', '--name', name, '--network', network,
        '--dns', '127.0.0.1', '--read-only', '--user', '1000:1000',
        '--cpus', '2', '--memory', '3g', '--pids-limit', '256',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--tmpfs', '/tmp:rw,exec,size=512m,mode=1777',
        '--tmpfs', '/workspace:rw,exec,size=512m,uid=1000,gid=1000,mode=700',
        '--tmpfs', '/codex:rw,exec,size=256m,uid=1000,gid=1000,mode=700',
        '--mount', f'type=bind,source={workspace.resolve()},target=/input,readonly',
        '--mount', f'type=bind,source={auth.resolve()},target=/auth/auth.json,readonly',
        '-e', 'HOME=/codex', '-e', 'CODEX_HOME=/codex', '-e', 'PYTHONPATH=/workspace/src',
        '-e', 'HTTP_PROXY='+proxy, '-e', 'HTTPS_PROXY='+proxy, '-e', 'ALL_PROXY='+proxy,
        '-e', 'http_proxy='+proxy, '-e', 'https_proxy='+proxy, '-e', 'NO_PROXY=',
        image, 'sh', '-c',
        'cp -a /input/. /workspace/ && chmod -R u+w /workspace && ln -s /auth/auth.json /codex/auth.json && exec sleep infinity']
    return command

class AgentContainer(AbstractContextManager):
    def __init__(self, docker, image, network, base, auth, evidence):
        self.docker, self.image, self.network = docker, image, network
        self.base, self.auth, self.evidence = base, auth, evidence
        self.name = 'arp-m2-agent-' + uuid.uuid4().hex
        self.created = False
    def __enter__(self):
        try:
            command = agent_command(self.image, self.name, self.network.internal, self.network.ip, self.base, self.auth)
            (self.evidence / 'container_command.json').write_text(json.dumps(['docker', *command], indent=2), encoding='utf-8')
            self.created = True
            self.docker.call(command)
            self.docker.call(['exec', self.name, 'sh', '-c', 'for i in $(seq 1 150); do if test -L /codex/auth.json; then test -f /workspace/TASK.md && test ! -e /workspace/.git; exit $?; fi; sleep .1; done; exit 91'], timeout=30)
            info = self.docker.inspect(self.name)
            validate_agent(info, self.base, self.auth, self.network.internal)
            (self.evidence / 'inspect.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise
    def exec(self, command, input=None, timeout=30):
        return self.docker.call(['exec', '-i', '--user', '1000:1000', self.name, *command], input=input, timeout=timeout)
    def __exit__(self, *args):
        if self.created and self.docker.timeouts < 2:
            logs = self.docker.call(['logs', self.name], check=False)
            (self.evidence / 'container_startup.log').write_bytes(logs.stdout + logs.stderr)
            self.docker.call(['rm', '--force', self.name])
            self.created = False

def validate_agent(info, workspace, auth, network):
    mounts = info['Mounts']
    expected = {'/input': str(workspace.resolve()), '/auth/auth.json': str(auth.resolve())}
    binds = [m for m in mounts if m['Type'] == 'bind']
    if {m['Destination'] for m in binds} != set(expected) or len(binds) != 2:
        raise ValueError('Unexpected agent bind mount')
    for m in binds:
        # Docker Desktop converts Windows drive paths in inspection results.
        normalized = m['Source'].replace('\\', '/').lower()
        local = expected[m['Destination']].replace('\\', '/').lower()
        if m['RW'] or not (normalized == local or normalized.endswith(local[2:])):
            raise ValueError('Wrong or writable agent input')
    host = info['HostConfig']
    if info['Config']['User'] != '1000:1000' or not host['ReadonlyRootfs'] or host['Privileged']:
        raise ValueError('Agent privileges differ')
    if host['CapAdd'] or {x.upper() for x in host['CapDrop']} != {'ALL'}:
        raise ValueError('Agent capabilities differ')
    if set(info['NetworkSettings']['Networks']) != {network} or host['NetworkMode'] != network:
        raise ValueError('Agent has another network')
    if host['Dns'] != ['127.0.0.1'] or host['PortBindings']:
        raise ValueError('Agent DNS or port exposure differs')
    if any('API_KEY=' in value or 'BASE_URL=' in value for value in info['Config']['Env']):
        raise ValueError('Injected provider environment')
