"""Descriptive audit of existing evidence only; never executes an agent or evaluator."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = re.compile(r"ERROR collecting|Interrupted: \d+ errors? during collection")
METADATA = re.compile(r"^E\s+importlib\.metadata\.PackageNotFoundError: No package metadata was found for click\s*$", re.M)
SUMMARY = re.compile(r"^\s*=*\s*(?P<counts>\d+ (?:passed|failed|skipped|deselected|xfailed|xpassed|errors?)(?:, \d+ (?:passed|failed|skipped|deselected|xfailed|xpassed|errors?))*) in [\d.]+s(?: .*)?\s*=*\s*$")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_diagnostics(output: str) -> dict:
    """Require emitted pytest evidence; neither quoted source nor shell exit is a test outcome."""
    summaries = [line.strip() for line in output.splitlines() if SUMMARY.fullmatch(line)]
    collection = bool(COLLECTION.search(output))
    failed = collection or any(re.search(r"\b[1-9]\d* (?:failed|errors?)\b", line) for line in summaries)
    return {"metadata_collection_error": collection and bool(METADATA.search(output)),
            "pytest_failed": failed, "pytest_summary_lines": summaries}


def build(root: Path = ROOT) -> dict:
    summary_path = root / 'results/m5_summary.json'
    plan_path = root / 'results/m5_plan.json'
    human_path = root / 'review/m3_human_labels.json'
    summary = json.loads(summary_path.read_text())
    plan = json.loads(plan_path.read_text())
    human = json.loads(human_path.read_text())
    agents = root / plan['intervention_path']
    assert sha(agents) == plan['intervention_sha256']
    guidance = agents.read_text(encoding='utf-8').strip()
    reused = {r['run_id'] if 'run_id' in r else Path(r['path']).name: r['path'] for r in plan['reused_baselines']}
    attempts = []
    for saved in summary['attempts']:
        rel = reused[saved['run_id']] if saved['source'].startswith('M3') else 'artifacts/private/m5-run-001/' + saved['run_id']
        path = root / rel
        assert sha(path/'events.jsonl') == saved['events_sha256'], rel
        assert sha(path/'result.json') == saved['result_sha256'], rel
        result = json.loads((path/'result.json').read_text())
        public = {r['item_id']: r for r in saved['public_pytest_runs']}
        evidence, reads, corrections, installs = [], [], [], []
        events = [json.loads(line) for line in (path/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        for line, event in enumerate(events, 1):
            item = event.get('item', {})
            if event.get('type') != 'item.completed' or item.get('type') != 'command_execution':
                continue
            command, output = item.get('command', ''), item.get('aggregated_output', '')
            ref = {'item_id': item['id'], 'jsonl_line': line, 'trace_path': rel+'/events.jsonl'}
            if guidance in output.replace('\r\n', '\n') and item.get('exit_code') == 0:
                reads.append({**ref, 'command': command, 'full_frozen_text_visible': True})
            if re.search(r'pip\s+install\b', command) and '/tmp/click-site' in command:
                installs.append({**ref, 'command': command, 'exit_code': item.get('exit_code'),
                                 'install_success_lines': [l for l in output.splitlines() if l.startswith('Successfully installed click-')]})
            if item['id'] in public:
                diag = output_diagnostics(output)
                detail = {**ref, **diag, 'command': command, 'exit_code': item.get('exit_code'),
                          'original_failed_flag': public[item['id']]['failed_run'],
                          'metadata_before_install_command': diag['metadata_collection_error'] and not installs,
                          'evidence': '\n'.join(l for l in output.splitlines() if
                              METADATA.fullmatch(l) or COLLECTION.search(l) or SUMMARY.fullmatch(l))}
                evidence.append(detail)
                if detail['original_failed_flag'] != diag['pytest_failed']:
                    corrections.append({**detail, 'reason': 'Pytest passed; a subsequent Git command failed.',
                                        'tail': '\n'.join(output.splitlines()[-4:])})
        # Every saved public-test command must have a matching completed event.
        assert len(evidence) == len(public)
        failed_tests = sorted(result.get('evaluation', {}).get('failures', []))
        attempts.append({k: saved[k] for k in ('run_id', 'task_id', 'split', 'arm', 'repeat', 'source',
                        'success', 'state', 'agent_wall_seconds', 'native_tool_calls', 'usage', 'events_sha256', 'result_sha256')} |
                       {'trace_path': rel+'/events.jsonl', 'hidden_failed_test_names': failed_tests,
                        'metadata_error_attempt': any(e['metadata_collection_error'] for e in evidence),
                        'metadata_error_commands': sum(e['metadata_collection_error'] for e in evidence),
                        'trace_confirmed_failed_public_commands': sum(e['pytest_failed'] for e in evidence),
                        'original_failed_public_commands': saved['failed_public_pytest_runs'],
                        'public_command_evidence': evidence, 'agents_read_evidence': reads,
                        'install_command_evidence': installs, 'metric_corrections': corrections})
    groups = []
    for population in ('confirmation', 'all_tasks'):
        for arm in ('baseline', 'intervention'):
            rows = [r for r in attempts if r['arm'] == arm and (population == 'all_tasks' or r['split'] == population)]
            groups.append({'population': population, 'arm': arm, 'attempts': len(rows),
                          'metadata_error_attempts': sum(r['metadata_error_attempt'] for r in rows),
                          'metadata_error_commands': sum(r['metadata_error_commands'] for r in rows),
                          'failed_public_commands': sum(r['trace_confirmed_failed_public_commands'] for r in rows),
                          'original_failed_public_commands': sum(r['original_failed_public_commands'] for r in rows),
                          'native_tool_calls': sum(r['native_tool_calls'] for r in rows),
                          'input_tokens': sum(r['usage']['input_tokens'] for r in rows if isinstance(r['usage'], dict)),
                          'cached_input_tokens': sum(r['usage']['cached_input_tokens'] for r in rows if isinstance(r['usage'], dict)),
                          'output_tokens': sum(r['usage']['output_tokens'] for r in rows if isinstance(r['usage'], dict)),
                          'usage_missing': sum(not isinstance(r['usage'], dict) for r in rows),
                          'agents_full_text_reads': sum(bool(r['agents_read_evidence']) for r in rows) if arm == 'intervention' else None})
    failures = []
    for task in sorted({r['task_id'] for r in attempts}):
        rows = [r for r in attempts if r['task_id'] == task]
        if all(r['success'] for r in rows):
            continue
        entry = {'task_id': task, 'split': rows[0]['split']}
        for arm in ('baseline', 'intervention'):
            pair = sorted((r for r in rows if r['arm'] == arm), key=lambda r: r['repeat'])
            entry[arm] = {'outcomes': ['pass' if r['success'] else 'fail' for r in pair],
                          'run_ids': [r['run_id'] for r in pair],
                          'consistent_outcome': pair[0]['success'] == pair[1]['success'],
                          'hidden_failure_counts': [len(r['hidden_failed_test_names']) for r in pair],
                          'same_hidden_failure_set': pair[0]['hidden_failed_test_names'] == pair[1]['hidden_failed_test_names'] if not any(r['success'] for r in pair) else None}
        failures.append(entry)
    labels = []
    for population in ('confirmation', 'all_M3'):
        rows = [r for r in human['labels'] if population == 'all_M3' or int(r['trajectory'].split('-')[1]) >= 5]
        labels.append({'population': population, 'n': len(rows),
                       'primary': dict(Counter(r['human_primary'] for r in rows)),
                       'secondary': dict(Counter(l for r in rows for l in r['human_secondary']))})
    return {'milestone': 'M4', 'status': 'descriptive_recorded_evidence_only',
            'definitions': {'population': 'Only the 48 experimental M5 slots, including eight retained M3 baselines. Earlier calibration and smokes excluded.',
                            'metadata_error': 'A completed public-pytest command emits both a collection interruption and the Click PackageNotFoundError traceback line.',
                            'failed_public_commands': 'Completed public-pytest shell commands with emitted terminal failed/error summaries or collection errors. Shell exit alone is not a pytest failure. One command may contain multiple invocations; no multiple visible terminal summaries occurred in these saved commands.',
                            'tokens': 'CLI-recorded token sums. Cached input is a subset of input, never added again. No paid cost estimate.',
                            'agents_read': 'A successful completed command exposes the entire frozen AGENTS text. This establishes exposure, not comprehension or adherence.',
                            'repeat': 'Nominal repeat 1 then repeat 2, not launch order.',
                            'inference': 'Descriptive diagnostics only. No new hypothesis tests or changes to frozen metrics, rules, labels, treatment, or outcomes.'},
            'sources': {str(p.relative_to(root)).replace('\\', '/'): sha(p) for p in (summary_path, plan_path, human_path,
                      root/'results/m1_summary.json', root/'results/m3_agreement.json', root/'docs/m3_human_review.md', agents)},
            'groups': groups, 'failure_consistency': failures, 'human_label_breakdown': labels,
            'metric_corrections': [c | {'run_id': r['run_id']} for r in attempts for c in r['metric_corrections']],
            'attempts': attempts}


def write(root: Path = ROOT) -> dict:
    data = build(root)
    (root/'results/m4_diagnostics.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')
    fields = ['run_id', 'task_id', 'split', 'arm', 'repeat', 'success', 'agent_wall_seconds', 'metadata_error_attempt',
              'metadata_error_commands', 'trace_confirmed_failed_public_commands', 'original_failed_public_commands',
              'native_tool_calls', 'input_tokens', 'cached_input_tokens', 'output_tokens', 'agents_read', 'agents_read_reference', 'trace_path']
    with (root/'review/m4_attempt_diagnostics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for r in data['attempts']:
            out = {k: r[k] for k in fields if k in r}
            out.update({k: r['usage'].get(k) for k in ('input_tokens', 'cached_input_tokens', 'output_tokens')})
            out['agents_read'] = bool(r['agents_read_evidence']) if r['arm'] == 'intervention' else 'not delivered'
            out['agents_read_reference'] = '; '.join(f"{e['item_id']} at line {e['jsonl_line']}" for e in r['agents_read_evidence'])
            writer.writerow(out)
    return data


if __name__ == '__main__':
    d = write()
    print(json.dumps({'groups': d['groups'], 'metric_corrections': len(d['metric_corrections']), 'attempts': len(d['attempts'])}, indent=2))
