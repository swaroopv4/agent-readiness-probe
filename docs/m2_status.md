# M2 status

October 1, 2026, America/Los_Angeles. **M2 is complete and accepted. All five development smokes passed the fresh offline evaluator.** No confirmation task, M3, M6, or outreach was started. Incremental paid API spend is $0; dollar cost is not measured.

## Migration and M1 integrity

The project is at C:/arp. Git fsck passes and f000b0b is an ancestor of the current checkout. The accepted m1-v7 manifest and human review are unchanged. The preserved artifacts/private/m1-v7 audit passes for all 12 accepted tasks, the four/eight split, production and oracle hashes, isolated workspaces, and all 108 evaluator evidence runs.

## Linux architecture and probes

The [architecture](m2_architecture.md) replaces the Windows sandbox, host tunnel, and MCP task broker. The agent image extends the validated evaluator image, adding Node 18.20.4 and Codex CLI 0.153.1 with its matching bundled Linux Code Mode host. Immutable image IDs are recorded in the [tracked summary](../results/m2_summary.json).

The non-root agent receives only the history-free buggy workspace plus TASK.md and the read-only Codex auth file. No hidden tests, gold patches, private experiment artifacts, host repository/history, or Docker socket are mounted. Capabilities are dropped, root is read-only, CPU/memory/PIDs/tmpfs are bounded, and the container is deleted after every attempt.

**Accepted limitation: credentials are visible inside the ephemeral agent container.** Read-only prevents changing the host file; it does not hide its contents from agent code. Credentials were not copied into the project or image, and the saved evidence contains no credential material.

The agent uses one Docker internal network whose only external exit is a separate exact-domain HTTPS CONNECT proxy. Allowed hosts are api.openai.com, chatgpt.com, and auth.openai.com on port 443; web search is disabled. The gate proved:

- github.com, pypi.org, and a proxied literal IP received CONNECT 403.
- Direct connections to 1.1.1.1 and 8.8.8.8 were unreachable; external DNS was blocked.
- The Codex endpoint returned TLS-verified 401 without auth, and saved login reported ChatGPT.
- An authenticated Codex probe ran successful native Linux commands to write and read a file.

Every probe passed before the valid smoke batch. The CLI selected **gpt-6-astra with low reasoning** using the saved login; the rollout identifies the client model and the fetched catalog records default reasoning. All five commands explicitly pin both settings. Backend served-model identity is not independently exposed. No provider/model fallback occurred.

The evaluator retains its validated image, hidden oracle, dependencies, and test command in a fresh network-none container. Hidden tests enter only evaluator workspaces. The trusted host checks immutable task files and captures production-only patches. The M2 task runner does not read or apply gold patches; the separate M1 integrity audit verifies their stored hashes.

## Development results

| Task | Repeat | Result | Passed | Skipped | Agent seconds |
|---|---:|---|---:|---:|---:|
| click-002 | 0 | resolved | 2000 | 25 | 64.078 |
| click-003 | 0 | resolved | 1953 | 25 | 85.344 |
| click-009 | 0 | resolved | 1630 | 25 | 56.656 |
| click-010 | 0 | resolved | 1587 | 24 | 160.265 |
| click-002 | 1 | resolved | 2000 | 25 | 71.265 |

All five have zero failures and evaluator errors. They made 38 native command calls. Total agent wall time: 437.608 seconds; evaluation: 42.235 seconds. CLI-reported smoke usage: 681,705 input tokens, including 549,632 cached input tokens, and 10,041 output tokens. Dollar cost is not measured.

This is five development attempts on four tasks with one repeat. It supplies no confirmation score or intervention-effect estimate. M1's precise statements, purposive selection, unknown training exposure, and small-sample limitations remain.

## Retained diagnostics and limits

The [Windows stop record](m2_windows_status.md) and private evidence are preserved. Linux recovery retained a subnet setup error, a metadata-capture failure after successful endpoint inference, a workspace-copy readiness race before task CLI launch, and four unavailable-tool-runtime launches. Three unchanged submissions from that failed environment were evaluated; the fourth CLI was halted. Those are infrastructure launches, not scored task failures. The final gate now requires actual successful Linux commands before tasks.

M2 totals 14 CLI invocations: five valid smokes, three connectivity/tool probes, four excluded Linux task infrastructure launches, and two earlier Windows aborts. There are 36 slots left under the original approximate 50-invocation ceiling and 43 scored runs left in the 48-run design. Completing that later design requires reviewing the ceiling; no later launch is authorized now.

