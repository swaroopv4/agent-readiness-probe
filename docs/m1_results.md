# M1 results

September 30, 2026. M1 mechanical checks pass. Twelve historical Click tasks have stable base, buggy-with-oracle, and gold-with-oracle evidence. Swaroop accepted all 12 tasks with approved statement revisions in m1-v7. No Codex agent inference, failure-label study, readiness score, or intervention experiment has run.

## Observed checks

The miner audited 397 commits in the frozen 2026 history. Seventy-one met structural eligibility. Filters rejected 178 non-single-parent commits, 129 without both production and test changes, 11 with deleted or renamed files, seven with inseparable non-documentation changes, and one above the production-size cap. A purposive behavioral shortlist contains 14 candidates. Its first 12 validated, so the two backups were not needed. The editor-argument backup is explicitly excluded because its mock oracle rejects an otherwise valid explicit shell=False implementation.

Each task has three fresh passing base executions, three consistently failing buggy-with-oracle executions, and three passing gold-with-oracle executions. The accepted set has 108 actual offline container executions. Their recorded durations total 928.831 seconds, excluding source preparation, image builds, and host audits. Earlier diagnostic batches contain another 37 completed executions, giving 145 unique completed task executions overall. An interrupted backup without a complete result record is excluded from that count. Copies of evidence in later freezes are not additional executions.

The original 39 core pytest tests passed after the final correction. The accepted m1-v7 version passes all 48 current core tests. The artifact audit reparsed all saved test XML, verified patch and statement hashes, checked stable outcomes and changed-file failures, and compared every agent workspace file with its base snapshot. Each agent snapshot has one clean Git commit, no remotes, and no original base or fix commit objects. It contains the base snapshot and TASK.md only.

The frozen split uses seed 20260930. Counts below describe each of three identical repetitions per state. Skips and expected failures remain in the underlying XML. These are task-validity results, not agent successes.

| Task | Split | Requirement | Base passed | Buggy failed | Gold passed |
|---|---|---|---:|---:|---:|
| click-001 | Confirmation | Short-help abbreviations and word boundaries | 2070 | 6 | 2092 |
| click-002 | Development | Sentinel copying and serialization | 1991 | 3 | 2000 |
| click-003 | Development | Stable help-option alias order | 1940 | 4 | 1953 |
| click-004 | Confirmation | Consistent color-value validation | 1685 | 38 | 1749 |
| click-005 | Confirmation | Complete CSI escape handling | 1749 | 30 | 1894 |
| click-006 | Confirmation | Prompt color follows output policy | 1677 | 2 | 1681 |
| click-007 | Confirmation | Version lookup from import names | 1658 | 2 | 1661 |
| click-008 | Confirmation | Borrowed pager output stays open | 1654 | 2 | 1656 |
| click-009 | Development | Parameter source during conversion and callbacks | 1624 | 3 | 1630 |
| click-010 | Development | Competing flags and source precedence | 1510 | 18 | 1587 |
| click-011 | Confirmation | Safe feedback for hidden prompts | 1494 | 2 | 1497 |
| click-012 | Confirmation | Serialized multi-value defaults | 1436 | 2 | 1441 |

## Environment and isolation

Source: pallets/click, BSD-3-Clause, head 06b2a678741131fd577ce170e23e5ca0aeba0309. Evaluator image ID: sha256:506974e3505483d01d749cfc2cffc6bae2e3d375f2f5ff69d241bc353b630cb7. The pinned base digest and dependency versions are in the Dockerfile. The private environment manifest records installed versions and wheel hashes.

Before the original executions, Docker engine 28.5.1 was reachable and C had about 89.1 GiB free. The actual [isolation probe](../artifacts/private/isolation-probe-v1/result.json) recorded UID 1000, no effective capabilities, no-new-privileges, no external route, a blocked external socket, and a failed write to the read-only input mount. The shared image contained no installed Click task code. Task execution commands also specify network none, read-only root, dropped capabilities, bounded temporary storage, and CPU, memory, and process limits.

After the interruption, Docker's engine was unavailable. Starting the existing Desktop installation did not restore it. The final disk observation was 127.22 GiB free. The m1-v6 freeze reused all 108 compatible executions from m1-v4, with zero fresh Docker executions. Reuse checked input tree hashes, patch bytes, exact commands, and image identity, then reparsed XML. Recorded-only mode refuses incompatible or missing evidence. This recovery audits preserved executions and does not establish current engine health. Fresh reproduction requires restoring Docker.

## Corrections and validity limits

Early diagnostic runs exposed missing less, a non-executable temporary mount, and Git discovery of the outer repository. The evaluator now includes pinned less, uses an executable bounded tmpfs, and applies patches with outer Git discovery disabled. The final parser handles pytest XML without a failure-type attribute. Three declared behavioral exception cases remain narrow: sentinel copying fails with ValueError, color validation raises TypeError instead of the required ValueError, and pager misuse closes a borrowed stream. These contracts and allowances need user review. They are not a general exception whitelist.

The final snapshot audit found Windows CRLF in TASK.md while its recorded statement hash used LF. The writer now uses canonical LF, all 12 snapshots were rebuilt, and previous snapshots were preserved. Gold, oracle, source trees, and original test outcomes were unchanged. The audit and core suite then passed.

The statements were reconstructed by the assistant from public changes and regression tests. They were accepted by Swaroop after specification-to-oracle review. Public benchmark metadata queries failed or timed out, so overlap checks are incomplete and model exposure remains unknown. Selection favors tractable behavioral tasks, and related subsystems and ancestor fixes limit independence. The supported upstream default Linux/Python-3.11 suite retains platform skips, expected failures, and default stress-test deselection. Three stable repeats do not prove absence of flakiness or correctness on every platform. Gold passing does not prove that every alternate correct implementation can pass.

## Cost and next gate

Incremental paid API spend is $0. No model inference request was made. Token usage and dollar cost are not measured. The approved future experiment remains 48 scored attempts across 12 tasks, with at most two infrastructure retries, using Codex CLI and the existing ChatGPT login. Confirmation has eight task clusters, so intervals will be wide. Rules precede the user's human labels. Paid judges and provider switching are prohibited.

See the [accepted task packet](../artifacts/private/m1-v7/review_packet.md) and supplied [human_review.csv](../artifacts/private/m1-v7/human_review.csv). All 12 acceptance decisions are recorded with reviewer Swaroop. Confirmation solutions are for validity review and must not guide the later intervention. The [protocol](m1_protocol.md) contains reproduction and audit commands. The [tracked summary](../results/m1_summary.json) and [host-only manifest](../datasets/click_m1_manifest.json) contain no oracle content.

M1 human review is complete. The Codex adapter, its OpenAI-only transport and credential boundary, and live smoke attempts belong to M2. M2 is authorized next, with Docker and egress checks before live attempts. Optional M6 is not authorized.

## Accepted m1-v7 review freeze

Seven statements changed under explicit user approval. Swaroop accepted all 12 tasks. Candidate files, historical tests, gold patches, recorded execution evidence, and the frozen split remain identical to m1-v6. Only statements, their isolated snapshots, acceptance metadata, and review documents were revised. The current freeze does not count evidence copies as new executions.

Statements were revised to match hidden assertions before any agent run. Revised tasks are more precisely specified than typical real-world tickets. The click-005 statement names _ansi_re because the oracle inspects it directly. click-010 remains development only and includes an unrelated duplicate-option warning check. These limits must accompany later results. See [review provenance](m1_review.md).
