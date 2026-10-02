# Public snapshot checks

This is a plain-folder public snapshot prepared from tracked files only. It contains no Git directory or history. Company-specific research, outreach, and audit documents remain in the private source repository. No Git initialization, commit, push, or publication is part of snapshot preparation.

## Validate this folder

From the snapshot root:

```shell
python -B -m arp.check_phase5
python -B -m pytest -p no:cacheprovider --basetemp .pytest-tmp-local-001
```

The portable checker validates all Markdown document links, five findings, the two-minute demo length, report rendering and embedded-data consistency, recorded source hashes, and folder contents for forbidden paths and credential patterns. It uses no Git commands and does not export files or run inference. Software tests are checks of the implementation, not new agent attempts. Use a fresh basetemp directory for each test run.

For the maintainer's stronger comparison scan, supply the original local repository as read-only comparison input:

```shell
python -B -m arp.check_phase5 --comparison-root C:/arp
```

This additionally compares current local authentication values, secret-valued local environment entries, and accepted private gold/oracle payloads and added hidden-test blocks in memory. Credential values and private payloads are never printed or copied to the snapshot. Without those inputs, pattern scanning remains available, but exact-value/private-payload coverage is explicitly unavailable. The original Git-history scanner, `arp.check_publication`, requires the private evidence store and an initialized source repository; it is not a plain-folder validation command.

## Historical records and remaining boundary

`results/phase5_validation.json` and `results/publication_audit.json` are unchanged records of the original repository checkpoint. Their document hashes, excluded-document identifiers, commit IDs, and history counts refer to that original content. They are not claims about this edited snapshot. Current snapshot checks print their results separately and do not overwrite frozen records.

Public metadata intentionally includes task identities, upstream commit IDs, hashes, test names, aggregate verdicts, human labels, and selected agent command/output evidence. Private-path references are metadata, not private files. Published upstream identities let readers recover historical fixes, so this task set cannot become a new untouched held-out benchmark after disclosure.

The bundled report is portable. Complete raw-trace regeneration and audits require the private evidence store. Pattern and known-value scans cannot prove that every possible secret encoding is absent. This folder has no Git history to audit; recheck the eventual public tree and its full reachable history before publication. Publish only the reviewed snapshot, never a filesystem copy that includes private evidence or credentials.
