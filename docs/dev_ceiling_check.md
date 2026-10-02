# Development ceiling check, before M3

M2 was committed first as eefd24ad0eb283af6fb11cac0dc9a0510b5f86dd on codex/phase-0-2. This check uses development tasks only: click-002, click-003, click-009, and click-010. No confirmation task was launched, and no confirmation outcome was used for configuration selection. M3 has not started. The user approved gpt-5.6-luna / low and the outcome hierarchy on October 2, 2026. The intervention and confirmation execution remain pending approval.

## Five accepted M2 smokes

All five used CLI 0.153.1, gpt-6-astra, and low reasoning. These are the original attempts, including the second click-002 attempt; no reruns were substituted.

| Attempt | Outcome | Agent wall (s) | CLI turns | Tools (command + edit) | Input | Cached input | Output | Reasoning output | Failed public pytest runs |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| 01-click-002-baseline-0 | pass | 64.078 | 1 | 9 (9 + 0) | 97,324 | 79,872 | 1,334 | 133 | 1 |
| 02-click-003-baseline-0 | pass | 85.344 | 1 | 8 (8 + 0) | 150,536 | 122,368 | 1,714 | 169 | 1 |
| 03-click-009-baseline-0 | pass | 56.656 | 1 | 5 (5 + 0) | 84,813 | 64,896 | 1,376 | 13 | 0 |
| 04-click-010-baseline-0 | pass | 160.265 | 1 | 10 (10 + 0) | 240,378 | 201,600 | 4,186 | 949 | 0 |
| 05-click-002-baseline-1 | pass | 71.265 | 1 | 6 (6 + 0) | 108,654 | 80,896 | 1,431 | 151 | 1 |

Smokes 1, 2, and 5 each had one initial public pytest collection error: importlib.metadata.PackageNotFoundError for Click in tests/test_deprecations.py. Each then supplied temporary package metadata outside the task's immutable files and reran successfully: 1,991 / 1,940 / 1,991 passed, respectively. Smoke 3's public suite passed 1,624 tests. Smoke 4's two public suite runs each passed 1,510 tests; its 170-case precedence diagnostic also passed. Their expected xfails are not unsuccessful test runs. No observed intermediate pytest run had a behavioral assertion failure in these five smokes. Intentional pre-fix pickle reproductions in the two click-002 attempts displayed the original bug and are recorded separately from pytest failures. Nonzero git/optional-file/optional-tool lookup commands are preserved in the JSON report and are not labeled as test failures. The CLI also emitted its unstable-feature warning in each attempt; that warning did not prevent native execution.

All five offline evaluator verdicts passed, with 2,000 / 1,953 / 1,630 / 1,587 / 2,000 passing tests and zero failures or errors. Public counts differ because hidden tests are injected only in the separate offline evaluator.

## Models available through this login's CLI catalog

The authenticated catalog was freshly queried through the same read-only ChatGPT login and internal proxy network, using the CLI's models endpoint with client_version=0.153.1. This discovery requested no inference. The query recorded only model metadata, not credentials or model instructions.

| Account catalog model | CLI picker | Supported reasoning | Default |
|---|---|---|---|
| gpt-6-astra | list | low, medium, high, xhigh, max, ultra | low |
| gpt-reserve | hide | low, medium, high, xhigh, max | medium |
| gpt-5.6-sol | list | low, medium, high, xhigh, max, ultra | low |
| gpt-5.6-terra | list | low, medium, high, xhigh, max, ultra | medium |
| gpt-5.6-luna | list | low, medium, high, xhigh, max | medium |
| gpt-5.5 | list | low, medium, high, xhigh | medium |
| codex-auto-review | hide | low, medium, high, xhigh, max | medium |

The five entries marked list are the standard CLI picker options exposed to this login. gpt-5.6-luna is the smallest named coding tier among those options; low is its lowest supported reasoning level. That is the operational definition of weakest used for these four attempts. The hidden gpt-reserve entry is described as fast and affordable agentic coding, but its strength relative to Luna and its intended use are not established by the catalog. codex-auto-review is designated for automatic approval review. Neither hidden entry was used as a task model. Catalog advertisement does not independently establish inference availability for every untested entry: gpt-6-astra and gpt-5.6-luna are directly inference-validated here; the other entries are catalog-advertised. The older saved catalog is not used to claim current availability.

The CLI explicitly sets model="gpt-5.6-luna" and model_reasoning_effort="low". The probe and all four task rollouts identify that model and observe low reasoning, despite the catalog's medium default. This is client/rollout evidence; the backend's underlying served identity is not separately exposed. See the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) for the model_reasoning_effort and web_search settings.

## Four weaker-model development attempts

The original pinned images, evaluator, task prompts, 900-second agent wall limit, and 300-second evaluator limit were retained. The read-only auth file was visible inside each ephemeral agent container, as explicitly accepted. The full network and native-tool gates passed before attempt 1; web search remained disabled. The failed attempt was retained without a retry or model fallback.

| Attempt | Outcome | Agent wall (s) | CLI turns | Tools (command + edit) | Input | Cached input | Output | Reasoning output | Failed public pytest runs |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| 01-click-002-baseline-0 | pass | 53.593 | 1 | 9 (7 + 2) | 163,895 | 132,864 | 2,001 | 405 | 2 |
| 02-click-003-baseline-0 | pass | 49.437 | 1 | 8 (7 + 1) | 113,670 | 93,952 | 1,825 | 245 | 1 |
| 03-click-009-baseline-0 | pass | 48.016 | 1 | 8 (7 + 1) | 131,847 | 109,312 | 1,692 | 537 | 0 |
| 04-click-010-baseline-0 | fail | 122.219 | 1 | 18 (14 + 4) | 454,247 | 391,680 | 4,687 | 2,288 | 2 |

