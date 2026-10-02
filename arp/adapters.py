"""Headless Codex inside the Linux task container. Evaluation stays on the host."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

CLI_VERSION = 'codex-cli 0.153.1'
DISABLED_FEATURES = ('apps', 'plugins', 'hooks', 'multi_agent', 'multi_agent_v2', 'browser_use',
    'browser_use_external', 'computer_use', 'image_generation', 'in_app_browser',
    'view_image', 'memories', 'workspace_dependencies',
    'skill_search', 'skill_mcp_dependency_install', 'standalone_web_search',
    'unbounded_connection_retries', 'goals', 'sleep_tool', 'tool_suggest',
    'recommended_plugins', 'remote_plugin', 'auth_elicitation')

def utc_now():
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class Limits:
    wall_seconds: int = 900
    paid_api_dollars: int = 0
    def __post_init__(self):
        if self.paid_api_dollars != 0 or not 1 <= self.wall_seconds <= 900:
            raise ValueError('Only the authorized zero-dollar, bounded plan is supported')

@dataclass(frozen=True)
class AdapterConfig:
    model: str | None = None
    reasoning_effort: str | None = None

@dataclass(frozen=True)
class AttemptResult:
    status: str
    returncode: int
    started: str
    finished: str
    seconds: float
    usage: dict | str
    dollar_cost: str
    incremental_paid_api_spend: int
    cli_version: str
    model: str
    inference_settings: dict
    events_sha256: str

class UnsupportedAdapterError(RuntimeError): pass

class DevinAdapter:
    def prepare(self, *args, **kwargs):
        raise UnsupportedAdapterError('Devin is unsupported in the zero-dollar pilot')
    run = cancel = collect = prepare

def event_result(raw: bytes, stderr: str, code: int, cancelled: bool = False):
    events = []
    for line in raw.splitlines():
        try: events.append(json.loads(line))
        except (ValueError, UnicodeError): continue
    errors = [e for e in events if e.get('type') in {'error', 'turn.failed'} or
              e.get('type') == 'item.completed' and e.get('item',{}).get('type') == 'error']
    text = json.dumps(errors) + '\n' + stderr
    usage = [e['usage'] for e in events if e.get('type') == 'turn.completed' and 'usage' in e]
    completed = any(e.get('type') == 'turn.completed' for e in events)
    limit = re.search(r'usage limit|usage_limit|rate limit|rate_limit|insufficient_quota|quota exceeded|hit your.*limit', text, re.I)
    runtime_missing = any(e.get('type') == 'item.completed' and e.get('item',{}).get('type') == 'error' and 'Code Mode is unavailable' in e['item'].get('message','') for e in events)
    status = ('usage_limit' if limit else 'tool_runtime_unavailable' if runtime_missing else 'cancelled' if cancelled else
              'completed' if completed and code == 0 else 'provider_or_transport_failure')
    return status, {'turns': usage} if usage else 'not measured'

def cli_command(config: AdapterConfig):
    command = ['codex', 'exec', '--json', '--ignore-user-config', '--ignore-rules',
        '--strict-config', '--skip-git-repo-check', '--color', 'never',
        '--dangerously-bypass-approvals-and-sandbox', '-C', '/workspace']
    for feature in DISABLED_FEATURES: command += ['--disable', feature]
    overrides = ['forced_login_method="chatgpt"', 'model_provider="openai"', 'web_search="disabled"',
        'approval_policy="never"', 'project_doc_max_bytes=0',
        'features.skip_host_skill_discovery=true', 'skills.include_instructions=false',
        'features.respect_system_proxy=true', 'mcp_servers={}',
        'analytics.enabled=false', 'features.code_mode_host=true']
    if config.model: overrides.append('model='+json.dumps(config.model))
    if config.reasoning_effort: overrides.append('model_reasoning_effort='+json.dumps(config.reasoning_effort))
    for override in overrides: command += ['-c', override]
    return command + ['-']

MODEL_METADATA = """
import json
from pathlib import Path
defaults = {}
cache_files = []
for path in Path('/codex').glob('*model*.json'):
    cache_files.append(path.name)
    try: cache = json.loads(path.read_text())
    except ValueError: continue
    models = cache.get('models', [])
    if isinstance(models, dict): models = models.get('models', [])
    for model in models:
        defaults[model.get('slug')] = model.get('default_reasoning_level')
