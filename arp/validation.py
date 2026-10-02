"""Fresh offline Docker executions and strict task validity gates."""
from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Execution:
    state: str
    repeat: int
    returncode: int
    seconds: float
    collected: int
    passed: int
    skipped: int
    failures: tuple[str, ...]
    failure_types: tuple[str, ...]
    errors: tuple[str, ...]
    outcomes: tuple[tuple[str, str], ...]
    timed_out: bool = False

    def record(self) -> dict:
        return asdict(self)


def parse_junit(path: Path, state: str, repeat: int, returncode: int,
                seconds: float, timed_out: bool = False) -> Execution:
    outcomes = []
    failures = []
    failure_types = []
    errors = []
    passed = skipped = 0
    if path.exists():
        # This is local trusted historical-test evidence, never an agent verdict.
        for case in ET.parse(path).getroot().iter("testcase"):
            node = case.get("classname", "") + "::" + case.get("name", "")
            failure, error, skip = case.find("failure"), case.find("error"), case.find("skipped")
            if failure is not None:
                failures.append(node)
                kind = failure.get("type", "")
                if not kind:
                    message = failure.get("message", "").strip()
                    if message.startswith(("AssertionError:", "assert ")):
                        kind = "AssertionError"
                    elif message.startswith(("Failed:", "DID NOT RAISE")):
                        kind = "Failed"
                    else:
                        match = re.match(r"([A-Za-z_][A-Za-z_0-9.]*):", message)
                        kind = match.group(1) if match else "unknown"
                failure_types.append(kind)
                outcome = "failed"
            elif error is not None:
                errors.append(node)
                outcome = "error"
            elif skip is not None:
                skipped += 1
                outcome = "skipped"
            else:
                passed += 1
                outcome = "passed"
            outcomes.append((node, outcome))
    return Execution(state, repeat, returncode, seconds, len(outcomes), passed,
                     skipped, tuple(sorted(failures)), tuple(sorted(failure_types)),
                     tuple(sorted(errors)), tuple(sorted(outcomes)), timed_out)


def docker_command(image: str, workspace: Path, evidence: Path, name: str) -> list[str]:
    script = (
        "cp -a /input /tmp/workspace && cd /tmp/workspace && "
        "python -m pip install --no-index --no-deps --no-build-isolation "
        "--target /tmp/site . > /tmp/install.log 2>&1 || "
        "{ cat /tmp/install.log; exit 90; }; "
        "PYTHONPATH=/tmp/workspace/src:/tmp/site python -m pytest -q --tb=short "
        "-p no:cacheprovider --junitxml=/evidence/junit.xml tests"
    )
    return [
        "docker", "run", "--name", name, "--rm", "--network", "none", "--read-only",
        "--user", "1000:1000", "--cpus", "2", "--memory", "3g", "--pids-limit", "256",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--tmpfs", "/tmp:rw,exec,size=768m,mode=1777", "--workdir", "/tmp",
        "--mount", f"type=bind,source={workspace.resolve()},target=/input,readonly",
        "--mount", f"type=bind,source={evidence.resolve()},target=/evidence",
        "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "-e", "PIP_DISABLE_PIP_VERSION_CHECK=1",
        "-e", "PYTHONHASHSEED=0", "-e", "TZ=UTC", image, "sh", "-c", script,
    ]


def execute(image: str, workspace: Path, evidence: Path, state: str, repeat: int,
            timeout: int = 300) -> Execution:
    evidence.mkdir(parents=True, exist_ok=False)
    name = "arp-m1-" + uuid.uuid4().hex
    command = docker_command(image, workspace, evidence, name)
    (evidence / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    start = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code, stdout, stderr = 124, exc.stdout or b"", exc.stderr or b""
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, check=False, timeout=30)
    seconds = time.monotonic() - start
    (evidence / "stdout.txt").write_bytes(stdout)
    (evidence / "stderr.txt").write_bytes(stderr)
    parsed = parse_junit(evidence / "junit.xml", state, repeat, code, seconds, timed_out)
    (evidence / "result.json").write_text(json.dumps(parsed.record(), indent=2), encoding="utf-8")
    return parsed


def validity_reason(runs: list[Execution], oracle_files: tuple[str, ...], repeats: int = 3,
                    behavioral_exception_types: tuple[str, ...] = ()) -> str | None:
    by_state = {state: [run for run in runs if run.state == state] for state in ("base", "buggy", "gold")}
    if any(len(values) != repeats or {r.repeat for r in values} != set(range(repeats))
           for values in by_state.values()):
        return "incomplete_repeated_validation"
    for state, values in by_state.items():
        if any(run.timed_out or run.collected == 0 or run.errors for run in values):
            return f"{state}_infrastructure_or_collection_failure"
        if any(run.outcomes != values[0].outcomes or run.failure_types != values[0].failure_types for run in values[1:]):
            return f"{state}_unstable_outcomes"
        if state in {"base", "gold"} and any(run.returncode != 0 or run.failures for run in values):
            return f"{state}_suite_does_not_pass"
        if state == "buggy":
            if any(run.returncode != 1 or not run.failures for run in values):
                return "oracle_does_not_discriminate"
            prefixes = tuple(name[:-3].replace("/", ".") + "::" for name in oracle_files)
            if any(not node.startswith(prefixes) for node in values[0].failures):
                return "failure_outside_changed_oracle"
            allowed = {"AssertionError", "Failed", *behavioral_exception_types}
            if any(kind not in allowed for kind in values[0].failure_types):
                return "oracle_failure_not_behavioral_assertion"
    if by_state["buggy"][0].collected != by_state["gold"][0].collected:
        return "gold_changes_test_collection"
    return None
