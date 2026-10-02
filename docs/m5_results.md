# M5 analysis checkpoint

Status: **M5_complete_pending_review**. Eight M3 confirmation baselines are retained without reruns. New scored outcomes: 40/40; unlaunched slots: 0; total scored outcomes still missing: 0.

This is the M5 analysis checkpoint, not the deferred M4 readiness report. The [committed plan](m5_plan.md), [order/configuration JSON](../results/m5_plan.json), and [machine-readable analysis](../results/m5_summary.json) contain the full provenance.

## Primary confirmation outcome

Baseline: 12/16; intervention: 12/16.

Intervention minus baseline mean task success: **+0.000 percentage points**. Paired task-cluster bootstrap 95% interval: [0.000, 0.000] percentage points; 10,000 resamples, seed 20261002, 8 task clusters.

Conservative Hoeffding 95% interval: [-96.032, 96.032] percentage points (half-width 96.032). Selected method: Hoeffding fallback (degenerate bootstrap); selected interval [-96.032, 96.032]. Conclusion: **inconclusive**.

The bootstrap preserves each task's two repeats in both arms as one cluster. The Hoeffding bound applies to differences in [-1,1] and is clipped to that range; it is the fallback if the bootstrap endpoints coincide. A zero-containing selected interval is inconclusive, not evidence of equivalence.

| Confirmation task direction | Tasks |
|---|---|
| gains | none |
| losses | none |
| unchanged | click-001, click-004, click-005, click-006, click-007, click-008, click-011, click-012 |

Directions compare task mean success across both repeats, rather than selecting the best patch.
All-task gains (descriptive): click-010.
All-task losses (descriptive): none.
All-task unchanged tasks (descriptive): click-001, click-002, click-003, click-004, click-005, click-006, click-007, click-008, click-009, click-011, click-012.

## Key secondary: agent wall time

Confirmation mean wall time: baseline 54.334s; intervention 56.996s. Paired task mean difference (intervention minus baseline): **+2.662s**, bootstrap 95% interval [-3.121, 10.538]s.

Wall-time effect is **inconclusive** because its interval includes zero.

Agent wall-time caps: baseline 0; intervention 0. Failed task attempts remain included: baseline 4; intervention 4.

Wall time is the prespecified key secondary outcome. It includes task failures and cap durations, excludes infrastructure, and measures the recorded CLI elapsed duration (including CLI metadata collection), not evaluator time. A faster failed attempt is not an efficient completion. No success-only conditioning or failure-penalty composite is used. Tool calls, token usage, and failed public pytest runs are diagnostics.

## Per-task results

| Task | Split | Baseline pass/scored (planned 2) | Intervention pass/scored (planned 2) | Success delta, pp | Baseline mean seconds | Intervention mean seconds | Wall delta, seconds |
|---|---|---:|---:|---:|---:|---:|---:|
| click-001 | confirmation | 2/2 | 2/2 | +0.0 | 53.766 | 79.250 | +25.484 |
| click-002 | development | 2/2 | 2/2 | +0.0 | 62.602 | 67.281 | +4.680 |
| click-003 | development | 2/2 | 2/2 | +0.0 | 67.648 | 64.743 | -2.906 |
| click-004 | confirmation | 2/2 | 2/2 | +0.0 | 51.641 | 48.297 | -3.344 |
| click-005 | confirmation | 2/2 | 2/2 | +0.0 | 49.227 | 46.320 | -2.907 |
| click-006 | confirmation | 0/2 | 0/2 | +0.0 | 49.773 | 60.992 | +11.219 |
| click-007 | confirmation | 1/2 | 1/2 | +0.0 | 55.258 | 50.484 | -4.773 |
| click-008 | confirmation | 1/2 | 1/2 | +0.0 | 61.062 | 56.273 | -4.788 |
| click-009 | development | 2/2 | 2/2 | +0.0 | 52.297 | 50.742 | -1.554 |
| click-010 | development | 0/2 | 1/2 | +50.0 | 88.789 | 83.226 | -5.563 |
| click-011 | confirmation | 2/2 | 2/2 | +0.0 | 67.351 | 65.375 | -1.976 |
| click-012 | confirmation | 2/2 | 2/2 | +0.0 | 46.594 | 48.977 | +2.383 |

## Descriptive outcomes

| Population | Arm | Pass/scored | First chronological attempt pass/scored | First-attempt Wilson 95% | pass@2 tasks | Mean agent seconds |
|---|---|---:|---:|---|---:|---:|
| confirmation | baseline | 12/16 | 6/8 | [40.928, 92.852]% | 7/8 | 54.334 |
| confirmation | intervention | 12/16 | 6/8 | [40.928, 92.852]% | 7/8 | 56.996 |
| development_descriptive | baseline | 6/8 | 3/4 | [30.064, 95.441]% | 3/4 | 67.834 |
| development_descriptive | intervention | 7/8 | 4/4 | [51.011, 100.000]% | 4/4 | 66.498 |
| all_tasks_descriptive | baseline | 18/24 | 9/12 | [46.769, 91.106]% | 10/12 | 58.834 |
| all_tasks_descriptive | intervention | 19/24 | 10/12 | [55.197, 95.303]% | 11/12 | 60.163 |

Development and all-task outcomes are descriptive only. First attempt means the earliest actual launch per task/arm; randomization may put repeat 2 before repeat 1. pass@2 is descriptive across complete two-repeat task/arms and is not the primary effect or a selective best-patch score.

## Infrastructure, diagnostics, and accounting

Infrastructure/missing recorded outcomes: 0. Unlaunched slots: 0. Docker timeouts: 0.

| Population | Arm | Tool calls | Failed public pytest runs | Input tokens | Cached input tokens (subset) | Output tokens | Usage missing |
|---|---|---:|---:|---:|---:|---:|---:|
| confirmation | baseline | 115 | 4 | 1966145 | 1543680 | 33665 | 0 |
| confirmation | intervention | 118 | 7 | 1952209 | 1584896 | 32362 | 0 |
| development | baseline | 81 | 5 | 1643237 | 1378304 | 19781 | 0 |
| development | intervention | 78 | 4 | 1507075 | 1264128 | 18426 | 0 |

Lifetime CLI invocations observed: 69 (28 before M5; 41 in M5 including gate). Incremental paid API spend: **$0**; subscription dollar cost is not measured. No paid judge, provider fallback, quota purchase/reset, or M6.

## Limitations and review boundary

All eight M3 baseline repeat-1 runs precede intervention runs. Only the remaining baseline repeat 2 and intervention repeats 1 and 2 are randomized/interleaved. Arm order is not fully randomized; cohort/time confounding remains.

Eight confirmation clusters give limited and potentially unstable uncertainty estimates. Task selection is purposive; statements were made precise during validity review, and training exposure is unknown. Effects are conditional on this frozen CLI/model/runtime/task population. Development exposure guided intervention selection; those outcomes do not enter primary confirmation inference. The M5 analysis code was committed before the new runs but after M3 baseline outcomes were known, implementing the previously documented formulas.

The frozen model, prompt sentence, AGENTS bytes, rubric, evaluator, and all M3 human labels remain unchanged. Requirement-verification guidance observed during M3 review remains an untested future candidate; it is not part of this treatment.

## Verification

The [saved-evidence and cleanup audit](../results/m5_audit.json) passed for all 40 new attempts and the eight retained baselines. All 24 intervention traces contain visible full AGENTS reads. No owned container or network remains; no saved auth credential bytes were detected. Frozen configuration and M3 human labels are unchanged. Core tests: 106 passed, one skipped for Windows host symlink privilege.

**Stop here for M5 review. Do not start M4.**