The valid Linux batch had zero Docker timeouts and no usage-limit stop. Two Docker timeouts forbid further live Docker operations; quota/usage-limit errors stop immediately. Agent wall time is capped at 900 seconds and evaluator time at 300 seconds. The prompt requests 120-second shell commands; native CLI timeouts are not claimed as a separately enforced 120-second security boundary.

## Verified checkpoint

Core checks: **88 passed, one skipped** (Windows host symlink privilege). M1 and M2 evidence audits pass. The M2 audit checks plan order, input bytes, mounts/privileges, model/web-search settings, event/patch hashes, parsed JUnit, immutable evaluator files, and offline commands. Cleanup found no M2 containers or networks.

Host-only evidence is in artifacts/private/m2-linux-run-005: config.json, probes/, ledger.jsonl, per-attempt patches and evaluations, audit.json, cleanup.json, and proxy.jsonl. Earlier Linux diagnostics remain in m2-linux-run-001 through m2-linux-run-004.

Read-only audits:

    python -m arp.check_m1 artifacts/private/m1-v7
    python -m arp.check_m2 artifacts/private/m2-linux-run-005

**Stop here for the user's M2 review.** Confirmation work, M3, optional M6, and outreach remain unauthorized.

## Post-M2 development ceiling check

M2 was committed as eefd24a before calibration. The authorized gpt-5.6-luna / low check passed three of four development tasks and failed click-010. No confirmation task or M3 work was launched. Full attempt metrics, live login catalog, accounting, and recommendations are in [dev_ceiling_check.md](dev_ceiling_check.md). On October 2, 2026, the user approved freezing gpt-5.6-luna / low: success primary, recorded wall time key secondary, and tool calls, tokens, and failed public test runs diagnostic. Intervention freeze and confirmation execution remain pending approval. Paid API spend remains $0, with 19 total CLI invocations including probes and earlier aborts.

## Intervention proposal pending approval

Calibration is committed as e4b0637. The setup-only AGENTS draft and proposed reduced M3 scope (8 baseline confirmation attempts, 12 human labels: 4 development calibration plus 8 confirmation evaluation) are in [m3_plan.md](m3_plan.md). The draft commands passed mechanical public-test checks on four development snapshots with zero inference calls. The intervention is not frozen and no confirmation task has run.

## Approved M3 transition

October 2, 2026. The user approved freezing setup-v1 exactly, the identical common prompt sentence, the reduced 8-baseline/12-human-label M3 plan, and retaining the eight M3 baselines as M5 baseline repeat 1 without reruns. M3 baselines precede intervention runs; remaining M5 attempts will be interleaved in frozen randomized order. See [m3_plan.md](m3_plan.md) and [m3_freeze.json](../results/m3_freeze.json). Freeze and commit precede confirmation execution.

## M3 baseline batch and labeling checkpoint

M3 freeze commit 19b880e preceded eight baseline confirmation attempts. Six passed and two failed; all are retained as M5 baseline repeat 1 without reruns. The 12-row human labeling sheet is ready, with zero human labels supplied. See [m3_status.md](m3_status.md). Intervention and rubric remain fixed; no M5 intervention attempt has run. Stop for human labeling.

## M3 human review completed

Swaroop subsequently supplied all twelve labels. Held-out primary agreement is 6/8, kappa 0.428571, and secondary set agreement 7/8. The rule abstained on both confirmation failures. See [human review and agreement](m3_human_review.md). M3 is complete under the approved reduced scope; the frozen intervention and rules remain unchanged. Stop before M4.

## Approved M5 completion before M4

October 2, 2026. The user approved the reordered milestone execution and all forty remaining scored slots across twelve tasks. M5 now has all 48 outcomes, reusing eight M3 baselines without reruns. Confirmation success is 12/16 in both arms, delta 0 pp; the degenerate bootstrap triggers the Hoeffding 95% interval [-96.03, +96.03] pp, so the result is inconclusive. Wall-time delta is +2.662s, paired bootstrap 95% [-3.121, +10.538]s, also inconclusive. All-task results are descriptive (baseline 18/24, intervention 19/24); only development task click-010 improved. See [M5 analysis](m5_results.md).

The separate M5 order amendment records task-block randomization seed 20261002 while preserving all frozen configuration and M3 human labels. The authorized forty runs plus one native gate bring lifetime CLI invocations to 69, replacing the earlier approximate 50 planning ceiling. Incremental paid API spend is $0. There were no infrastructure exclusions, usage-limit stops, or Docker timeouts; owned resources are cleaned up. Stop for M5 review before M4.
