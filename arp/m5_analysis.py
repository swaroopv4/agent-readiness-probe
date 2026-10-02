"""Prespecified paired task-cluster analysis; no task or model execution."""
import math
import random
from statistics import mean


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def cluster_interval(differences, seed=20261002, resamples=10000, bounded=True):
    if not differences:
        raise ValueError('No paired task clusters')
    rng = random.Random(seed)
    estimate = mean(differences)
    samples = [mean(rng.choices(differences, k=len(differences))) for _ in range(resamples)]
    bootstrap = [percentile(samples, .025), percentile(samples, .975)]
    result = {'estimate': estimate, 'bootstrap_95': bootstrap, 'resamples': resamples,
              'seed': seed, 'clusters': len(differences), 'degenerate': bootstrap[0] == bootstrap[1]}
    if bounded:
        width = math.sqrt(2 * math.log(40) / len(differences))
        result['hoeffding_95'] = [max(-1, estimate - width), min(1, estimate + width)]
        result['hoeffding_half_width'] = width
        result['selected_interval'] = result['hoeffding_95'] if result['degenerate'] else bootstrap
        result['selected_method'] = 'Hoeffding fallback (degenerate bootstrap)' if result['degenerate'] else 'paired task-cluster bootstrap'
        interval = result['selected_interval']
        result['conclusion'] = 'inconclusive' if interval[0] <= 0 <= interval[1] else 'gain' if interval[0] > 0 else 'possible regression'
    return result


def wilson(successes, n):
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    scale = 1 + z*z/n
    middle = (p + z*z/(2*n)) / scale
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / scale
    return [middle-half, middle+half]


def analyze(records, tasks, seed=20261002):
    expected = {(t['task_id'], arm, repeat) for t in tasks for arm in ['baseline', 'intervention'] for repeat in [1, 2]}
    seen = [(r['task_id'], r['arm'], r['repeat']) for r in records]
    if len(seen) != len(set(seen)) or not set(seen) <= expected:
        raise ValueError('Duplicate or unknown experimental slot')
    exclusions = [r for r in records if r['success'] is None]
    missing = sorted(expected - set(seen))
    table = []
    for task in tasks:
        row = {'task_id': task['task_id'], 'split': task['split']}
        for arm in ['baseline', 'intervention']:
            attempts = sorted((r for r in records if r['task_id'] == task['task_id'] and r['arm'] == arm), key=lambda r:r['repeat'])
            observed = [r for r in attempts if r['success'] is not None]
            row[arm] = {'successes': sum(r['success'] for r in observed), 'scored': len(observed), 'planned': 2,
                        'success_rate': mean(r['success'] for r in observed) if observed else None,
                        'mean_wall_seconds': mean(r['agent_wall_seconds'] for r in observed) if observed else None,
                        'attempts': [{k:r[k] for k in ['repeat','state','success','agent_wall_seconds','run_id','source']} for r in attempts]}
        complete = all(row[arm]['scored'] == 2 for arm in ['baseline', 'intervention'])
        row['comparable_complete'] = complete
        row['success_delta'] = row['intervention']['success_rate'] - row['baseline']['success_rate'] if complete else None
        row['wall_delta_seconds'] = row['intervention']['mean_wall_seconds'] - row['baseline']['mean_wall_seconds'] if complete else None
        row['direction'] = 'missing/infrastructure' if not complete else 'gain' if row['success_delta'] > 0 else 'loss' if row['success_delta'] < 0 else 'unchanged'
        table.append(row)
    confirmation = [r for r in table if r['split'] == 'confirmation']
    def group_summary(split):
        selected = table if split == 'all' else [r for r in table if r['split'] == split]
        ids = {r['task_id'] for r in selected}
        out = {'tasks': len(selected), 'planned_attempts_per_arm': 2*len(selected), 'arms': {}}
        for arm in ['baseline','intervention']:
            observed = [r for r in records if r['task_id'] in ids and r['arm'] == arm and r['success'] is not None]
            # Repeats are randomized; first means actual first launch, not repeat number.
            first=[]
            for task_id in ids:
                launches=sorted((r for r in records if r['task_id']==task_id and r['arm']==arm),key=lambda r:(r.get('started') or '',r['repeat']))
                if launches and launches[0]['success'] is not None: first.append(launches[0])
            complete_tasks = [r for r in selected if r[arm]['scored'] == 2]
            out['arms'][arm] = {'successes': sum(r['success'] for r in observed), 'scored_attempts': len(observed),
                'execution_coverage': len(observed)/(2*len(selected)),
                'task_weighted_success_rate': mean(r[arm]['success_rate'] for r in selected) if all(r[arm]['scored'] == 2 for r in selected) else None,
                'mean_wall_seconds': mean(r['agent_wall_seconds'] for r in observed) if observed else None,
                'agent_caps': sum(r['state']=='cancelled' for r in observed),
                'failed_task_attempts': sum(not r['success'] for r in observed),
                'first_attempt_successes': sum(r['success'] for r in first), 'first_attempt_scored': len(first),
                'first_attempt_wilson_95': wilson(sum(r['success'] for r in first),len(first)),
                'pass_at_2_tasks': sum(r[arm]['successes'] > 0 for r in complete_tasks), 'pass_at_2_denominator': len(complete_tasks)}
        if all(r['comparable_complete'] for r in selected):
            out['success_delta'] = mean(r['success_delta'] for r in selected)
            out['wall_delta_seconds'] = mean(r['wall_delta_seconds'] for r in selected)
        else:
            out['success_delta'] = None
            out['wall_delta_seconds'] = None
        return out
    comparable = len(confirmation) == 8 and all(r['comparable_complete'] for r in confirmation)
    primary = cluster_interval([r['success_delta'] for r in confirmation], seed) if comparable else {'conclusion':'incomplete; infrastructure/missing outcomes prevent comparable primary estimate'}
    wall = cluster_interval([r['wall_delta_seconds'] for r in confirmation], seed, bounded=False) if comparable else {'estimate':None}
    wall['definition'] = 'Intervention minus baseline mean agent wall seconds, paired over tasks; includes unsuccessful task attempts and agent caps, excludes infrastructure. No success-only efficiency claim or penalty composite.'
    return {'complete_48_slot_design': len(records)==48 and not missing and not exclusions,
            'primary_confirmation': primary, 'key_secondary_confirmation_wall': wall,
            'confirmation': group_summary('confirmation'), 'development_descriptive': group_summary('development'),
            'all_tasks_descriptive': group_summary('all'), 'task_results': table,
            'gains': [r['task_id'] for r in confirmation if r['direction']=='gain'],
            'losses': [r['task_id'] for r in confirmation if r['direction']=='loss'],
            'unchanged': [r['task_id'] for r in confirmation if r['direction']=='unchanged'],
            'infrastructure_exclusions': [{k:r.get(k) for k in ['run_id','task_id','arm','repeat','state','source']} for r in exclusions],
            'unlaunched_slots': missing, 'human_labels_changed': False}
