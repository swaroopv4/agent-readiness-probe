# Five findings from the Click pilot

These findings use the 48 experimental outcomes and saved trace evidence. Primary inference uses eight confirmation tasks. Development-inclusive diagnostics are descriptive. Human labels concern twelve M3 trajectories only. Model and reasoning were frozen at gpt-5.6-luna / low.

## 1. Reading setup guidance did not guarantee executing setup first

All 24 intervention attempts visibly read the complete frozen AGENTS.md. Six ran pytest before its install recipe, received Click `PackageNotFoundError` collection errors, and installed package metadata later. Confirmation metadata-error incidence was 2/16 in each arm, and all-task incidence was 6/24 in each arm.

The intended first-error avoidance did not appear in attempt-level counts. This does not establish intent, comprehension, or the effect of enforcing setup order. All-task metadata-error command counts were seven baseline and six intervention because one baseline attempt repeated the error. [Definitions and exact events](m4_results.md#descriptive-mechanism-diagnostics)

## 2. Outcomes varied across agent attempts on the same task

Click-007 passed baseline repeat 1 and failed repeat 2, while intervention failed repeat 1 and passed repeat 2. Click-008 failed repeat 1 and passed repeat 2 in each arm. Their arm mean success rates therefore did not change, even though individual outcomes did.

These attempts produced different patches. They are not repeated executions of an unchanged patch, so this is agent run-to-run variability, not demonstrated test flakiness. Two repeats are insufficient to estimate reliable task-level success probabilities. Selecting the successful patch alone would conceal this variability. [Recorded repeat outcomes](m4_results.md#failures-across-nominal-repeats)

## 3. A source convention caused deterministic behavior in one reviewed patch

In the saved M3 click-006 patch, `termui` directly imported `should_strip_ansi`. `CliRunner.isolation` rebound the `_compat` and `utils` attributes but left that imported reference intact. The retained function used TTY detection when the function-level color argument was `None`, bypassing runner-level `color=True`.

Recorded public API microchecks on the saved source showed ANSI stripped with runner-level color enabled and preserved with explicit prompt/confirm `color=True`. This confirms Swaroop's hypothesis for that patch without changing his labels. All four click-006 attempts failed the same two hidden tests, but a shared hidden-test signature does not establish that every patch used this same mechanism. Documenting the convention is an untested candidate with no measured lift. [Source verification](m3_human_review.md#click-006-hypothesis-check)

## 4. The tested setup file showed no observed confirmation lift

Baseline and intervention both passed 12/16 confirmation attempts. Every confirmation task had a zero arm-mean success difference, so the paired task-cluster bootstrap interval was degenerate at [0, 0]. The prespecified Hoeffding fallback was **95% [-96.032, +96.032] percentage points**, centered on an observed delta of zero. The primary result is **inconclusive**, not evidence of equivalence or proof that setup guidance never helps.

Mean agent wall time was 54.334s baseline and 56.996s intervention. The +2.662s paired difference had bootstrap 95% [-3.121, +10.538]s and was also inconclusive. All-task success was 18/24 versus 19/24, with the sole gain on development click-010, reported descriptively. No measured productivity or ROI gain follows. [Frozen analysis](m5_results.md)

## 5. Automated diagnostics needed human and trace-level review

The rule labeler had primary agreement 6/8 on held-out M3 traces, but it abstained on both failures. Its failure coverage was 0/2, so aggregate agreement did not establish failure-classification ability. Swaroop labeled both `reasoning_error`, adding `missing_context` for click-006. Both reviewed failures stopped after existing tests passed without checking every stated requirement.

Separately, the original public-test failure counter counted two intervention commands where pytest passed and a subsequent Git operation failed. Trace-confirmed failed pytest commands were four baseline versus five intervention on confirmation, and nine versus nine across all tasks. Original counts were preserved rather than overwritten.

Human review supplied distinctions the rule did not, while raw output clarified what a shell exit meant. Requirement-verification guidance and checks after the final edit are untested candidates, not demonstrated rescues. The single reviewer was unblinded, and these confirmation-derived candidates require fresh held-out tasks. [Human agreement](m3_human_review.md), [counter audit](m4_results.md#descriptive-mechanism-diagnostics)

The pilot is limited by purposive historical tasks, unknown training exposure, precise reconstructed statements, eight confirmation clusters and partially randomized arm order. Credentials were visible in ephemeral agent containers by explicit acceptance. Incremental paid API spend was $0, while subscription dollar cost and human effort were not measured. No new experiment or intervention was performed for these findings.
