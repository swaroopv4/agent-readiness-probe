# Revised resource checkpoint

September 30, 2026, America/Los_Angeles. Status: user approved the $0 plan, accepted all 12 tasks, and authorized M2 after the m1-v7 commit. This supersedes the previous paid-provider plan. M2 Linux work is complete: five development smokes passed. Infrastructure launches and connectivity/tool probes remain accounted for; see [M2 status](m2_status.md). Incremental paid API spend is $0. Per-run dollar cost is not measured.

## Authorized plan

Use Codex CLI headless through `codex exec`, authenticated with the user's existing ChatGPT plan. No paid API, Anthropic key, paid judge, purchased credits, cloud VM, or provider fallback is allowed. If a step requires spending, stop and ask. If Codex usage limits block progress, stop and tell the user. Do not switch providers.

Mine one public repository, initially pallets/click or a documented replacement if its history is insufficient. Target 12 accepted tasks, four development and eight confirmation. Two arms with two attempts each gives 48 scored runs. M2 smoke attempts count toward that plan when the baseline is unchanged. Reserve at most two infrastructure retries for an operational ceiling of about 50, with aborted attempts retained. Optional Codex labels would need accounting within the same allowance. M6 is optional future work and must not start.

Failure labeling uses rules followed by the user's own human review. No paid LLM judge. A secondary Codex headless label may use the same login if useful. The confirmation sample is eight tasks, so intervals will be wide. Keep the paired task-cluster analysis and disclose the small sample.

## Accounts and resources

| Resource | Credential | Incremental cash and status |
|---|---|---|
| Existing ChatGPT plan and Codex CLI | Existing saved ChatGPT login, outside the project | No new purchase authorized. CLI 0.153.1 reports logged in using ChatGPT |
| Public GitHub source history | None for anonymous clone | $0 direct charge. One active repository |
| Docker Desktop local Linux engine | No probe credential | Engine reachable before original M1 runs, unavailable after interruption. No paid upgrade authorized |
| Public container registry and PyPI | None for public downloads | No paid service. Download during environment preparation, before offline evaluation |
| Python, Git, local disk and CPU | Existing installation | No new hardware or cloud allocation |
| User human review | No API key | Actual user review required. Labor and inter-human agreement are not measured |
| Devin adapter stub | None | No network, subscription, or paid session |

No experiment API key is required. Never put auth.json, OAuth tokens, API keys, or host credential stores in Git, images, or logs. The October 1 Linux revision explicitly permits mounting saved ChatGPT auth read-only into the ephemeral agent container; credentials are visible there, an accepted limitation. API-key authentication is prohibited; verify ChatGPT login before runs. The tracked .env.example contains only non-secret policy settings.

