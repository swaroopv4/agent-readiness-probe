# M4 readiness report checkpoint

October 2, 2026. **M4_complete_pending_review**. The [single-file Click readiness report](../reports/click_readiness.html) contains inline styling, a conditional success visualization, and an embedded recorded-data snapshot. It works offline without sidecars or remote assets. All metrics use saved evidence; this milestone made no agent, evaluator, judge, or Docker calls. No new hypothesis tests were introduced.

The primary confirmation result remains baseline 12/16 versus intervention 12/16, success delta **0 pp**. The degenerate paired task-cluster bootstrap interval [0, 0] triggers the prespecified Hoeffding fallback: **95% [-96.032, +96.032] pp**, inconclusive. Key secondary wall-time delta is **+2.662s**, paired bootstrap **95% [-3.121, +10.538]s**, also inconclusive. All-task results (18/24 versus 19/24) remain descriptive. No frozen source, outcome, analysis, intervention, rubric, or human label was modified.

## Descriptive mechanism diagnostics

Only the 48 experimental slots are included, with the eight retained M3 baselines. Earlier smokes and pre-experiment development calibration are excluded. “All tasks” includes the confirmation rows; these populations must not be added together.

| Population | Arm | Metadata-error attempts | Metadata-error commands | Trace-confirmed failed public pytest commands | Original saved failure counter | Tool calls | Input tokens | Cached input subset | Output tokens |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Confirmation | Baseline | 2/16 | 2 | 4 | 4 | 115 | 1,966,145 | 1,543,680 | 33,665 |
| Confirmation | Intervention | 2/16 | 2 | 5 | 7 | 118 | 1,952,209 | 1,584,896 | 32,362 |
| All tasks | Baseline | 6/24 | 7 | 9 | 9 | 196 | 3,609,382 | 2,921,984 | 53,446 |
| All tasks | Intervention | 6/24 | 6 | 9 | 11 | 196 | 3,459,284 | 2,849,024 | 50,788 |

Metadata collection errors require an emitted Click `PackageNotFoundError` traceback plus a collection interruption, rather than a source-text mention. Both repeats of click-001 had them in both arms; all-task counts additionally include both repeats of development click-002 and click-003. Baseline click-002 repeat 1 emitted the error twice.

All **24/24** intervention attempts visibly read the complete frozen AGENTS.md (16/16 confirmation). Exact completed event IDs, JSONL line numbers, paths and digests are preserved in the report and [diagnostic JSON](../results/m4_diagnostics.json). Reading is exposure evidence, not proof of comprehension or adherence. All six intervention attempts with metadata errors ran the failing command before the install recipe; those commands used only `/workspace/src` in PYTHONPATH. They executed the recipe later. The unchanged error incidence gives no observed first-error avoidance.

The frozen public-test counter flags a nonzero shell exit even when pytest passed and a later command failed. In intervention click-008 repeat 1, event `item_10` shows `257 passed, 24 skipped in 0.39s` before Git exits 129. Repeat 2, event `item_8`, shows `1654 passed, 24 skipped, 31000 deselected, 1 xfailed in 3.50s` before Git exits 128. The new descriptive audit distinguishes these two flags; the original counters are retained, not rewritten. Unit: completed public-pytest command executions with actual emitted test failure/error summaries or collection errors. Commands can contain multiple pytest invocations, but none here had multiple visible terminal summaries. Expected xfails are not failures; failed summaries still count when a later command masks the shell exit.

Input tokens include cached input, so the cached column must not be added again. All 48 attempts have usage. Native tool calls count completed CLI tool items, not individual subprocesses. These sums are diagnostic, not efficacy tests or dollar cost estimates.

## Failures across nominal repeats

| Task | Split | Baseline R1 / R2 | Intervention R1 / R2 | Consistency |
|---|---|---|---|---|
| click-006 | Confirmation | fail / fail | fail / fail | Same two hidden failures in all four attempts |
| click-007 | Confirmation | pass / fail | fail / pass | Mixed in both arms |
| click-008 | Confirmation | fail / pass | fail / pass | Mixed in both arms |
| click-010 | Development | fail / fail | fail / pass | Baseline outcome consistent, hidden failure sets different (10 vs 1, no common failing test); intervention mixed |

All other eight tasks passed both repeats in both arms. Confirmation has four failed attempts in each arm across three tasks; all-task counts are six baseline and five intervention failures across four tasks. Nominal repeat order differs from launch order under randomization. No new failure labels are inferred for M5.

## Human evidence and fix priorities

Human labels remain exactly Swaroop's twelve M3 labels. The eight confirmation baseline repeat-1 traces have six `no_failure` and two `reasoning_error` primary labels; all twelve reviewed traces have nine and three, respectively, with zero human `unclassified`. Secondary labels overlap: confirmation has `env_setup` 1, `reasoning_error` 3, `missing_context` 1; all reviewed M3 has 3, 5, 1. These are not all-experiment failure proportions.

Held-out rule primary agreement remains 6/8 (75%), kappa 0.428571; secondary-set agreement 7/8 (87.5%). The rule abstained on both held-out failures, so failure coverage is 0/2. Absent taxonomy classes and inter-human agreement are not measured. The unblinded reviewer saw more evidence on the detailed failures than the rule.

The report includes the [already verified CliRunner trap](m3_human_review.md): isolation patches `_compat` and `utils` attributes but does not update a directly imported `termui` reference. The saved patch strips ANSI when color is enabled at the runner and the prompt/confirm argument stays `None`; explicit function-level `color=True` retains ANSI. This verified source behavior does not establish that documenting the convention improves agents.

The report ranks three evidence-supported priorities, explicitly as provisional work priorities rather than predicted effect sizes:

1. **Untested requirement-verification guidance**: observed opportunity in both human-reviewed confirmation failures (2/2), unknown rescue rate, cost and lift.
2. **Untested should_strip_ansi convention documentation**: observed opportunity in M3-08 (1/2), overlapping the first candidate; effect not measured.
3. **Tested setup-v1 reference**: measured primary delta 0 pp with the wide selected interval above; wall-time delta +2.662s with its interval. No demonstrated lift or first-error avoidance, no equivalence conclusion.

The two untested candidates derive from exposed confirmation review and require fresh held-out tasks for any future experiment. No intervention is changed or frozen here.

## Verification and reproduction

```powershell
python -B -m arp.m4_report
```

This regenerates the diagnostic JSON, [48-row CSV](../review/m4_attempt_diagnostics.csv), and standalone HTML from saved evidence only. Core tests: **111 passed, one skipped** for Windows host symlink privilege. Five new tests check real pytest evidence versus misleading source text, masked exit codes, expected xfails, pytest pass followed by Git failure, and escaping of supplied notes. The existing full saved-evidence audit passes: all 40 new attempts and eight retained baselines, same offline evaluator, frozen artifacts unchanged. The [M4 artifact audit](../results/m4_audit.json) also checks deterministic regeneration, embedded source equality, trace references and CSV totals. Browser QA loads the report directly by file URL, verifies embedded 48-attempt data, and checks desktop, tablet and mobile widths with all details expanded; no outer-page overflow, external requests or page errors. Desktop/mobile, diagnostic and fix-list screenshots were visually inspected. A print rendering was also produced as local QA. Private QA evidence is in `artifacts/private/m4-*`.

Lifetime CLI invocations remain 69; incremental paid API spend remains $0; subscription dollar cost is not measured. **Stop for M4 review.** No M6, new experiment, publication or outreach is started.
