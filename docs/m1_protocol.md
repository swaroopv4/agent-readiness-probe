# M1 execution and review protocol

The authorized pilot uses one public repository and no model inference during M1. The miner exports each historical parent snapshot, separates production and test changes, and validates the task in fresh offline Docker containers. The Codex adapter belongs to M2 and is not implemented in M1.

## Reproduce the task checks

From the project directory, with Python 3.11+ and Docker Desktop's Linux engine available:

```powershell
python -m arp.m1 --output artifacts/private/m1-reproduction-001
```

Use a new output directory name for each reproduction. Existing evidence is never overwritten. This command obtains public source if needed, builds the evaluator image, audits the frozen 2026 history, and executes the behavioral shortlist until 12 candidates validate. Initial image and dependency preparation uses public network downloads. Every test execution then uses Docker network none. No API key or model request is needed.

The image pins the Python base digest, Python package versions, and the less package version. Each output records the actual image ID, package list, wheel SHA-256 hashes, source/archive hashes, production and oracle patch hashes, commands, test XML, stdout, stderr, runtime, and return codes. A future rebuild can fail if a public artifact disappears. Such failures are infrastructure failures, not agent performance.

Core tests can run separately with a fresh project-local temporary directory:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest --basetemp artifacts/private/coretests-review-001
```

The explicit temporary path avoids the observed permission failure in the host's default pytest temporary directory. Choose a new name to preserve prior test artifacts. The evaluator always disables automatic third-party pytest plugin discovery.

## Validity gates

Each accepted candidate must have three passing base runs, three consistently failing buggy-plus-oracle runs, and three passing gold-plus-oracle runs. Both test collection and case outcomes must match across repeats. Failures must occur in changed oracle files. Missing dependencies, collection errors, timeouts, and failing base or gold suites reject a candidate.

The supported full suite is the upstream default pytest test suite in the base snapshot. Upstream platform skips, expected failures, and default stress-test deselections remain in force and are recorded. The result is Linux/Python-3.11 validation, not validation on every supported platform or an exhaustive stress run. Three stable repetitions cannot prove that a test never flakes.

Pytest XML often omits an exception type attribute. The parser recognizes assertion messages and records other exception types instead of treating all failed tests as behavioral evidence. The sentinel-copy task explicitly allows ValueError as a behavioral failure because its contract requires copying and serialization to succeed. The color task allows TypeError as a failure because invalid inputs are required to raise ValueError instead. The pager ownership task allows a closed-stream ValueError as a behavioral failure. These narrow exception allowances are recorded for user review. Infrastructure exception types are not broadly whitelisted.

Only documentation side changes are omitted. A candidate that also changes build configuration, dependencies, non-Python test fixtures, or inseparable source artifacts is rejected. Gold production changes and the historical test delta are applied separately with Git's outer-repository discovery disabled. The prepared agent workspace has exactly B's files plus TASK.md, a new single-commit history, and no remotes. The host checker compares every file hash against B.

## Dataset selection and inference limits

The shortlist is purposive and behavioral. It favors tractable fixes with meaningful contracts and excludes spacing-only and error-wording-only changes. Its fixed order is stored in datasets/click_candidates.json. The manifest records structural eligibility and execution rejections across the frozen public-history population. This is not a representative random sample of Click maintenance work.

The 12 execution-valid tasks are assigned to four development tasks and eight confirmation tasks using seed 20260930. No difficulty stratification is claimed. Some fixes affect related subsystems or have ancestor snapshots containing earlier fixes. Attempts start fresh, but task clustering and historical exposure limit interpretation. Public model-training contamination cannot be ruled out. Failed public benchmark metadata queries are recorded as incomplete checks, never as evidence of zero overlap.

No confirmation agent outcomes exist during M1. The user can inspect confirmation oracles for validity, but must not use confirmation solutions to choose or author the later preparation intervention. The fix must be frozen from development evidence before confirmation trajectories are opened.

## Human acceptance and milestone boundary

After the batch completes, audit its artifacts and create the task review packet:

```powershell
python -m arp.check_m1 artifacts/private/m1-v7
```

The review packet and human_review.csv are host-only. For each task, the user checks specification clarity, assertion alignment, allowance for alternate correct implementations, and meaningful work. Blank human-review fields mean no human acceptance has occurred. Assistant reconstruction or self-review does not count as human annotation.

M1-v7 records the supplied user acceptance and rerun checks. The user authorized M2 after this commit. M2 must implement the Codex CLI adapter under the existing ChatGPT login, verify credential isolation and OpenAI-only transport egress, and enforce usage-limit stopping. No M2 live runs may start before those isolation and availability checks pass. M6 expansion remains unauthorized.

## Recover an interrupted freeze without Docker

The final manifest was recovered from the already completed m1-v4 executions. This mode compares input trees, production and oracle patches, exact commands, and the recorded image ID. It reparses the saved XML and refuses missing or incompatible evidence. It never builds an image or launches a container. The saved environment manifest is copied with its package and wheel hashes. Recorded execution durations remain the original durations, rather than being reported as new runs.

```powershell
$recordedCommand = Get-Content artifacts/private/m1-v4/candidates/f67c2bb6c2f055c1c7a57cd46c3697fc26a7742e/evidence/base-0/command.json -Raw | ConvertFrom-Json
python -m arp.m1 --output artifacts/private/m1-recorded-reproduction-001 --reuse-evidence artifacts/private/m1-v4 --image $recordedCommand[-4] --recorded-only
```

This audits existing executions. It does not verify the current Docker engine or claim fresh repeated runs. The engine was reachable before the original 108 executions, and the actual isolation probe was recorded then. After the interruption the engine was unavailable, including after an attempted restart of the existing installation. Fresh reproduction requires restoring the local engine. No paid fallback was selected.

The accepted review freeze and its reproduction command are documented in [m1_review.md](m1_review.md). Human decisions come from the supplied CSV, never from assistant inference. The checker rejects mismatched task IDs, split changes, missing reviewer identity, changed review metadata, and acceptance-count inconsistencies.