The official [headless documentation](https://developers.openai.com/codex/noninteractive) documents JSONL events and reuse of saved CLI authentication. The official [authentication documentation](https://developers.openai.com/codex/auth) distinguishes subscription login from usage-based API keys. Record CLI-reported usage where present. Missing counters and dollar cost remain `not measured`, rather than inferring a dollar value from tokens.

## Verified before M1

| Resource | September 30 observation |
|---|---|
| Docker engine | Reachable, 28.5.1, Linux amd64, Docker Desktop 4.48.0, desktop-linux context |
| C free disk | About 89.1 GiB at the latest check, above the user's roughly 80 GB estimate |
| Python | 3.11.9 |
| pytest | 9.0.3 on the host |
| Git | 2.55.0 |
| Codex | 0.153.1, logged in using ChatGPT. No model inference invoked |
| Host memory and CPU | Previously observed 11.8 GiB RAM and eight logical processors |
| Scheduling | Serial containers, two CPU cores, 3 GiB RAM, five-minute evaluator cap |

Preserve at least 10 GiB free and check disk after M1. Base images and public dependencies may be downloaded during setup. Evaluator runs must use --network none. The Linux agent remains isolated from gold patches, hidden tests, source history, private experiment artifacts, the Docker socket, and arbitrary external access. Saved read-only ChatGPT auth is the explicitly accepted credential exception. Its only exit is the allowlisted Docker proxy. M2 proved this boundary and Linux execution before the valid batch.

## Limits and remaining gates

The global incremental spending cap is $0. Existing subscription capacity is finite and availability is not guaranteed. Dollar cost is not measured. Use 15-minute agent limits, five-minute evaluator limits, and one concurrent task. Request 120-second shell commands; native CLI timeouts are not independently enforced as a separate 120-second boundary. Do not claim controls the pinned CLI cannot enforce. The host runner must persist attempt counts, cancellations, usage-limit stops, and missing usage.

M1 completed three base runs, three buggy-with-oracle runs, and three gold-with-oracle runs for each of 12 execution-valid candidates. The 108 runs total 928.831 seconds of recorded execution time. Another 37 completed diagnostic executions are retained. Human effort and end-to-end runtime are not measured. These runs used local Docker and no paid inference. Swaroop accepted all 12 tasks in m1-v7.

The cheaper fallback is to stop and preserve completed artifacts when plan limits prevent progress. There is no alternate provider or paid fallback. Reproducible fixtures can test software but cannot be reported as agent performance.

The zero-budget revision was committed before implementation as eda55f2. M1-v7 checks and human review now pass. M2 is authorized after that commit, starting with Docker verification. Stop if Docker is unavailable or Codex limits block progress, and otherwise stop after M2 for review. No later milestone is authorized.

## M1 recovery update

The original Linux engine was verified before validation, and 108 completed task executions are preserved in m1-v4. Core tests and the final manifest audit use local Python. After the interruption no M1 process remained, the Docker engine was unavailable, and an attempted restart did not restore it. The current C check reports about 127.4 GiB free. The final freeze uses verified existing evidence in recorded-only mode and launches no new containers. This does not replace a fresh engine check for later execution. No paid API, new account, credits, or provider fallback was used.

## Historical Windows M2 resource stop

October 1, 2026. M1-v7 is committed as f000b0b. M2 has zero completed smoke attempts, two aborted CLI invocations, and one container-setup abort before CLI launch. Docker task execution and forced cleanup timed out. The later read-only engine check responds with 28.5.1 Linux and no remaining arp task container. C has 123.9 GiB free. No provider fallback, paid API, purchased capacity, or paid judge was used. Incremental paid API spend remains $0. Token usage and per-run dollar cost are not measured. The two infrastructure CLI aborts are preserved against the approximately 50-invocation ceiling. Live work stops here pending the user resuming M2. See [M2 status](m2_status.md).

## Linux M2 review checkpoint

October 1, 2026. All five development smokes passed using gpt-6-astra, low reasoning, and CLI 0.153.1. Network and native-tool probes passed; containers and networks were removed. Saved login is mounted read-only and visible inside each ephemeral agent container by explicit user acceptance. Paid API spend is $0; CLI usage is recorded and dollar cost is not measured. Total CLI invocations are 14: five valid smokes, three probes, four excluded Linux task infrastructure launches, and two earlier Windows aborts. Thirty-six slots remain under the original approximate 50 ceiling, versus 43 remaining scored runs; a complete later experiment needs ceiling review. No M3, confirmation, M6, or outreach was started. Stop for M2 review.

## Approved M5 completion before M4

October 2, 2026. The user approved the reordered milestone execution and all forty remaining scored slots across twelve tasks. M5 now has all 48 outcomes, reusing eight M3 baselines without reruns. Confirmation success is 12/16 in both arms, delta 0 pp; the degenerate bootstrap triggers the Hoeffding 95% interval [-96.03, +96.03] pp, so the result is inconclusive. Wall-time delta is +2.662s, paired bootstrap 95% [-3.121, +10.538]s, also inconclusive. All-task results are descriptive (baseline 18/24, intervention 19/24); only development task click-010 improved. See [M5 analysis](m5_results.md).

The separate M5 order amendment records task-block randomization seed 20261002 while preserving all frozen configuration and M3 human labels. The authorized forty runs plus one native gate bring lifetime CLI invocations to 69, replacing the earlier approximate 50 planning ceiling. Incremental paid API spend is $0. There were no infrastructure exclusions, usage-limit stops, or Docker timeouts; owned resources are cleaned up. Stop for M5 review before M4.

## M4 recorded-data report checkpoint

October 2, 2026. The user authorized descriptive mechanism diagnostics and the single-file readiness report after M5. [M4 is ready for review](m4_results.md); the primary and wall-time results remain inconclusive. This stage used local saved-evidence audits, Python tests and headless browser rendering only. No additional agent, evaluator, judge, Docker or paid API operation occurred. Lifetime CLI invocations remain 69 and incremental paid API spend remains $0. Token diagnostics are recorded; subscription dollar cost is not measured. No frozen configuration, outcomes or human labels changed. Stop for M4 review; no new candidate intervention, M6, publication or outreach is authorized.

## Approved Phase 4 and Phase 5 checkpoint

October 2, 2026. M4 was approved. Three reinforcement audits and the visitor README, five findings, two-minute demo, unsent outreach draft and pre-publish check are complete pending review. These phases use saved evidence and local software/browser checks only, with public-site reads for offering verification. No model, evaluator, judge, Docker, paid API, publication or messaging operation occurred. Lifetime CLI invocations remain 69 and paid API spend $0. Frozen results, labels and treatment remain unchanged. Company-specific audit logs and outreach remain in the private source repository. See [findings](findings.md) and [publication check](pre_publish_check.md). Stop for review.
