"""Record supplied human labels and compare them with unchanged M3 predictions.

No agents, evaluators, or rule generation are invoked by this review step.
"""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from .m3 import ROOT, validate_freeze
from .rules import LABELS


def secondary(value):
    return set(value) if isinstance(value, list) else {v.strip() for v in value.split(',') if v.strip()}


def compare(rows):
    n = len(rows)
    if not n:
        raise ValueError('Agreement requires labeled rows')
    truth = Counter(r['human_primary'] for r in rows)
    predicted = Counter(r['rule_primary'] for r in rows)
    matches = sum(r['human_primary'] == r['rule_primary'] for r in rows)
    expected = sum(truth[k] * predicted[k] for k in LABELS) / n**2
    observed = matches / n
    confusion = Counter((r['human_primary'], r['rule_primary']) for r in rows)
    covered = [r for r in rows if r['rule_primary'] != 'unclassified']
    failures = [r for r in rows if r['outcome'] == 'fail']
    per_class = {}
    secondary_classes = {}
    for name in LABELS:
        tp = confusion[name, name]
        support, called = truth[name], predicted[name]
        per_class[name] = {
            'human_support': support, 'rule_predictions': called, 'true_positive': tp,
            'false_positive': called - tp, 'false_negative': support - tp,
            'precision': tp / called if called else None,
            'recall': tp / support if support else None,
            'status': 'measured' if support or called else 'not measured (absent in both)',
        }
        human_count = sum(name in secondary(r['human_secondary']) for r in rows)
        rule_count = sum(name in secondary(r['rule_secondary']) for r in rows)
        both = sum(name in secondary(r['human_secondary']) & secondary(r['rule_secondary']) for r in rows)
        secondary_classes[name] = {
            'human_support': human_count, 'rule_predictions': rule_count, 'true_positive': both,
            'false_positive': rule_count - both, 'false_negative': human_count - both,
            'precision': both / rule_count if rule_count else None,
            'recall': both / human_count if human_count else None,
            'status': 'measured' if human_count or rule_count else 'not measured (absent in both)',
        }
    return {
        'n': n, 'primary_exact_matches': matches, 'primary_exact_agreement': observed,
        'primary_kappa': (observed - expected) / (1 - expected) if expected < 1 else None,
        'kappa_definition': 'All primary categories, including unclassified as a distinct prediction; no excluded abstentions.',
        'primary_confusion': [{'human': h, 'rule': p, 'count': count} for (h, p), count in sorted(confusion.items())],
        'primary_per_class': per_class,
        'secondary_exact_matches': sum(secondary(r['human_secondary']) == secondary(r['rule_secondary']) for r in rows),
        'secondary_exact_agreement': sum(secondary(r['human_secondary']) == secondary(r['rule_secondary']) for r in rows) / n,
        'joint_exact_matches': sum(r['human_primary'] == r['rule_primary'] and secondary(r['human_secondary']) == secondary(r['rule_secondary']) for r in rows),
        'secondary_per_class': secondary_classes,
        'abstentions': n - len(covered), 'coverage': len(covered) / n,
        'covered_exact_agreement': sum(r['human_primary'] == r['rule_primary'] for r in covered) / len(covered) if covered else None,
        'failed_outcomes': len(failures),
        'failed_outcome_coverage': sum(r['rule_primary'] != 'unclassified' for r in failures) / len(failures) if failures else None,
        'disagreements': [r['trajectory'] for r in rows if r['human_primary'] != r['rule_primary'] or secondary(r['human_secondary']) != secondary(r['rule_secondary'])],
    }


