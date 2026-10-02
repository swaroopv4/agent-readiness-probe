# Two-minute report walkthrough

Open `reports/click_readiness.html` before recording. Use the section links to move through the report, keeping evidence tables collapsed except where indicated. The spoken text below is about 250 words, paced for two minutes. Bracketed instructions are not spoken. No model or Docker runs are needed.

## 0:00–0:20 | The question

[Show the title and primary result cards.]

“This is a small historical-task probe for Click. It asks whether a coding agent completes maintenance tasks, what goes wrong, and whether one setup-guidance file helps. I recorded forty-eight attempts across twelve tasks using the same model and isolated evaluator.”

## 0:20–0:40 | The honest result

[Point to both success bars and the wide interval.]

“On eight confirmation tasks, both arms passed twelve of sixteen attempts. The observed lift was zero. The selected ninety-five percent interval spans about minus ninety-six to plus ninety-six percentage points. That is inconclusive, not proof of equivalence. Wall-time difference was also inconclusive.”

## 0:40–1:00 | Reading versus execution order

[Click Mechanism diagnostics. Point to metadata-error attempts.]

“All twenty-four intervention runs read the context file. Six nevertheless ran tests before its setup recipe and hit missing package-metadata errors. Both arms had the same error incidence. The evidence distinguishes exposure to instructions from following their order.”

## 1:00–1:20 | Repeat variability

[Click Repeat failures. Point to click-007 and click-008.]

“Click-seven and click-eight had both passing and failing attempts within each arm. Different patches produced different outcomes. This is agent variability, not demonstrated test flakiness. Two repeats help reveal instability, but cannot estimate a reliable success probability.”

## 1:20–1:40 | The verified trap

[Click Verified trap. Point to the import flow and microcheck table.]

“In the reviewed Click-six patch, a directly imported ANSI helper bypassed CliRunner's patched attributes. Runner-level color enabled still lost ANSI, while explicit function-level color preserved it. That mechanism was verified on the saved patch. A documentation fix has not been tested.”

## 1:40–2:00 | What comes next

[Click Ranked fixes, then briefly show Provenance.]

“The ranked candidates are requirement checks after the final edit and documenting this convention. Their effects are not measured. The tested setup file showed no observed confirmation lift. This pilot offers inspectable evidence and limits, with fresh held-out tasks needed before testing the new candidates.”