result = []
for path in Path('/codex/sessions').rglob('*.jsonl'):
    for line in path.read_text().splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if event.get('type') == 'turn_context':
            p = event['payload']
            entry = {k:p[k] for k in ('model','effort','reasoning_effort','model_provider') if k in p}
            entry['context_keys'] = sorted(p)
            settings = (p.get('collaboration_mode') or {}).get('settings') or {}
            entry['effective_reasoning_effort'] = settings.get('reasoning_effort')
            entry['catalog_default_reasoning_effort'] = defaults.get(p.get('model'))
            entry['cache_files'] = cache_files
            result.append(entry)
print(json.dumps(result))
"""

class CodexCLIAdapter:
    def __init__(self, config):
        self.config, self.process, self.result = config, None, None
        self.cancelled = False
    def prepare(self, container, prompt, evidence, limits=Limits()):
        self.container, self.prompt, self.evidence, self.limits = container, prompt, evidence, limits
        self.command = ['docker','exec','-i','--user','1000:1000',container.name,*cli_command(self.config)]
        (evidence/'cli_command.json').write_text(json.dumps(self.command, indent=2), encoding='utf-8')
        (evidence/'prompt.txt').write_text(prompt, encoding='utf-8')
    def run(self):
        start, started = time.monotonic(), utc_now()
        with (self.evidence/'events.jsonl').open('wb') as output, (self.evidence/'stderr.txt').open('wb') as errors:
            self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=output, stderr=errors)
            try: self.process.communicate(self.prompt.encode(), timeout=self.limits.wall_seconds)
            except subprocess.TimeoutExpired: self.cancel()
        raw = (self.evidence/'events.jsonl').read_bytes()
        stderr = (self.evidence/'stderr.txt').read_text(encoding='utf-8', errors='replace')
        status, usage = event_result(raw, stderr, self.process.returncode, self.cancelled)
        metadata = [] if self.cancelled or self.process.returncode != 0 else json.loads(self.container.exec(['python','-I','-c',MODEL_METADATA]).stdout)
        (self.evidence/'model_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        selected = metadata[-1] if metadata else {}
        model = selected.get('model', 'not measured')
        observed_effort = selected.get('effective_reasoning_effort') or selected.get('effort') or selected.get('reasoning_effort')
        effort = observed_effort or self.config.reasoning_effort or selected.get('catalog_default_reasoning_effort') or 'not measured'
        evidence = ('CLI rollout model and observed rollout reasoning' if observed_effort else
                    'CLI rollout model and explicit client reasoning override' if self.config.reasoning_effort else
                    'CLI rollout model and fetched catalog default reasoning')
        evidence += '; backend served identity not independently exposed'
        if status == 'completed' and (model == 'not measured' or effort == 'not measured'):
            raise RuntimeError('CLI effective model/reasoning metadata missing')
        if status == 'completed' and self.config.model and model != self.config.model:
            raise RuntimeError('CLI model differs from the frozen model')
        if status == 'completed' and self.config.reasoning_effort and effort != self.config.reasoning_effort:
            raise RuntimeError('CLI reasoning differs from the frozen setting')
        self.result = AttemptResult(status, self.process.returncode, started, utc_now(),
            round(time.monotonic()-start,3), usage, 'not measured', 0, CLI_VERSION,
            model, {'reasoning_effort':effort,'evidence':evidence,'observed_reasoning_effort':observed_effort,
                    'catalog_default_reasoning_effort':selected.get('catalog_default_reasoning_effort')}, hashlib.sha256(raw).hexdigest())
        (self.evidence/'adapter_result.json').write_text(json.dumps(asdict(self.result), indent=2), encoding='utf-8')
        return self.result
    def cancel(self):
        self.cancelled = True
        self.container.docker.call(['kill', self.container.name])
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
    def collect(self):
        if self.result is None: raise RuntimeError('Attempt has not terminated')
        return self.result
