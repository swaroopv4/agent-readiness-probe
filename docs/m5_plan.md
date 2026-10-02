# M5 approved execution and analysis plan

October 2, 2026. The user approved running M5 before M4 and completing the twelve-task, two-arm, two-repeat experiment. M4 remains unauthorized until M5 review.

## Scope and retention

There are 48 experimental slots: 12 tasks x 2 arms x 2 repeats. The eight M3 confirmation baselines are baseline repeat 1 and are retained byte-for-byte, including both failures. Run exactly 40 new slots: 24 confirmation and 16 development. Earlier M2 smokes used another model; Luna development calibration used the prior prompt and repeat 0. Those runs remain historical and are excluded from this experiment. No outcome-based retries or replacements.

## Order amendment

The latest instruction supersedes only the future global order in the historical M3 freeze. Its intervention, common prompt, rubric, model, images, baseline-reuse rule, and original evidence remain unchanged. A separate committed [M5 plan](../results/m5_plan.json) records this approved amendment and source hashes before any new launch.

Seed: **20261002**. Use Python Random(seed), shuffle the sorted task blocks, then shuffle each block's remaining arm/repeat slots. This is blocked randomization of the remaining slots, permitting consecutive same-arm draws. M3 baseline repeat 1 still precedes all intervention runs; full arm-order randomization is not claimed. Development tasks are descriptive only and cannot revise the intervention.

## Fixed runtime and stops

Use gpt-5.6-luna / low, Codex CLI 0.153.1, the frozen common prompt including its AGENTS sentence, and intervention-only /workspace/AGENTS.md with SHA256 `ae59af6e5b2ef1b510958ef4159c0e0c05d9cbc0d313db7617fb6781dbc43c89`. No hidden tests, gold patches, private artifacts, history, or Docker socket enter agents. Read-only auth remains visible inside each ephemeral container as already accepted. The same evaluator runs fresh and offline. Re-run the full unchanged network/native-tool gate before scored attempts.

Keep the $0 paid-API cap and ChatGPT login, 900-second agent and 300-second evaluator caps. Checkpoint every slot and outcome to the private ledger/progress and tracked summary. Stop for usage limits or two Docker timeouts; retain infrastructure outcomes as exclusions/missing, do not retry or fallback. Any critical infrastructure failure also stops rather than silently replacing the slot.

This approval replaces the earlier approximate 50 invocation planning ceiling: 28 prior calls + 40 scored calls + one gate project to 69, with actual calls separately recorded. No paid judge, quota purchase, automatic limit reset, provider switch, or M6.

## Analysis

Primary: mean of eight confirmation-task differences, each difference intervention mean success across two repeats minus baseline mean success across two repeats. Compute the paired task-cluster percentile 95% bootstrap with 10,000 resamples, seed 20261002; both arms/repeats stay within each sampled task. Also report the clipped Hoeffding interval for differences in [-1,1], half-width sqrt(2*log(40)/8), and use it as fallback when bootstrap endpoints coincide. An interval containing zero is inconclusive; report negative effects as possible regression. No equivalence claim.

Key secondary: intervention minus baseline task-mean agent wall seconds, using the same paired clusters and bootstrap. Include failed task attempts and cap indicators, excluding infrastructure. Interpret wall time with success; a quicker failed attempt is not efficient completion. No success-only conditioning or penalty composite. Tool calls, tokens, and failed public test runs remain diagnostics.

Report each task's counts/deltas, gains/losses/unchanged confirmation tasks, first chronological attempt per arm with Wilson intervals, and descriptive pass@2. All-task and development results are descriptive; do not pool development into the primary inference. Show infrastructure exclusions, unlaunched slots, and coverage. Incomplete confirmation data blocks the final comparable estimate, with missing outcomes shown rather than counted as task failures.

The historical precise task statements, purposive selection, unknown training exposure, eight confirmation clusters, partially randomized arm order, and time/cohort confounding remain limitations. Candidate interventions observed during M3 review remain untested future work; do not alter frozen AGENTS.md.

Commit this plan and guarded analysis/runner before launch. After the batch, audit evidence, record analysis, commit, and **stop before M4**.

## Frozen remaining order

| New slot | Task | Split | Arm | Repeat |
|---:|---|---|---|---:|
| 1 | click-007 | confirmation | baseline | 2 |
| 2 | click-007 | confirmation | intervention | 2 |
| 3 | click-007 | confirmation | intervention | 1 |
| 4 | click-002 | development | baseline | 1 |
| 5 | click-002 | development | baseline | 2 |
| 6 | click-002 | development | intervention | 1 |
| 7 | click-002 | development | intervention | 2 |
| 8 | click-005 | confirmation | intervention | 2 |
| 9 | click-005 | confirmation | intervention | 1 |
| 10 | click-005 | confirmation | baseline | 2 |
| 11 | click-001 | confirmation | intervention | 1 |
| 12 | click-001 | confirmation | baseline | 2 |
| 13 | click-001 | confirmation | intervention | 2 |
| 14 | click-010 | development | intervention | 2 |
| 15 | click-010 | development | baseline | 1 |
| 16 | click-010 | development | baseline | 2 |
| 17 | click-010 | development | intervention | 1 |
| 18 | click-008 | confirmation | intervention | 1 |
| 19 | click-008 | confirmation | baseline | 2 |
| 20 | click-008 | confirmation | intervention | 2 |
| 21 | click-004 | confirmation | intervention | 1 |
| 22 | click-004 | confirmation | intervention | 2 |
| 23 | click-004 | confirmation | baseline | 2 |
| 24 | click-006 | confirmation | intervention | 1 |
| 25 | click-006 | confirmation | baseline | 2 |
| 26 | click-006 | confirmation | intervention | 2 |
| 27 | click-009 | development | intervention | 1 |
| 28 | click-009 | development | baseline | 1 |
| 29 | click-009 | development | intervention | 2 |
| 30 | click-009 | development | baseline | 2 |
| 31 | click-012 | confirmation | intervention | 1 |
| 32 | click-012 | confirmation | baseline | 2 |
| 33 | click-012 | confirmation | intervention | 2 |
| 34 | click-011 | confirmation | intervention | 2 |
| 35 | click-011 | confirmation | intervention | 1 |
| 36 | click-011 | confirmation | baseline | 2 |
| 37 | click-003 | development | baseline | 1 |
| 38 | click-003 | development | intervention | 1 |
| 39 | click-003 | development | baseline | 2 |
| 40 | click-003 | development | intervention | 2 |