- click-002: two public pytest collection errors for missing Click metadata, one before and one after the source fix; a pre-fix pickle diagnostic also failed as expected. Its post-fix sentinel/Option diagnostic passed. The agent did not obtain a successful full public suite run. The independent offline evaluator passed 2,000 tests, with 25 skipped.
- click-003: one actual public suite collection error for the same metadata issue. A separate git diff && pytest command failed at git because the container has no repository history, so pytest never ran in that command. The later selected options/basic tests passed 665 tests, with 71 deselected. The independent offline evaluator passed 1,953 tests, with 25 skipped.
- click-009: the public suite passed 1,624 tests, with no intermediate test failure observed. The independent offline evaluator passed 1,630 tests, with 25 skipped.
- click-010: the full public suite produced 29 failures and 1,481 passes; the final targeted shared-default regression still failed (one failed test). The independent offline evaluator had 69 failures, 1,518 passes, 24 skips, and zero collection errors. This is a submitted behavioral failure, not an infrastructure error.

## Recommendation for the user to decide

Freeze gpt-5.6-luna / low with CLI 0.153.1 and the current pinned M2 images for the experiment. The five Astra smokes all passed, whereas the four Luna attempts passed three and failed one. Luna therefore provides observed room for success improvement on development tasks. Four tasks with one new attempt each are a calibration sample, not a precise baseline success-rate estimate or proof that the ceiling is absent on confirmation tasks. The failure remains in the denominator. Do not pool Astra and Luna outcomes under one frozen configuration.

Keep success as the primary outcome. Add agent wall time as a prespecified key secondary outcome; do not make wall time, tool calls, and tokens all co-primary with success for this small pilot. Every attempt has exactly one CLI turn, so that count carries no useful variation. Tool-call counts depend on shell batching versus separate file edits, and tokens depend on context repetition and caching. Preserve both as diagnostic secondary outcomes. If an efficiency hypothesis is important enough to become co-primary, define its success constraint, failure handling, comparison rule, and multiplicity treatment before confirmation is opened. A useful prespecified wall-time sensitivity analysis assigns unsuccessful task-local attempts the 900-second cap; infrastructure failures remain missing and separately reported. Raw early failure time alone must not be credited as efficiency.

On the four matched development tasks, Astra's mean agent wall time was 91.586 seconds and Luna's was 68.316 seconds. Luna used 43 native calls versus 32, and 863,659 reported input tokens versus 573,051. This is descriptive: model, timing, cache conditions, tool strategy, and public verification behavior differed, and Luna failed one task. It does not demonstrate intervention lift or a causal model-speed comparison. The package-metadata collection issue should be documented as an environment/setup obstacle; any future environment change would require a new configuration/version and development revalidation before pooling outcomes.

## Measurement and accounting boundaries

Agent wall time is the adapter's monotonic time from CLI process launch through termination and model-metadata collection. It excludes container setup, source capture, offline evaluation, and cleanup. Separate evaluator times and all per-attempt usage fields are in [the machine-readable summary](../results/dev_ceiling_summary.json). CLI turns are completed top-level user turns, not internal model requests. Native calls count completed command/file-edit tool events, including failed calls; a compound shell command counts once. Internal Code Mode wrapper calls are not exposed and are not claimed as measured.

Token values are cumulative CLI usage counters, not unique task text or dollar cost. Cached input is included in input. Reasoning output is retained as separately reported; subset counters should not be added to their parents. All cache-write counters were zero. Failed pytest accounting inspects output as well as exit status, so a trailing shell command cannot hide a visible test failure. Evidence references and event/result hashes are retained.

The four scored development attempts and one native endpoint probe add five CLI invocations to the previous 14, giving 19 total. Catalog discovery used zero inference calls. Paid API spend is $0; subscription dollar cost is not measured. Docker timeouts were zero, usage limits did not block progress, and all arp-m2 containers and networks were removed. No further task attempt is authorized by this report.

If the four Luna baseline attempts are retained in a 48-run frozen Luna design, 44 scored runs remain. The original approximate 50-invocation ceiling has 31 slots left, so that full design would need a ceiling decision before later execution. The five Astra smokes remain calibration evidence. The $0 monetary cap is unchanged.

Repository verification: 92 tests passed and one Windows symlink test was skipped. The confirmation-split guard, explicit low override despite medium catalog default, and output-based intermediate-test parser have focused regression checks. An initial host test invocation hit an inaccessible shared Windows temp directory; tests passed with a workspace-local temporary directory. That host setup issue is separate from the development agent results.

Host-only evidence roots: artifacts/private/m2-linux-run-005, artifacts/private/dev-catalog-001, and artifacts/private/dev-ceiling-001. The original accepted evidence was not modified. The user authorized committing the calibration changes on October 2, 2026. The accepted M2 commit is intact. The original recommendations above remain an audit record; the approved outcome hierarchy below controls future work.

## Approved calibration configuration

October 2, 2026, America/Los_Angeles. Freeze gpt-5.6-luna / low with CLI 0.153.1 and the pinned M2 images. Success is primary. Recorded agent wall time is the prespecified key secondary outcome. Tool calls, tokens, and failed public test runs are diagnostic. No failure-penalty composite or additional co-primary outcome has been approved. Do not pool the five Astra smoke outcomes with the frozen Luna experiment. The intervention is not frozen; no confirmation execution is authorized.
