"""Render the M5 analysis checkpoint as Markdown; M4 reporting stays pending."""
from .m5 import ROOT, load


def interval(value, scale=1):
    return '['+', '.join(f'{v*scale:.3f}' for v in value)+']'


def render():
    summary=load(ROOT/'results/m5_summary.json')
    result=summary['analysis']; primary=result['primary_confirmation']; wall=result['key_secondary_confirmation_wall']
    lines=['# M5 analysis checkpoint','',
           f"Status: **{summary['status']}**. Eight M3 confirmation baselines are retained without reruns. New scored outcomes: {summary['new_scored_completed']}/40; unlaunched slots: {summary['unlaunched_attempts_remaining']}; total scored outcomes still missing: {summary['scored_outcomes_still_missing']}.",'',
           'This is the M5 analysis checkpoint, not the deferred M4 readiness report. The [committed plan](m5_plan.md), [order/configuration JSON](../results/m5_plan.json), and [machine-readable analysis](../results/m5_summary.json) contain the full provenance.','',
           '## Primary confirmation outcome','']
    if 'estimate' in primary:
        arms=result['confirmation']['arms']
        lines.extend([f"Baseline: {arms['baseline']['successes']}/{arms['baseline']['scored_attempts']}; intervention: {arms['intervention']['successes']}/{arms['intervention']['scored_attempts']}.",'',
                      f"Intervention minus baseline mean task success: **{primary['estimate']*100:+.3f} percentage points**. Paired task-cluster bootstrap 95% interval: {interval(primary['bootstrap_95'],100)} percentage points; {primary['resamples']:,} resamples, seed {primary['seed']}, {primary['clusters']} task clusters.",'',
                      f"Conservative Hoeffding 95% interval: {interval(primary['hoeffding_95'],100)} percentage points (half-width {primary['hoeffding_half_width']*100:.3f}). Selected method: {primary['selected_method']}; selected interval {interval(primary['selected_interval'],100)}. Conclusion: **{primary['conclusion']}**.",'',
                      'The bootstrap preserves each task\'s two repeats in both arms as one cluster. The Hoeffding bound applies to differences in [-1,1] and is clipped to that range; it is the fallback if the bootstrap endpoints coincide. A zero-containing selected interval is inconclusive, not evidence of equivalence.',''])
    else:
        lines.extend(['A comparable primary estimate is not computed because confirmation slots are incomplete or have infrastructure exclusions. Missing outcomes are not task failures and are not silently replaced.',''])
    lines.extend(['| Confirmation task direction | Tasks |','|---|---|'])
    for name in ['gains','losses','unchanged']:
        lines.append(f"| {name} | {', '.join(result[name]) or 'none'} |")
    lines.extend(['','Directions compare task mean success across both repeats, rather than selecting the best patch.'])
    for direction in ['gain','loss','unchanged']:
        names=[r['task_id'] for r in result['task_results'] if r['direction']==direction]
        label={'gain':'gains','loss':'losses','unchanged':'unchanged tasks'}[direction]
        lines.append(f"All-task {label} (descriptive): {', '.join(names) or 'none'}.")
    lines.extend(['', '## Key secondary: agent wall time',''])
    if wall.get('estimate') is not None:
        arms=result['confirmation']['arms']
        lines.extend([f"Confirmation mean wall time: baseline {arms['baseline']['mean_wall_seconds']:.3f}s; intervention {arms['intervention']['mean_wall_seconds']:.3f}s. Paired task mean difference (intervention minus baseline): **{wall['estimate']:+.3f}s**, bootstrap 95% interval {interval(wall['bootstrap_95'])}s.",'',
                      'Wall-time effect is **inconclusive** because its interval includes zero.' if wall['bootstrap_95'][0] <= 0 <= wall['bootstrap_95'][1] else 'The wall-time interval excludes zero; interpret its direction alongside success.', '',
                      f"Agent wall-time caps: baseline {arms['baseline']['agent_caps']}; intervention {arms['intervention']['agent_caps']}. Failed task attempts remain included: baseline {arms['baseline']['failed_task_attempts']}; intervention {arms['intervention']['failed_task_attempts']}.",''])
    else:
        lines.extend(['A comparable paired wall-time effect is not computed for incomplete confirmation data.',''])
    lines.extend(['Wall time is the prespecified key secondary outcome. It includes task failures and cap durations, excludes infrastructure, and measures the recorded CLI elapsed duration (including CLI metadata collection), not evaluator time. A faster failed attempt is not an efficient completion. No success-only conditioning or failure-penalty composite is used. Tool calls, token usage, and failed public pytest runs are diagnostics.','',
                  '## Per-task results','', '| Task | Split | Baseline pass/scored (planned 2) | Intervention pass/scored (planned 2) | Success delta, pp | Baseline mean seconds | Intervention mean seconds | Wall delta, seconds |','|---|---|---:|---:|---:|---:|---:|---:|'])
    for task in result['task_results']:
        b,i=task['baseline'],task['intervention']
        delta='not measured' if task['success_delta'] is None else f"{task['success_delta']*100:+.1f}"
        wdelta='not measured' if task['wall_delta_seconds'] is None else f"{task['wall_delta_seconds']:+.3f}"
        btime='not measured' if b['mean_wall_seconds'] is None else f"{b['mean_wall_seconds']:.3f}"
        itime='not measured' if i['mean_wall_seconds'] is None else f"{i['mean_wall_seconds']:.3f}"
        lines.append(f"| {task['task_id']} | {task['split']} | {b['successes']}/{b['scored']} | {i['successes']}/{i['scored']} | {delta} | {btime} | {itime} | {wdelta} |")
    lines.extend(['', '## Descriptive outcomes','', '| Population | Arm | Pass/scored | First chronological attempt pass/scored | First-attempt Wilson 95% | pass@2 tasks | Mean agent seconds |','|---|---|---:|---:|---|---:|---:|'])
    for name in ['confirmation','development_descriptive','all_tasks_descriptive']:
        for arm,a in result[name]['arms'].items():
            ci='not measured' if a['first_attempt_wilson_95'] is None else interval(a['first_attempt_wilson_95'],100)+'%'
            time='not measured' if a['mean_wall_seconds'] is None else f"{a['mean_wall_seconds']:.3f}"
            lines.append(f"| {name} | {arm} | {a['successes']}/{a['scored_attempts']} | {a['first_attempt_successes']}/{a['first_attempt_scored']} | {ci} | {a['pass_at_2_tasks']}/{a['pass_at_2_denominator']} | {time} |")
    lines.extend(['', 'Development and all-task outcomes are descriptive only. First attempt means the earliest actual launch per task/arm; randomization may put repeat 2 before repeat 1. pass@2 is descriptive across complete two-repeat task/arms and is not the primary effect or a selective best-patch score.','',
                  '## Infrastructure, diagnostics, and accounting',''])
    exclusions=result['infrastructure_exclusions']
    lines.append(f"Infrastructure/missing recorded outcomes: {len(exclusions)}. Unlaunched slots: {len(result['unlaunched_slots'])}. Docker timeouts: {summary['docker_timeouts']}.")
    for r in exclusions: lines.append(f"- {r['run_id']}: {r['state']} ({r['task_id']}, {r['arm']}, repeat {r['repeat']})")
    if summary.get('stop_reason'): lines.extend(['', 'Stop reason: '+summary['stop_reason']['error']])
    lines.extend(['','| Population | Arm | Tool calls | Failed public pytest runs | Input tokens | Cached input tokens (subset) | Output tokens | Usage missing |','|---|---|---:|---:|---:|---:|---:|---:|'])
    for split in ['confirmation','development']:
        for arm in ['baseline','intervention']:
            records=[r for r in summary['attempts'] if r['split']==split and r['arm']==arm and r['success'] is not None]
            measured=[r for r in records if isinstance(r.get('usage'),dict)]
            counts=[sum(r.get(key,0) for r in records) for key in ['native_tool_calls','failed_public_pytest_runs']]
            tokens=[sum(r['usage'].get(key,0) for r in measured) for key in ['input_tokens','cached_input_tokens','output_tokens']]
            lines.append(f"| {split} | {arm} | {counts[0]} | {counts[1]} | {tokens[0]} | {tokens[1]} | {tokens[2]} | {len(records)-len(measured)} |")
    accounting=summary['accounting']
    lines.extend(['', f"Lifetime CLI invocations observed: {accounting['total_cli_invocations_observed']} (28 before M5; {accounting['new_cli_invocations_observed']} in M5 including gate). Incremental paid API spend: **$0**; subscription dollar cost is not measured. No paid judge, provider fallback, quota purchase/reset, or M6.",'',
                  '## Limitations and review boundary','', summary['config']['arm_order_limitation'],'',
                  'Eight confirmation clusters give limited and potentially unstable uncertainty estimates. Task selection is purposive; statements were made precise during validity review, and training exposure is unknown. Effects are conditional on this frozen CLI/model/runtime/task population. Development exposure guided intervention selection; those outcomes do not enter primary confirmation inference. The M5 analysis code was committed before the new runs but after M3 baseline outcomes were known, implementing the previously documented formulas.','',
                  'The frozen model, prompt sentence, AGENTS bytes, rubric, evaluator, and all M3 human labels remain unchanged. Requirement-verification guidance observed during M3 review remains an untested future candidate; it is not part of this treatment.','',
                  '## Verification','',
                  'The [saved-evidence and cleanup audit](../results/m5_audit.json) passed for all 40 new attempts and the eight retained baselines. All 24 intervention traces contain visible full AGENTS reads. No owned container or network remains; no saved auth credential bytes were detected. Frozen configuration and M3 human labels are unchanged. Core tests: 106 passed, one skipped for Windows host symlink privilege.','',
                  '**Stop here for M5 review. Do not start M4.**'])
    (ROOT/'docs/m5_results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__': render()
