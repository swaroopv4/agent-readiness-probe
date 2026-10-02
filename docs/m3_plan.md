# M3 freeze and approved reduced plan

October 2, 2026, America/Los_Angeles. Calibration was committed as e4b0637. The user approved freezing gpt-5.6-luna / low, success primary, agent wall time as the prespecified key secondary outcome, and tool calls, tokens, and failed public test runs as diagnostic outcomes. CLI 0.153.1 and the pinned M2 images remain the runtime configuration. The user approved this intervention and reduced M3 scope on October 2, 2026. The exact intervention, common prompt, development-derived rubric, and remaining M5 order are frozen before confirmation execution in results/m3_freeze.json. Earlier proposal text below is retained as provenance; this approval section controls execution.

## Draft AGENTS.md

The full candidate is [interventions/drafts/setup-v1/AGENTS.md](../interventions/drafts/setup-v1/AGENTS.md). It contains only general package installation, import-path, and public pytest instructions. Its source evidence is the public pyproject.toml, src layout, public tests/test_basic.py, and tests/conftest.py in the four development base snapshots. The metadata issue is observable in the base's public tests/test_deprecations.py where that file exists. No future commit, hidden test, gold patch, confirmation packet, or confirmation outcome was consulted to draft it. Test dependencies and scratch paths describe the existing common runtime.

The candidate uses a real offline installation rather than synthesized package metadata: pip builds this checkout using its declared Flit backend, with no index, dependency resolution, or build-isolation download. The build backend and pytest are already present in the frozen image. PYTHONPATH puts the working src tree before the scratch installation, so subsequent edits are tested rather than a stale installed source copy. No setup is pre-applied to either arm by the host.

Mechanical command checks in fresh network-none containers with the frozen agent image succeeded on all four unmodified development snapshots:

| Development task | Focused public tests passed | Full public tests passed | Collection errors |
|---|---:|---:|---:|
| click-002 | 102 | 1991 | 0 |
| click-003 | 102 | 1940 | 0 |
| click-009 | 88 | 1624 | 0 |
| click-010 | 88 | 1510 | 0 |

These are setup/test recipe checks, not additional scored agent attempts or an intervention-effect estimate. They used no Codex inference, auth file, proxy, hidden tests, or gold patches. All four received byte-identical AGENTS.md content. The private verification store is artifacts/private/intervention-draft-check-001; public-base source hashes and draft fingerprint are recorded in [the proposal JSON](../results/m3_proposal.json). A draft fingerprint is an audit reference, not an approved intervention freeze.

## Delivery proposal

Deliver AGENTS.md as a file at /workspace/AGENTS.md in the intervention arm's clean staged input. The baseline has no overlay. Copy the same approved bytes for every task and repeat; do not template task IDs, package versions, test names, or setup commands. The install command obtains the version from each base's existing manifest itself.

Keep the CLI's ignore-rules and disabled automatic document discovery settings. Add this one sentence to the common task prompt in BOTH prospective arms:

> If /workspace/AGENTS.md exists, read it before starting the task.

Do not paste the AGENTS contents into the prompt or rely on automatic discovery. The shared sentence is necessary because the current M2 flags suppress automatic AGENTS ingestion. The task instructions and TASK.md body otherwise match across arms. The file's presence and contents are the treatment. Record the approved overlay hash, common-prompt bytes/hash, CLI flags, image IDs, and input snapshots before launching. All future attempts use that same delivery procedure.

The four earlier Luna attempts remain development calibration; the new common prompt is versioned, and their outcomes are not silently pooled into a prospective confirmation denominator. Require the host collector to verify the AGENTS file is unchanged before creating the production-only patch. Preserve all existing immutable task/test/configuration checks. The evaluator is unchanged and receives the trusted original test workspace plus the allowed production patch, with no intervention file or scratch package installation. Agent auth and network restrictions remain unchanged.

No agent delivery smoke or confirmation attempt is run by this proposal. Instruction compliance should be audited from exposed read/tool events; noncompliance must not be silently dropped from scoring. No runner/CLI flag change has been applied to deliver this draft yet.

## click-010 Luna failure review

The reviewed trajectory is artifacts/private/dev-ceiling-001/04-click-010-baseline-0. Its first public pytest call, item_12, completed collection and reported 29 failed / 1481 passed / 23 skipped / 1 xfailed. The final focused public call, item_20, still had one assertion failure. None of its completed shell outputs contained PackageNotFoundError, ERROR collecting, ImportError, or ModuleNotFoundError. The offline evaluator reported 69 failures and zero collection errors. The public base has no tests/test_deprecations.py, unlike click-002 and click-003.

The observed failed tests are behavioral. There is no trace evidence that the same missing-package-metadata collection problem contributed to this attempt. This is an observable failure classification, not proof about hidden reasoning or a prediction that setup documentation will rescue it. The failed attempt remains a failure and was not retried. No task-specific arbitration or solution information appears in the candidate AGENTS.md.

## Reduced M3 scope proposed for approval

Run eight baseline confirmation attempts: one fresh gpt-5.6-luna / low attempt on each of the eight accepted confirmation tasks. No replacement of completed poor outcomes or best-of-N selection. All confirmation packets/outcomes remain unopened during intervention drafting.

The user will human-label twelve real Luna trajectories:

- Four existing development attempts from artifacts/private/dev-ceiling-001 for rubric development/calibration, including the genuine click-010 failure and the three successful controls.
- Eight new baseline confirmation trajectories for classifier evaluation, one per confirmation task. Preserve successful, failed, task-local setup, and capped attempts; report runner/provider infrastructure failures separately.

