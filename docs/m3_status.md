# M3 status: completed under the approved reduced scope

October 2, 2026, America/Los_Angeles. The approved freeze was committed as 19b880e before any confirmation execution. All eight gpt-5.6-luna / low baseline confirmation attempts completed: six passed the unchanged offline evaluator and two failed. There were no retries, Docker timeouts, or usage-limit stops. These are M5 baseline repeat 1 and must not be rerun.

The [HTML labeling sheet](../review/m3_labeling_sheet.html) and [CSV sheet](../review/m3_labeling_sheet.csv) contain twelve completed human reviews supplied by Swaroop: four development calibration and eight held-out confirmation rows. The [supplied-label record](../review/m3_human_labels.json) preserves labels and notes separately from the unchanged rule predictions. See [human review and agreement](m3_human_review.md) and [agreement JSON](../results/m3_agreement.json). The click-006 color-patching hypothesis was confirmed without changing the human label. The observed requirement-verification pattern is recorded solely as an untested future candidate; frozen AGENTS.md is unchanged. Stop before M4.

## Frozen artifacts

- AGENTS.md SHA256: ae59af6e5b2ef1b510958ef4159c0e0c05d9cbc0d313db7617fb6781dbc43c89. Exact approved text remains at interventions/drafts/setup-v1/AGENTS.md, frozen in place.
- The common prompt and development-calibrated rubric were committed before the first confirmation run. Their digests and source digests are in [m3_freeze.json](../results/m3_freeze.json).
- Baseline inputs contained no AGENTS overlay, hidden tests, gold patches, private artifacts, or history. Both prospective arms use the same frozen prompt sentence. M3 ran only baseline.
- The rule labeler was not changed after confirmation exposure. Two failed confirmation attempts have unclassified primary labels because the frozen rules found insufficient public evidence for a narrower terminal class. Human review may supply evidence-backed labels without revising the intervention or frozen rules.

## Baseline repeat 1 outcomes

| Task | Outcome | Agent seconds | Native calls | Failed public pytest runs | Rule primary | Rule secondary |
|---|---|---:|---:|---:|---|---|
| click-001 | pass | 66.656 | 8 | 2 | no_failure | env_setup, reasoning_error |
| click-004 | pass | 48.891 | 5 | 0 | no_failure | none |
| click-005 | pass | 56.079 | 7 | 0 | no_failure | reasoning_error |
| click-006 | fail | 50.187 | 7 | 0 | unclassified | none |
| click-007 | pass | 67.875 | 10 | 0 | no_failure | reasoning_error |
| click-008 | fail | 77.343 | 8 | 0 | unclassified | none |
| click-011 | pass | 67.359 | 8 | 0 | no_failure | none |
| click-012 | pass | 47.844 | 7 | 0 | no_failure | none |

This is a baseline batch, not an intervention-effect estimate. Success is primary, recorded agent wall time is the prespecified key secondary outcome, and tool calls/tokens/failed public test runs are diagnostic. Expected xfails and intentional pre-fix reproductions are not automatically terminal task failures. Primary rule labels describe terminal outcomes; intermediate obstacles are secondary diagnostics. Rule predictions are shown as requested, so human review is unblinded and may be anchored. No independent blinded or inter-human validation claim is made.

## Review and later execution boundary

Human labels supplied: twelve, reviewer Swaroop. Held-out primary exact agreement is 6/8 (75%), primary kappa 0.428571, secondary set agreement 7/8 (87.5%), and joint agreement 6/8 (75%). The rule abstained on both failures: coverage is 6/8 overall and 0/2 on failed outcomes. `reasoning_error` primary recall is 0/2; precision is undefined with zero predictions. Other absent classes are not measured. Development agreement is separately 4/4 for primary and secondary, with kappa 1; these are calibration examples. The approved 12-label scope replaces the original 20-label requirement. The eight-row unblinded, single-reviewer evaluation supports only limited pilot conclusions.

All eight M3 baselines precede intervention runs, so arm order is not fully randomized and time/cohort confounding remains. The frozen M5 remaining order interleaves baseline repeat 2 with intervention repeats 1 and 2 using seed 20261002 (24 attempts). No M5 attempt has started. These repeat-1 baselines must be retained in M5, including the two failures.

Operational CLI invocations: 28 total (19 before M3, one M3 gate, eight baseline attempts). Paid API spend is $0; subscription dollar cost is not measured. The original approximate 50 ceiling has 22 slots remaining. The later 24 M5 attempts plus another gate project to 53 total; resolve the ceiling at the M5 checkpoint before launch. No paid judge, provider fallback, M4, M5, M6, or outreach was run here.

## Verification and reproduction

The evidence audit passed for all eight attempts: exact accepted task input bytes and common prompt, read-only auth/input mounts, history-free agent workspaces, model/reasoning pins, disabled web search, event/patch hashes, production-only submissions, parsed evaluator JUnit, and unchanged offline evaluator files. Cleanup found no owned agent/proxy/evaluator containers or agent networks. The saved evidence and review files contain no auth credential bytes. The read-only audit is arp/check_m3.py; source hashes and sanitized attempt data are in [m3_summary.json](../results/m3_summary.json).

The initial HTML preparation passed Node syntax and CSV round-trip checks with blank labels. The completed sheet now embeds Swaroop's supplied labels and uses a new browser storage namespace to avoid restoring old blank drafts. The frozen sheet generator and its separate presentation fixup remain unchanged. Completed-review reproduction reads the supplied human-label JSON and preserves predictions and evidence, without rerunning agents:

    python -B -m arp.m3_agreement

Host-only run evidence is artifacts/private/m3-confirmation-001. The frozen intervention and rubric remain unchanged. Human labeling and agreement are complete under the approved reduced scope. Stop before M4.

## Approved M5 completion before M4

October 2, 2026. The user approved the reordered milestone execution and all forty remaining scored slots across twelve tasks. M5 now has all 48 outcomes, reusing eight M3 baselines without reruns. Confirmation success is 12/16 in both arms, delta 0 pp; the degenerate bootstrap triggers the Hoeffding 95% interval [-96.03, +96.03] pp, so the result is inconclusive. Wall-time delta is +2.662s, paired bootstrap 95% [-3.121, +10.538]s, also inconclusive. All-task results are descriptive (baseline 18/24, intervention 19/24); only development task click-010 improved. See [M5 analysis](m5_results.md).

The separate M5 order amendment records task-block randomization seed 20261002 while preserving all frozen configuration and M3 human labels. The authorized forty runs plus one native gate bring lifetime CLI invocations to 69, replacing the earlier approximate 50 planning ceiling. Incremental paid API spend is $0. There were no infrastructure exclusions, usage-limit stops, or Docker timeouts; owned resources are cleaned up. Stop for M5 review before M4.
