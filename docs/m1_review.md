# M1 human review and accepted version

The user explicitly accepted all 12 tasks under reviewer name Swaroop. This is human acceptance supplied in the conversation, not assistant self-review. The review timestamp records when those supplied decisions were entered. Separate checklist ratings were not supplied and remain blank.

Tasks click-002, click-003, click-006, click-008, and click-012 were accepted without statement changes. Tasks click-001, click-004, click-005, click-007, click-009, click-010, and click-011 were accepted with the exact statement revisions approved in the conversation. The accepted ledger is datasets/m1_human_review.csv, copied to human_review.csv in m1-v7.

For click-005, the revised statement names _ansi_re because the hidden test inspects it directly. For click-010, the task remains development only and its oracle includes an unrelated duplicate-option warning check. Neither test was changed or removed.

Statements were revised to match hidden assertions before any agent run. Revised tasks are more precisely specified than typical real-world tickets. This limits transfer to ordinary maintenance tickets and must accompany later readiness or intervention results. Confirmation specification review does not permit using confirmation solutions to author the intervention.

The m1-v7 freeze copies the historical candidates and evidence unchanged, rebuilds the base-only TASK.md snapshots with canonical LF, preserves the four/eight split, and records statement hashes and actual human decisions. No new container validation or model request is claimed. The older m1-v6 remains intact as the pending-review version. Core tests and the M1 checker are rerun for the accepted version.

To reproduce the accepted review freeze from preserved local artifacts, use a fresh output directory:

```powershell
python -m arp.review_m1 artifacts/private/m1-v6 artifacts/private/m1-review-reproduction-001 datasets/m1_human_review.csv
```

M2 is now authorized under the same zero-dollar cap. Its first gate is the local Docker engine. If Docker is unavailable, stop before live attempts and report that limitation. Codex usage-limit failures also stop the batch, with no provider fallback. M6 remains unauthorized.
