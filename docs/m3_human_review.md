# M3 human review and agreement

October 2, 2026. Reviewer **Swaroop** supplied all twelve primary labels, secondary label sets, and notes directly in the conversation. [The supplied review](../review/m3_human_labels.json) preserves the reviewer's notes, including the originally unconfirmed hypothesis. Its timestamp is transcription time, not an inferred time spent reviewing. The [CSV](../review/m3_labeling_sheet.csv), [HTML sheet](../review/m3_labeling_sheet.html), and [evidence bundle](../review/m3_labeling_evidence.json) now contain those labels. Original rule predictions and trace evidence are unchanged; human decisions are separate fields, not replacements for rule outputs.

## Held-out confirmation agreement

Evaluation uses only the eight confirmation trajectories. The four development rows are reported separately as calibration. [Machine-readable agreement](../results/m3_agreement.json) includes every taxonomy class, nonzero confusion cells, undefined denominators, secondary-label diagnostics, and abstention coverage.

| Measure | Eight confirmation trajectories |
|---|---:|
| Primary exact agreement | 6/8 = 75% |
| Primary Cohen's kappa | 0.428571 |
| Secondary set exact agreement | 7/8 = 87.5% |
| Both primary and secondary agree | 6/8 = 75% |
| Rule non-abstention coverage | 6/8 = 75% |
| Rule abstentions | 2/8 = 25% |
| Agreement among non-abstained rows | 6/6 = 100% |
| Non-abstention coverage on failed outcomes | 0/2 = 0% |

Kappa includes `unclassified` as a distinct predicted category and counts both abstentions as disagreements. Observed agreement is 0.75; chance agreement from marginal frequencies is 0.5625; kappa is (0.75 - 0.5625)/(1 - 0.5625) = 3/7. Secondary comparison uses exact sets, ignoring ordering; the empty set means no secondary label. The 100% agreement among covered rows concerns only successful trajectories and cannot establish failure-classification performance.

| Human primary | Rule primary | Count |
|---|---|---:|
| no_failure | no_failure | 6 |
| reasoning_error | unclassified | 2 |

For primary `no_failure`, precision and recall are both 6/6 = 100%. For primary `reasoning_error`, recall is 0/2 = 0%; precision is undefined because the rule made no such prediction. The rule's two `unclassified` predictions were abstentions, not human-labeled `unclassified` examples. Their categorical precision is 0/2 and recall is undefined. Other primary classes have zero human and predicted support and are not measured.

For secondary labels, `env_setup` has one human-positive and one correct rule prediction (precision/recall 100%); `reasoning_error` has three human-positive and three correct predictions (precision/recall 100%). `missing_context` has one human-positive and zero predictions (recall 0%, precision undefined). Other secondary classes are absent and not measured. No aggregate over absent classes is reported.

The disagreements are preserved:

- **M3-08 / click-006:** rule primary `unclassified`, no secondary; human primary `reasoning_error`, secondary `missing_context`.
- **M3-10 / click-008:** rule primary `unclassified`, no secondary; human primary `reasoning_error`, no secondary.

Development calibration alone has primary agreement 4/4, secondary set agreement 4/4, joint agreement 4/4, primary kappa 1, and coverage 4/4. These examples informed the frozen rubric and are not held-out validation. There is no pooled validation claim across twelve rows.

## click-006 hypothesis check

**Confirmed for the runner-level color-enabled case.** In the saved submitted source, [testing.py](../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/testing.py) lines 504-523 define the isolation replacement for `should_strip_ansi`. When its color argument is `None`, it uses the runner's `default_color`. Isolation rebinds `utils.should_strip_ansi` and `_compat.should_strip_ansi`; it does not rebind `termui.should_strip_ansi`.

The submitted patch imports `should_strip_ansi` directly into `termui` and calls that retained reference in `_prepare_prompt`. Replacing `_compat`'s attribute does not update the reference already bound in `termui`. The original [_compat.py](../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/_compat.py) lines 498-509 uses TTY autodetection for `color=None`; the runner's captured stdout is not a TTY. [globals.py](../artifacts/private/m3-confirmation-001/04-click-006-baseline-1/captured_source/src/click/globals.py) lines 54-67 leaves the default `None` when the command context supplies no color setting. As a result, `runner.invoke(..., color=True)` alone does not reach this imported reference, and ANSI is stripped before the runner's visible-input function writes the prompt.

A host-only Python inspection of this exact captured source, with bytecode writes disabled, confirmed the function identities inside `runner.isolation(color=True)`: `termui` retained the original function, `_compat` was patched, and `utils` used the patched function. With the same captured stdout and `color=None`, the `termui` reference returned strip=True while the patched `_compat` reference returned strip=False. Public API microchecks on the saved patch produced:

| Call inside `runner.invoke(..., color=True)` | Observed output |
|---|---|
| `prompt(style("Name", fg="green"))` | `Name: Bob\n` |
| `prompt(style("Name", fg="green"), color=True)` | `\x1b[32mName\x1b[0m: Bob\n` |
| `confirm(style("Hello World!", fg="green"))` | `Hello World! [y/N]: y\n` |
| `confirm(style("Hello World!", fg="green"), color=True)` | `\x1b[32mHello World!\x1b[0m [y/N]: y\n` |

Thus explicit `color=True` on the new prompt/confirm parameter retains ANSI; the broken case is color enabled through the runner with the function's default color. This check explains the saved failures but does not amend Swaroop's labels or notes. It is post-review assistant inspection, not an agent-authored test, a new scored confirmation attempt, or a fresh offline evaluation. It used no hidden tests or gold patches. The frozen intervention and rules are unchanged.

## Observed pattern and future work

Swaroop observed that both confirmation failures stopped after existing tests passed without verifying every stated requirement. The saved trace supports that bounded observation: click-006 ran the existing suite and added no custom branch check; click-008's two pre-patch diagnostic scripts did not exercise the TTY/nonexistent-PAGER path, and were not rerun after its final patch. This is a pattern in these two failures, not evidence of its prevalence elsewhere or proof that additional checks would rescue them.

Record **explicit requirement coverage checks and rerunning relevant checks after the final patch** as an **untested candidate intervention for future work**. This candidate comes from exposed confirmation evidence. It is not added to setup-v1, not frozen, and not authorized for execution. Any later experiment selecting this candidate needs fresh held-out tasks; these tasks cannot support an untouched confirmation claim for it. Frozen AGENTS.md remains byte-identical at SHA256 `ae59af6e5b2ef1b510958ef4159c0e0c05d9cbc0d313db7617fb6781dbc43c89`.

## Interpretation and checkpoint

There are only eight held-out task clusters. One reviewer saw rule predictions and aggregate outcomes; the two detailed failure reviews also included hidden failure evidence, which the deterministic rule does not use. Possible anchoring and differences in evidence access limit the comparison. Inter-human agreement is not measured, and absent classes are not validated. The user-approved twelve-label scope replaces the original twenty-label milestone requirement; this is a limited pilot, not broad classifier validation.

M3 is complete under the approved reduced scope. All eight baseline repeat-1 results remain retained for M5 without reruns. No additional agent, evaluator, or judge invocation occurred; accounting remains 28 CLI invocations and $0 incremental paid API spend. **Stop before M4.**

To reproduce only the supplied labels and agreement, without generating trajectories or blanking the review:

```powershell
python -B -m arp.m3_agreement
```

The original frozen `arp.m3_sheet` generator is historical preparation code that writes blank human fields. Do not use it to reproduce the completed review; the supplied human-label JSON is now the annotation source of truth.