The four development trajectories already informed model/intervention selection; they are not held-out evaluation examples. Develop the rule/rubric using those four and the user's evidence-backed labels, then freeze it before opening the eight confirmation trajectories. Compute evaluation agreement and supported per-class diagnostics on the eight confirmation traces only. Report development labeling separately. No human labels have been supplied yet; assistant trace review does not count as human annotation. No paid or optional Codex judge calls are planned.

This proposal reduces the original 20-human-label milestone to 12 total labels, with only 8 evaluation examples across 8 task clusters. The original 20-label acceptance requirement is not met, and this replacement needs the user's approval. Label coverage is limited; absent classes remain not measured, unclassified/abstention is permitted, and the sample cannot support a broad classifier-validation claim or inter-human agreement estimate. Do not fabricate or manufacture failures to meet a quota. If an infrastructure issue prevents eight usable evaluations, report the gap and stop for a decision rather than silently replacing it.

Success remains primary. Report recorded agent wall seconds for every attempt as the key secondary outcome, alongside outcome and cap indicators so an early failed attempt is not interpreted as efficient completion. No failure-penalty composite is approved. Tool calls, CLI tokens, and failed public test runs are diagnostic, with unavailable counters marked not measured. M3 is a baseline/labeling milestone and supplies no paired intervention-effect estimate.

## Approval sequence and resources

Before any confirmation launch, the user must approve this exact intervention text, delivery procedure, reduced labeling requirement, and prospective M3 plan. Then freeze the overlay and common prompt. Obtain the user's four development labels and freeze the rubric before confirmation traces are opened. Run only the eight baseline attempts after the full M2 gate passes. Stop on Codex usage limits or two Docker timeouts; use the same 900-second agent cap, 300-second offline evaluator cap, and $0 paid-API cap. Prompt-requested command time remains 120 seconds, without claiming an independent native per-command timeout enforcement guarantee.

There are 19 prior CLI invocations, unchanged by the four mechanical checks. Eight baseline attempts plus one native endpoint/tool gate would bring the planned M3 total to 28, leaving 22 slots under the original approximate 50 ceiling. Additional infrastructure retries or probes require explicit accounting. No quota purchase, provider switch, paid judge, M6, or outreach is authorized.

A later paired intervention experiment needs its own approved plan and checkpoint. If all M3 baselines run before all intervention attempts, that ordering cannot be called randomized arm order. Before claiming intervention lift, decide whether to obtain new randomized pairs or disclose fixed-order/temporal limitations; do not silently carry over the original two-repeats/randomized 48-run analysis. Confirmation evidence must never revise this intervention; revising it after exposure requires fresh held-out tasks.

Stop here for the user's approval. No intervention freeze or confirmation run has occurred.

## Approved execution freeze (supersedes proposal gates above)

The exact bytes of interventions/drafts/setup-v1/AGENTS.md are frozen in place; its historical drafts directory does not imply it is editable. SHA256: ae59af6e5b2ef1b510958ef4159c0e0c05d9cbc0d313db7617fb6781dbc43c89. The user-approved delivery is a workspace file in the intervention arm only. Both prospective arms receive the sentence "If /workspace/AGENTS.md exists, read it before starting the task." The complete shared prompt prefix, rubric, calibrated development rule outputs, accepted manifest digest, CLI settings, source digests, and pinned images are recorded in [m3_freeze.json](../results/m3_freeze.json). The runner refuses uncommitted or changed freeze artifacts.

The deterministic rubric is calibrated using only the four existing Luna development traces, then committed before any confirmation run. The user's current instruction authorizes rule calibration before human review; obtaining four human labels first is no longer an execution prerequisite. Human annotation remains pending: development rule output is not human ground truth, and classifier agreement is not measured until the user labels the sheet. Rule primary labels describe terminal outcomes, with intermediate setup/behavior events recorded as secondary diagnostics. The eight confirmation traces are held out from rule development. Rules and intervention cannot be changed after their exposure. Missing-context, wrong-file, and flakiness claims require human evidence; unsupported cases remain unclassified.

Run exactly eight baseline confirmation attempts, one per accepted task, explicitly numbered baseline repeat 1 (one-based M5 numbering). The prior development repeat-0 data is calibration only. All eight M3 attempts are retained as baseline repeat 1 in M5; they must never be rerun, replaced for a poor outcome, or relabeled as extra pilot attempts. Preserve failed, capped, and invalid submissions in the task denominator. Stop for usage limits or runner/provider infrastructure failures; no automatic retry or fallback. Human review comprises 4 development calibration rows plus 8 held-out confirmation rows, 12 total, with no claim of meeting the original 20-label gate.

M3 baseline repeat 1 precedes all intervention runs. Arm order is therefore not fully randomized and time/cohort confounding is a limitation. In M5, interleave the remaining baseline repeat 2 and both intervention repeats 1 and 2 in the frozen randomized order (seed 20261002, 24 remaining attempts). The user approved this order plan; this turn does not launch those attempts. Reuse all eight M3 baselines in the final two-repeats-per-arm, eight-task result. Do not claim complete arm-order randomization or reuse the original unqualified randomized-arm analysis.

Operational accounting remains 19 prior CLI invocations. M3's eight baselines plus one gate bring the projected total to 28. The later 24 M5 attempts plus one new gate would bring it to 53, exceeding the original approximate 50 ceiling by three. Record that resource limitation for the M5 checkpoint; no M5 launch or expansion occurs now. Paid API spend remains capped at $0.

Commit this freeze and the guarded runner first. Then run the full isolation/network/native-tool gate, the eight baselines, the unchanged rule labeler, and prepare a simple editable HTML/CSV labeling sheet with one row per trajectory, task, outcome, rule label, key evidence, and blank human fields. Stop when the sheet is ready. M3 remains pending human labeling and agreement analysis rather than being reported complete.
