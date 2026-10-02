"""Validate the portable report and diagnostic evidence without executing task code."""
import csv
from html.parser import HTMLParser
import json
from .m4_diagnostics import ROOT, build, sha
from .m4_report import render


class Snapshot(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_snapshot = False
        self.data = ''
        self.active_scripts = []
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'script':
            if attributes.get('type') == 'application/json' and attributes.get('id') == 'recorded-data':
                self.in_snapshot = True
            else:
                self.active_scripts.append(attributes)
        if attributes.get('src') or tag == 'link' and attributes.get('href'):
            self.external_assets.append(attributes)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_snapshot = False

    def handle_data(self, data):
        if self.in_snapshot:
            self.data += data


def audit() -> dict:
    d = build()
    assert d == json.loads((ROOT/'results/m4_diagnostics.json').read_text())
    s = json.loads((ROOT/'results/m5_summary.json').read_text())
    p = json.loads((ROOT/'results/m5_plan.json').read_text())
    h = json.loads((ROOT/'review/m3_human_labels.json').read_text())
    agreement = json.loads((ROOT/'results/m3_agreement.json').read_text())
    m1 = json.loads((ROOT/'results/m1_summary.json').read_text())
    agents = (ROOT/p['intervention_path']).read_text(encoding='utf-8')
    report = ROOT/'reports/click_readiness.html'
    text = report.read_text(encoding='utf-8')
    assert text == render(d, s, p, h, agreement, m1, agents)
    parser = Snapshot()
    parser.feed(text)
    embedded = json.loads(parser.data)
    assert embedded['M5'] == s and embedded['human_labels'] == h and embedded['diagnostics'] == d
    assert not parser.external_assets and not parser.active_scripts
    assert len(d['attempts']) == len({(r['task_id'], r['arm'], r['repeat']) for r in d['attempts']}) == 48
    for r in d['attempts']:
        assert r['original_failed_public_commands'] - r['trace_confirmed_failed_public_commands'] == len(r['metric_corrections'])
        assert all(len(e['pytest_summary_lines']) <= 1 for e in r['public_command_evidence'])
        events = [json.loads(l) for l in (ROOT/r['trace_path']).read_text(encoding='utf-8').splitlines()]
        for e in r['agents_read_evidence'] + r['public_command_evidence'] + r['install_command_evidence']:
            raw = events[e['jsonl_line']-1]
            assert raw['type'] == 'item.completed' and raw['item']['id'] == e['item_id']
        if r['arm'] == 'intervention':
            assert r['agents_read_evidence']
            if r['metadata_error_attempt']:
                errors = [e for e in r['public_command_evidence'] if e['metadata_collection_error']]
                assert all(e['metadata_before_install_command'] for e in errors)
                assert any(e['install_success_lines'] and e['jsonl_line'] > max(x['jsonl_line'] for x in errors)
                           for e in r['install_command_evidence'])
    # Verify failure consistency at the test-set level rather than outcome labels alone.
    six = [r['hidden_failed_test_names'] for r in d['attempts'] if r['task_id'] == 'click-006']
    assert len(six) == 4 and len(six[0]) == 2 and all(t == six[0] for t in six)
    ten = [set(r['hidden_failed_test_names']) for r in d['attempts'] if r['task_id'] == 'click-010' and r['arm'] == 'baseline']
    assert not ten[0] & ten[1]
    with (ROOT/'review/m4_attempt_diagnostics.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 48
    for group in d['groups']:
        subset = [r for r in rows if r['arm'] == group['arm'] and (group['population'] == 'all_tasks' or r['split'] == 'confirmation')]
        assert sum(int(r['native_tool_calls']) for r in subset) == group['native_tool_calls']
        assert sum(int(r['trace_confirmed_failed_public_commands']) for r in subset) == group['failed_public_commands']
    return {'status': 'passed', 'attempts': 48, 'intervention_reads_verified': 24,
            'metric_corrections': len(d['metric_corrections']), 'source_digests': d['sources'],
            'report_sha256': sha(report), 'report_bytes': report.stat().st_size,
            'frozen_human_labels_unchanged': sha(ROOT/'review/m3_human_labels.json') == agreement['human_labels_sha256'],
            'new_agent_calls': 0, 'new_evaluator_calls': 0, 'new_hypothesis_tests': 0}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
