"""Build one portable HTML readiness report from recorded M1/M3/M5 evidence."""
import html
import json
from pathlib import Path
from .m4_diagnostics import ROOT, sha, write


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def table(headers: list, rows: list, caption: str = '') -> str:
    return '<div class="table-wrap"><table>' + (f'<caption>{esc(caption)}</caption>' if caption else '') + '<thead><tr>' + ''.join(
        '<th scope="col">'+esc(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join(
        '<tr>'+''.join('<td>'+esc(c)+'</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'


CSS = """
:root{--ink:#152c35;--muted:#526872;--paper:#f5f7f6;--line:#d5dfdf;--teal:#14676c;--amber:#845116;--amber-bg:#fff1da}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}
header,main,footer{max-width:1152px;margin:auto;padding:32px}header{padding-top:58px;padding-bottom:20px}
.eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;font-weight:700;color:var(--teal)}h1{font-size:clamp(34px,5vw,58px);line-height:1.12;letter-spacing:-.04em;margin:12px 0 18px;max-width:900px}
h2{font-size:26px;letter-spacing:-.02em;line-height:1.25;margin:0 0 16px}h3{font-size:18px;margin:20px 0 10px}p{margin:10px 0 16px}a{color:var(--teal)}.lede{font-size:20px;max-width:880px;color:var(--muted)}
nav{display:flex;flex-wrap:wrap;gap:10px 22px;padding:16px 0;border-bottom:1px solid var(--line)}nav a{font-size:14px;text-decoration:none}section{background:white;border:1px solid var(--line);border-radius:14px;padding:28px;margin:0 0 24px;scroll-margin-top:20px}
.badge{display:inline-block;border-radius:6px;padding:3px 9px;font-size:12px;font-weight:750;letter-spacing:.04em;background:#e8f0f0;color:var(--teal)}.warn{background:var(--amber-bg);color:var(--amber)}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.card{padding:20px;background:var(--paper);border-radius:10px;min-width:0}.value{font-size:36px;font-weight:750;line-height:1.15;margin:8px 0}.small{font-size:13px;color:var(--muted)}.callout{border-left:4px solid var(--amber);padding:12px 18px;background:var(--amber-bg);border-radius:0 8px 8px 0}
.bars{margin:22px 0}.bar-row{display:grid;grid-template-columns:150px 1fr 100px;align-items:center;gap:14px;margin:14px 0}.track{height:18px;background:#e7eded;border-radius:3px;overflow:hidden}.fill{height:100%;background:var(--teal)}.intervention{background:#507f8c}
.interval{width:100%;height:auto;display:block}.table-wrap{overflow:auto;margin:16px 0}table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}th{color:var(--muted);font-size:12px;line-height:1.4}td,th{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}th:first-child,td:first-child{padding-left:0}caption{text-align:left;font-weight:650;padding:0 0 10px;font-size:14px}tbody tr:last-child td{border-bottom:0}
details{border-top:1px solid var(--line);padding-top:14px;margin-top:18px}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f3;border-radius:8px;padding:16px;font:12px/1.6 Consolas,monospace}code{font:13px/1.6 Consolas,monospace;overflow-wrap:anywhere}.fix{display:grid;grid-template-columns:42px 1fr;gap:16px;padding:22px 0;border-top:1px solid var(--line)}.rank{border:1px solid var(--line);border-radius:50%;height:38px;width:38px;display:grid;place-items:center;font-weight:750}.fix h3{margin:0 0 8px}.fix p:last-child{margin-bottom:0}li{margin:7px 0}footer{font-size:13px;color:var(--muted);padding-top:0}.hashes td:last-child{font:11px/1.5 Consolas,monospace;overflow-wrap:anywhere}
@media(max-width:760px){header,main,footer{padding:20px}header{padding-top:32px}section{padding:20px;border-radius:10px}.grid{grid-template-columns:1fr}.bar-row{grid-template-columns:95px 1fr 68px;font-size:12px;gap:8px}h2{font-size:23px}.lede{font-size:18px}td,th{padding:9px 10px}.fix{gap:10px}}
@media print{body{background:white;font-size:11px}header,main,footer{max-width:none;padding:12px}header{padding-top:12px}h1{font-size:32px}h2{font-size:20px}section{padding:16px;border-radius:0;break-inside:auto}.grid{grid-template-columns:repeat(3,1fr)}nav{display:none}.table-wrap{overflow:visible}table{font-size:10px}details{display:block}pre{font-size:9px}.value{font-size:25px}a{color:inherit}}
"""


def embed_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def render(d: dict, s: dict, p: dict, human: dict, agreement: dict, m1: dict, agents: str) -> str:
    a = s['analysis']
    primary, wall = a['primary_confirmation'], a['key_secondary_confirmation_wall']
    conf = a['confirmation']['arms']
    lo, hi = [v*100 for v in primary['selected_interval']]
    groups = d['groups']
    diagnostic_rows = [[g['population'].replace('_', ' '), g['arm'], g['attempts'],
                        f"{g['metadata_error_attempts']}/{g['attempts']}", g['metadata_error_commands'],
                        g['failed_public_commands'], g['original_failed_public_commands'], g['native_tool_calls']]
                       for g in groups]
    token_rows = [[g['population'].replace('_', ' '), g['arm'], f"{g['input_tokens']:,}",
                   f"{g['cached_input_tokens']:,}", f"{g['output_tokens']:,}", g['usage_missing']] for g in groups]
    failure_rows = [[r['task_id'], r['split'], ' / '.join(r['baseline']['outcomes']),
                    ' / '.join(r['intervention']['outcomes']),
                    'Both arms consistently fail; same two hidden failures in all four attempts.' if r['task_id'] == 'click-006' else
                    'Baseline consistently fails, but hidden failure sets differ (10 vs 1, no shared failing test); intervention mixed.' if r['task_id'] == 'click-010' else
                    'Mixed outcomes in both arms.'] for r in d['failure_consistency']]
    task_rows = [[r['task_id'], r['split'], f"{r['baseline']['successes']}/2", f"{r['intervention']['successes']}/2",
                 f"{r['success_delta']*100:+.1f}", f"{r['baseline']['mean_wall_seconds']:.3f}",
                 f"{r['intervention']['mean_wall_seconds']:.3f}", f"{r['wall_delta_seconds']:+.3f}"] for r in a['task_results']]
    read_rows = [[r['run_id'], r['task_id'], r['split'], ', '.join(f"{e['item_id']} · line {e['jsonl_line']}" for e in r['agents_read_evidence']),
                 r['trace_path']] for r in d['attempts'] if r['arm'] == 'intervention']
    metadata_rows = [[r['run_id'], r['arm'], r['split'],
                     ', '.join(f"{e['item_id']} · line {e['jsonl_line']}" for e in r['public_command_evidence'] if e['metadata_collection_error']),
                     r['trace_path']] for r in d['attempts'] if r['metadata_error_attempt']]
    correction_rows = [[r['run_id'], r['item_id'], r['exit_code'], ' / '.join(r['pytest_summary_lines']), r['reason']] for r in d['metric_corrections']]
    primary_rows, secondary_rows = [], []
    taxonomy = ('env_setup', 'missing_context', 'wrong_file_located', 'convention_violation', 'test_flakiness', 'reasoning_error', 'unclassified', 'no_failure')
    for category in taxonomy:
        primary_rows.append([category] + [g['primary'].get(category, 0) for g in d['human_label_breakdown']])
        if category not in ('unclassified', 'no_failure'):
            secondary_rows.append([category] + [g['secondary'].get(category, 0) for g in d['human_label_breakdown']])
    label_rows = [[r['trajectory'], r['task'], 'confirmation' if int(r['trajectory'].split('-')[1]) >= 5 else 'development calibration',
                   r['human_primary'], ', '.join(r['human_secondary']) or 'none', r['human_notes']] for r in human['labels']]
    hashes = {**d['sources'], **{k: p[k] for k in ('manifest_sha256', 'common_prompt_sha256', 'rubric_sha256', 'agent_image_id', 'proxy_image_id', 'evaluator_image_id')}}
    attempt_rows = [[r['run_id'], r['task_id'], r['arm'], r['repeat'], 'pass' if r['success'] else 'fail',
                    f"{r['agent_wall_seconds']:.3f}", r['metadata_error_commands'], r['trace_confirmed_failed_public_commands'],
                    r['native_tool_calls'], f"{r['usage']['input_tokens']:,}", f"{r['usage']['output_tokens']:,}"] for r in d['attempts']]
    metadata_snippet = esc('E   importlib.metadata.PackageNotFoundError: No package metadata was found for click\n!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!')
    trap_table = table(['Call inside runner.invoke(..., color=True)', 'Saved host-only microcheck output'], [
        ['prompt(style("Name", fg="green"))', r'Name: Bob\n'],
        ['prompt(style("Name", fg="green"), color=True)', r'\x1b[32mName\x1b[0m: Bob\n'],
        ['confirm(style("Hello World!", fg="green"))', r'Hello World! [y/N]: y\n'],
        ['confirm(style("Hello World!", fg="green"), color=True)', r'\x1b[32mHello World!\x1b[0m [y/N]: y\n']])
    trap_flow = esc('termui imported alias → original should_strip_ansi → color=None uses TTY detection\nCliRunner.isolation(color=True) → patches _compat + utils attributes only\ncaptured stdout is not a TTY → original alias strips ANSI')
    # No remote assets, fetches, or source content execution. The snapshot travels with the file.
    snapshot = {'diagnostics': d, 'M5': s, 'plan': p, 'human_labels': human, 'agreement': agreement,
                'M1_summary_sha256': sha(ROOT/'results/m1_summary.json')}
    embedded = embed_json(snapshot)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; script-src 'none'; connect-src 'none'; base-uri 'none'">
<title>Click · recorded agent readiness report</title><style>{CSS}</style></head><body>
<header><div class="eyebrow">Agent Readiness Probe · Click · M4 · 2 October 2026</div>
<h1>Setup guidance showed no observed confirmation lift.</h1>
<p class="lede">Success was 75% in both arms on eight confirmation tasks. The selected interval is wide and includes zero: this pilot is <strong>inconclusive</strong>, not evidence of equivalence or a general readiness threshold.</p>
<nav aria-label="Report sections"><a href="#primary">Primary result</a><a href="#mechanism">Mechanism diagnostics</a><a href="#failures">Repeat failures</a><a href="#labels">Human labels</a><a href="#trap">Verified trap</a><a href="#fixes">Ranked fixes</a><a href="#provenance">Provenance</a></nav></header>
<main>
<section id="primary"><span class="badge warn">PRIMARY · INCONCLUSIVE</span><h2 style="margin-top:12px">Measured effect of frozen setup-v1</h2>
<div class="grid"><div class="card"><div>Success delta</div><div class="value">{primary['estimate']*100:+.1f} pp</div><div class="small">Intervention minus baseline</div></div>
<div class="card"><div>Selected 95% interval</div><div class="value" style="font-size:27px">[{lo:+.2f}, {hi:+.2f}]</div><div class="small">Percentage points · Hoeffding fallback</div></div>
<div class="card"><div>Complete scored design</div><div class="value">48 / 48</div><div class="small">32 confirmation + 16 development attempts<br>Zero infrastructure exclusions</div></div></div>
<div class="bars"><div class="bar-row"><span>Baseline</span><div class="track"><div class="fill" style="width:75%"></div></div><strong>12/16 · 75%</strong></div>
<div class="bar-row"><span>Intervention</span><div class="track"><div class="fill intervention" style="width:75%"></div></div><strong>12/16 · 75%</strong></div></div>
<svg class="interval" viewBox="0 0 920 112" role="img" aria-label="Confirmation effect zero percentage points, selected interval minus 96.032 to plus 96.032 points">
<line x1="60" y1="42" x2="860" y2="42" stroke="#d5dfdf" stroke-width="2"/><line x1="460" y1="18" x2="460" y2="62" stroke="#526872" stroke-dasharray="4 4"/>
<line x1="{460+lo*4:.2f}" y1="42" x2="{460+hi*4:.2f}" y2="42" stroke="#845116" stroke-width="7"/><circle cx="460" cy="42" r="7" fill="#152c35"/>
<g font-family="system-ui,sans-serif" font-size="13" fill="#526872"><text x="60" y="84" text-anchor="middle">−100 pp</text><text x="460" y="84" text-anchor="middle">0</text><text x="860" y="84" text-anchor="middle">+100 pp</text></g></svg>
<p>The paired task-cluster bootstrap resampled all four outcomes per task together: {primary['resamples']:,} resamples, seed {primary['seed']}, eight clusters. Each task had identical arm mean success, so its interval was [0, 0] pp. The prespecified degenerate-case fallback is the conservative Hoeffding bound for task differences in [−1, 1], clipped to that range. The selected interval includes zero; no equivalence claim follows.</p>
<h3>Prespecified key secondary: agent wall time</h3>
<p>Baseline mean <strong>{conf['baseline']['mean_wall_seconds']:.3f}s</strong>; intervention <strong>{conf['intervention']['mean_wall_seconds']:.3f}s</strong>. Difference <strong>{wall['estimate']:+.3f}s</strong>, paired bootstrap 95% interval <strong>[{wall['bootstrap_95'][0]:+.3f}, {wall['bootstrap_95'][1]:+.3f}]s</strong>: also inconclusive. Wall time includes failed attempts and CLI metadata collection, excludes evaluator time; there were no agent caps. A faster failed attempt is not an efficient completion. No success-only conditioning was used.</p>
<div class="callout">This is conditional, test-verified performance on selected historical Click tasks using gpt-5.6-luna / low. There is no universal pass threshold or enterprise-readiness certification.</div>
<h3>All-task results are descriptive</h3><p>Across twelve tasks: baseline 18/24 (75%), intervention 19/24 (79.17%); delta +4.17 pp. Development alone: 6/8 versus 7/8. Only development task click-010 gained (+50 pp in its two-repeat task mean); zero tasks lost and eleven were unchanged. All eight confirmation task means were unchanged. These development-inclusive numbers do not replace the primary result.</p>
<details><summary>All twelve task means and wall times</summary>{table(['Task','Split','Baseline pass','Intervention pass','Delta pp','Baseline s','Intervention s','Delta s'],task_rows)}</details></section>

<section id="mechanism"><span class="badge">DESCRIPTIVE · NO NEW HYPOTHESIS TESTS</span><h2 style="margin-top:12px">Exposure did not prevent the first collection errors</h2>
{table(['Population','Arm','Attempts','Metadata-error attempts','Metadata-error commands','Failed public pytest commands','Original failure counter','Tool calls'],diagnostic_rows)}
<p>Collection errors affected <strong>2/16 attempts in each arm</strong> on confirmation tasks and <strong>6/24 in each arm</strong> across all tasks. The affected tasks were click-001 in confirmation, plus click-002 and click-003 in development, both repeats in both arms. Baseline click-002 repeat 1 had two such commands. This supports no observed reduction in attempt-level metadata-error incidence.</p>
<p>All <strong>24/24 intervention attempts</strong> exposed the complete frozen AGENTS.md in successful command output (16/16 confirmation). In all six intervention attempts with metadata errors, the failing command preceded the <code>pip install --target /tmp/click-site</code> command; its PYTHONPATH included only <code>/workspace/src</code>. The install recipe was executed later. A visible read establishes exposure, not comprehension or adherence before the first test. Baseline workspaces had no delivered AGENTS overlay.</p>
<h3>Token diagnostics: recorded totals per arm</h3>{table(['Population','Arm','Input tokens','Cached input subset','Output tokens','Usage missing'],token_rows)}
<p class="small">Native tool calls count completed CLI command, file-change, MCP and web-search items, rather than individual subprocesses. Cached input is already included in input. Token totals accumulate repeated context across turns; they are not unique text volume. No usage is missing. Token/tool differences are descriptive, not additional efficacy tests.</p>
<h3>Two original failure flags were Git failures after passing pytest</h3>
<p>The frozen M5 counter used shell exit status as one failure signal. In click-008 intervention repeats 1 and 2, pytest passed before Git returned a nonzero code. Trace-confirmed failed public pytest commands are therefore <strong>4 vs 5</strong> on confirmation and <strong>9 vs 9</strong> across all tasks. Original saved counts remain <strong>4 vs 7</strong> and <strong>9 vs 11</strong>. Frozen data and the primary analysis were not rewritten.</p>
{table(['Run','Event','Shell exit','Visible pytest result','Audit explanation'],correction_rows)}
<p class="small">Unit: a completed public-pytest shell command with an emitted failed/error terminal summary or collection error. A command can contain multiple invocations; none here had multiple visible terminal summaries. Expected xfails are not failures. Actual failed summaries count even if a later command masks the exit code. These counters do not represent all possible bespoke diagnostic scripts.</p>
<details><summary>Exact metadata-error trace references (12 attempts, 13 commands)</summary>{table(['Run','Arm','Split','Completed event · JSONL line','Trace path'],metadata_rows)}<pre>{metadata_snippet}</pre></details>
<details><summary>Full-text AGENTS read evidence for all 24 intervention attempts</summary>{table(['Run','Task','Split','Completed event · JSONL line','Trace path'],read_rows)}<p class="small">Every event above has exit code zero and contains the full text whose hash is recorded in provenance.</p></details>
</section>

<section id="failures"><span class="badge">DESCRIPTIVE · REPEAT CONSISTENCY</span><h2 style="margin-top:12px">Four tasks had at least one failed attempt</h2>
{table(['Task','Split','Baseline R1 / R2','Intervention R1 / R2','Consistency'],failure_rows)}
<p>Confirmation: each arm had four failed attempts across click-006, click-007 and click-008. Across all tasks: baseline six failures, intervention five; both arms also failed click-010. All other eight tasks passed both repeats in both arms. Repeat numbers are nominal labels, not chronological launch order.</p>
<p>Click-006 repeatedly failed the same two hidden tests in all four attempts. Consistent failure outcomes do not always imply the same failure: baseline click-010 failed ten hidden tests in repeat 1 and one different test in repeat 2. No M5 failure label is inferred from these outcomes.</p>
<details><summary>All 48 attempt-level diagnostics</summary>{table(['Run','Task','Arm','Repeat','Outcome','Agent s','Metadata commands','Failed pytest commands','Tools','Input tokens','Output tokens'],attempt_rows)}</details></section>

<section id="labels"><span class="badge">HUMAN REVIEW · M3 ONLY</span><h2 style="margin-top:12px">Reviewed failures were labeled reasoning errors</h2>
<p>Swaroop labeled twelve M3 trajectories: four development calibration traces and eight confirmation baseline repeat-1 traces. Confirmation contained six successes and two failures; both failures were <strong>reasoning_error</strong>. Across the twelve reviewed traces, all three failures had that primary label. Primary labels partition this reviewed sample; secondary labels can overlap. These labels are not extrapolated to the other M5 trajectories.</p>
{table(['Human primary','Confirmation M3 (8)','All reviewed M3 (12)'],primary_rows)}
{table(['Human secondary (overlapping)','Confirmation M3 (8)','All reviewed M3 (12)'],secondary_rows)}
<p class="small">Zero human unclassified labels are explicit. Absence of a class in this small sample does not validate the classifier for that class. A successful final outcome can have a secondary label for an intermediate error.</p>
<h3>Held-out rule versus human agreement</h3>
<p>Primary exact agreement: <strong>{agreement['held_out_confirmation']['primary_exact_matches']}/8 (75%)</strong>; Cohen’s κ <strong>{agreement['held_out_confirmation']['primary_kappa']:.6f}</strong>. Secondary set agreement: <strong>7/8 (87.5%)</strong>. The rule abstained as <code>unclassified</code> on both confirmation failures, so failure coverage was <strong>0/2</strong>. Its 6/6 agreement on covered rows concerns successes only. Development calibration was 4/4 agreement and is not held-out validation.</p>
<p>One reviewer saw rule predictions and outcomes; the detailed failures also included hidden failure evidence not available to the rule. Potential anchoring and unequal evidence access limit interpretation. Inter-human agreement is not measured.</p>
<details><summary>All supplied labels and unchanged notes</summary>{table(['Trajectory','Task','Scope','Primary','Secondary','Swaroop’s note'],label_rows)}</details></section>

<section id="trap"><span class="badge">VERIFIED SOURCE MECHANISM · NOT A TESTED DOCUMENTATION FIX</span><h2 style="margin-top:12px">CliRunner patches attributes, not a retained import</h2>
<p>Swaroop’s click-006 hypothesis was confirmed for runner-level color. In the submitted source, <code>termui</code> directly imported <code>should_strip_ansi</code>. <code>CliRunner.isolation</code> rebound <code>_compat.should_strip_ansi</code> and <code>utils.should_strip_ansi</code>, but did not rebind that retained <code>termui</code> alias.</p>
<pre>{trap_flow}</pre>
<p>With <code>runner.invoke(..., color=True)</code> and the new prompt/confirm parameter left at <code>None</code>, the retained original function stripped ANSI. Explicit <code>prompt(..., color=True)</code> or <code>confirm(..., color=True)</code> preserved it.</p>
{trap_table}
<p class="small">Verified in the saved M3 click-006 submission: testing.py lines 504–523, _compat.py lines 498–509, globals.py lines 54–67, and the direct termui import/helper. The recorded host-only inspection checked function identities and public API behavior with bytecode writes disabled. It was not an agent-authored test, new scored attempt, or hidden/gold-based intervention. Source and microcheck details are preserved in docs/m3_human_review.md.</p>
<p>The other reviewed confirmation failure, click-008, only fixed <code>MaybeStripAnsi</code> streams. Its diagnostics did not exercise the stated TTY plus nonexistent PAGER path and were not rerun after the final patch. Both reviewed failures stopped after existing tests passed without checking every stated requirement. That is an observed pattern in two traces, not proof that extra guidance would rescue them.</p></section>

<section id="fixes"><h2>Ranked future-work priorities</h2><p>Ranking is a provisional judgment about observed coverage and implementation effort, not an estimated lift ranking. Only setup-v1 was tested. The two new candidates derive from exposed confirmation review and need fresh held-out tasks. Their opportunity shares overlap and are not additive; neither is a rescue probability.</p>
<div class="fix"><div class="rank">1</div><div><h3>Explicit requirement coverage and checks after the final patch</h3><span class="badge warn">UNTESTED · EFFECT NOT MEASURED</span><p>Require a check for each stated branch and rerun relevant checks after the final edit. Observed opportunity: 2/2 human-reviewed confirmation failures (M3-08 and M3-10), not the entire M5 failure population. Provisional first priority because it addresses both reviewed patterns. Drafting effort appears low; actual effort, added wall time, token cost and success lift are <strong>not measured</strong>.</p></div></div>
<div class="fix"><div class="rank">2</div><div><h3>Document the should_strip_ansi patching convention</h3><span class="badge warn">UNTESTED · EFFECT NOT MEASURED</span><p>Explain the existing isolation patch points and how a retained direct import can bypass them. Observed opportunity: M3-08, 1/2 reviewed confirmation failures, overlapping priority 1. The source mechanism is verified; the effect of documentation on agent behavior is <strong>not measured</strong>. Provisional narrower priority. Drafting effort appears low; runtime cost and lift remain unknown.</p></div></div>
<div class="fix"><div class="rank">3</div><div><h3>Frozen setup-v1 AGENTS.md: retain as the measured reference</h3><span class="badge">TESTED · INCONCLUSIVE</span><p>Measured confirmation effect <strong>0.00 pp</strong>, selected 95% interval <strong>[{lo:+.2f}, {hi:+.2f}] pp</strong>. Agent wall-time delta <strong>{wall['estimate']:+.3f}s</strong>, interval <strong>[{wall['bootstrap_95'][0]:+.3f}, {wall['bootstrap_95'][1]:+.3f}]s</strong>. Metadata-error incidence was unchanged despite 24/24 full-text reads. No demonstrated success lift or first-error avoidance; the wide interval does not establish ineffectiveness. No further roll-out priority is supported by this pilot alone. Incremental paid API spend was $0; subscription dollar cost is not measured.</p></div></div>
<div class="callout">No candidate has been added to the frozen treatment or executed here. The next research decision requires review; this report introduces no new scored attempt or hypothesis test.</div></section>

<section id="provenance"><h2>What this evidence covers</h2>
<p>{m1['human_accepted_count']} human-accepted historical Click tasks, split four development / eight confirmation. M1 audited {m1['population_count']} public commits, found {m1['structurally_eligible_count']} structurally eligible candidates, and preserved {m1['execution_count']} accepted-task base/buggy/gold validation executions. Two attempts per arm per task form the 48-outcome experiment. Eight M3 baseline repeat-1 outcomes were retained without reruns; forty remaining attempts were randomized within task blocks using seed <strong>{p['seed']}</strong>.</p>
<p><strong>Arm-order limitation:</strong> {esc(p['arm_order_limitation'])} Eight confirmation clusters yield limited uncertainty resolution. Selection was purposive; task statements were made precise during validity review, and training exposure is unknown. Development exposure guided setup-v1 selection. Analysis code was committed before new M5 runs but after M3 outcomes were known, implementing the earlier documented formulas. Results do not establish performance on unseen enterprise work or other agents.</p>
<p><strong>Frozen execution:</strong> Codex CLI {esc(p['cli_version'])}, {esc(p['model'])} / {esc(p['reasoning_effort'])}; same offline fresh evaluator image and injected hidden tests. Agent workspaces held only buggy source, TASK.md and intervention-only AGENTS.md; no hidden tests, gold patches, private artifacts, history or Docker socket. The internal network’s allowlisted proxy was the only exit, and Codex web search was disabled. Read-only login credentials were visible in the ephemeral agent container, an accepted limitation. Containers were deleted after attempts.</p>
<p><strong>Delivery:</strong> frozen AGENTS.md at <code>/workspace/AGENTS.md</code> in the intervention arm only. Both arms used the same prompt sentence: <q>If /workspace/AGENTS.md exists, read it before starting the task.</q> All frozen hashes and human labels remain unchanged.</p>
<p><strong>Resources:</strong> no infrastructure exclusions, usage-limit stops or Docker timeouts in M5; no agent wall caps. Lifetime CLI invocations remain {s['accounting']['total_cli_invocations_observed']}. M4 made zero agent, evaluator or judge calls. Incremental paid API spend remains $0; no paid fallback or capacity purchase. Historical M2 smokes and pre-experiment development calibration are excluded from experimental denominators. Saved-evidence audit found no owned containers/networks or saved auth bytes.</p>
<details><summary>Frozen AGENTS.md text</summary><pre>{esc(agents)}</pre></details>
<details class="hashes"><summary>Source digests and image identities</summary>{table(['Source / identity','SHA256 / image ID'],list(hashes.items()))}</details>
<details><summary>Reproduce this report from saved data</summary><pre>python -B -m arp.m4_report</pre><p>This reads saved JSON, completed trace events and recorded source-review notes only; it launches no model, network or Docker operation. The report carries an embedded JSON snapshot and needs no external assets. Detailed evidence is also in results/m4_diagnostics.json and review/m4_attempt_diagnostics.csv. Absolute local trace paths can be resolved relative to C:\\arp. All aggregates shown above are bundled in this file.</p></details>
</section></main><footer>Prepared from recorded evidence only. M4 is ready for review. No later experiment, intervention change, report publication or outreach is authorized by this artifact.</footer>
<script type="application/json" id="recorded-data">{embedded}</script></body></html>'''


def main() -> None:
    d = write()
    s = json.loads((ROOT/'results/m5_summary.json').read_text())
    p = json.loads((ROOT/'results/m5_plan.json').read_text())
    h = json.loads((ROOT/'review/m3_human_labels.json').read_text())
    agreement = json.loads((ROOT/'results/m3_agreement.json').read_text())
    m1 = json.loads((ROOT/'results/m1_summary.json').read_text())
    agents = (ROOT/p['intervention_path']).read_text(encoding='utf-8')
    reports = ROOT/'reports'
    reports.mkdir(exist_ok=True)
    path = reports/'click_readiness.html'
    path.write_text(render(d, s, p, h, agreement, m1, agents), encoding='utf-8', newline='\n')
    print(json.dumps({'report': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size, 'attempts': len(d['attempts'])}))


if __name__ == '__main__':
    main()