def record():
    freeze = validate_freeze()
    supplied_path = ROOT / 'review/m3_human_labels.json'
    supplied = json.loads(supplied_path.read_text(encoding='utf-8'))
    if supplied['reviewer'] != 'Swaroop':
        raise ValueError('Reviewer differs from the supplied review')
    decisions = {r['trajectory']: r for r in supplied['labels']}
    expected_ids = {f'M3-{i:02d}' for i in range(1, 13)}
    if len(supplied['labels']) != 12 or set(decisions) != expected_ids:
        raise ValueError('Exactly twelve unique human decisions required')
    sheet = ROOT / 'review/m3_labeling_sheet.csv'
    with sheet.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        rows = list(reader)
    summary_path = ROOT / 'results/m3_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    predictions = {r['trajectory']: r for r in summary['rule_labels']}
    bundle_path = ROOT / 'review/m3_labeling_evidence.json'
    bundle = json.loads(bundle_path.read_text(encoding='utf-8'))
    evidence = {r['trajectory']: r for r in bundle['rows']}
    if len(rows) != 12 or set(r['trajectory'] for r in rows) != expected_ids:
        raise ValueError('Sheet rows differ from the approved scope')
    for row in rows:
        key = row['trajectory']
        decision, prediction, detail = decisions[key], predictions[key], evidence[key]
        if row['task'] != decision['task'] or row['task'] != prediction['task_id']:
            raise ValueError('Task identity differs')
        if (row['rule_primary'] != prediction['primary'] or secondary(row['rule_secondary']) != set(prediction['secondary'])
                or detail['rule_primary'] != prediction['primary'] or detail['rule_secondary'] != prediction['secondary']
                or decision['events_sha256'] != prediction['events_sha256'] or detail['events_sha256'] != prediction['events_sha256']):
            raise ValueError('Original rule predictions or trajectory provenance differs')
        if decision['human_primary'] not in LABELS or not secondary(decision['human_secondary']) <= set(LABELS):
            raise ValueError('Unsupported human label')
        for field in ['human_primary', 'human_secondary', 'human_notes']:
            value = decision[field]
            row[field] = ', '.join(value) if isinstance(value, list) else value
            detail[field] = value
        detail['reviewer'] = supplied['reviewer']
        detail['recorded_at'] = supplied['recorded_at']
    development = compare([r for r in rows if r['review_role'] == 'development calibration'])
    confirmation = compare([r for r in rows if r['review_role'] == 'held-out confirmation'])
    assert development['n'] == 4 and confirmation['n'] == 8
    agreement = {
        'milestone': 'M3', 'status': 'completed_approved_reduced_scope_stop_before_M4',
        'reviewer': supplied['reviewer'], 'recorded_at': supplied['recorded_at'],
        'human_labels_supplied': 12, 'label_provenance': supplied['source'],
        'human_labels_sha256': hashlib.sha256(supplied_path.read_bytes()).hexdigest(),
        'rubric_sha256': freeze['rubric_sha256'], 'intervention_sha256': freeze['intervention_sha256'],
        'held_out_confirmation': confirmation, 'development_calibration': development,
        'limitations': ['Only eight held-out task clusters; four development rows are calibration, not validation.',
                        'One human reviewer, unblinded to rule predictions; possible anchoring. Inter-human agreement not measured.',
                        'The reviewer inspected hidden failure evidence for M3-08 and M3-10; the frozen rule uses public trace evidence and aggregate outcome only.',
                        'Manual labels remain separate from original rule predictions. Unsupported classes are not measured.',
                        'No intervention effect measured; the observation from confirmation is not used to change the frozen intervention.'],
        'M4_started': False, 'additional_agent_or_evaluator_runs': 0,
    }
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    sheet.write_text(stream.getvalue(), encoding='utf-8', newline='')
    bundle.update(status='human_review_recorded', human_labels_supplied=12, reviewer=supplied['reviewer'], recorded_at=supplied['recorded_at'])
    bundle_path.write_text(json.dumps(bundle, indent=2) + '\n', encoding='utf-8', newline='\n')
    page_path = ROOT / 'review/m3_labeling_sheet.html'
    page = page_path.read_text(encoding='utf-8')
    start = page.index('const rows=') + len('const rows=')
    end = page.index('; const columns=', start)
    page = page[:start] + json.dumps(rows).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026') + page[end:]
    page = page.replace('Human labels are blank. Review the evidence, select your primary label, and optionally add secondary labels and evidence references. Export the CSV and return it for agreement analysis.',
                        'All 12 human labels supplied by Swaroop are recorded. The CSV and human-label JSON are the canonical review record; rule predictions remain unchanged.')
    page = page.replace('No independent blinded validation or human labels are claimed yet.', 'This is one supplied human review, with no independent blinded or inter-human validation claim.')
    old_key = 'arp-m3-' + freeze['rubric_sha256']
    page = page.replace(json.dumps(old_key), json.dumps(old_key + '-reviewed-' + agreement['human_labels_sha256']))
    page_path.write_text(page, encoding='utf-8', newline='\n')
    (ROOT / 'results/m3_agreement.json').write_text(json.dumps(agreement, indent=2) + '\n', encoding='utf-8', newline='\n')
    summary['status'] = agreement['status']
    summary['human_labeling'].update(human_labels_supplied=12, reviewer=supplied['reviewer'], recorded_at=supplied['recorded_at'],
                                     agreement='results/m3_agreement.json', held_out_primary_exact_agreement=confirmation['primary_exact_agreement'],
                                     held_out_primary_kappa=confirmation['primary_kappa'], held_out_secondary_exact_agreement=confirmation['secondary_exact_agreement'])
    for path in summary['review_artifacts_sha256']:
        summary['review_artifacts_sha256'][path] = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    summary['verification']['human_fields'] = 'twelve supplied primary labels, secondary sets and notes recorded; reviewer Swaroop'
    summary_path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    return agreement


if __name__ == '__main__':
    result = record()
    print(json.dumps({k: result[k] for k in ['status', 'reviewer', 'human_labels_supplied', 'held_out_confirmation', 'development_calibration']}))
