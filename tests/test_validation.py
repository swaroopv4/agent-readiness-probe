from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from arp.validation import Execution, docker_command, parse_junit, validity_reason


def executions() -> list[Execution]:
    result = []
    for state in ("base", "buggy", "gold"):
        for repeat in range(3):
            failed = state == "buggy"
            result.append(Execution(state, repeat, int(failed), 1.0, 1, int(not failed), 0,
                ("tests.test_core::test_regression",) if failed else (),
                ("AssertionError",) if failed else (), (),
                (("tests.test_core::test_regression", "failed" if failed else "passed"),)))
    return result


def test_complete_behavioral_validation():
    assert validity_reason(executions(), ("tests/test_core.py",)) is None


@pytest.mark.parametrize("change,expected", [
    ({"returncode": 1, "failures": ("tests.test_core::test_regression",)}, "gold_suite_does_not_pass"),
    ({"errors": ("tests.test_core::test_import",)}, "gold_infrastructure_or_collection_failure"),
    ({"timed_out": True}, "gold_infrastructure_or_collection_failure"),
    ({"collected": 0}, "gold_infrastructure_or_collection_failure"),
])
def test_failed_gold_never_validates(change, expected):
    runs = executions()
    runs[6:] = [replace(r, **change) for r in runs[6:]]
    assert validity_reason(runs, ("tests/test_core.py",)) == expected


def test_incomplete_validation_rejected():
    assert validity_reason(executions()[:-1], ("tests/test_core.py",)) == "incomplete_repeated_validation"


def test_unstable_outcomes_rejected():
    runs = executions()
    runs[4] = replace(runs[4], outcomes=(("tests.test_core::test_regression", "passed"),))
    assert validity_reason(runs, ("tests/test_core.py",)) == "buggy_unstable_outcomes"


def test_import_failure_is_not_a_regression():
    runs = executions()
    runs[3:6] = [replace(r, failure_types=("ImportError",)) for r in runs[3:6]]
    assert validity_reason(runs, ("tests/test_core.py",)) == "oracle_failure_not_behavioral_assertion"


def test_unrelated_failure_rejected():
    runs = executions()
    runs[3:6] = [replace(r, failures=("tests.test_other::test_old",)) for r in runs[3:6]]
    assert validity_reason(runs, ("tests/test_core.py",)) == "failure_outside_changed_oracle"


def test_nondiscriminating_oracle_rejected():
    runs = executions()
    runs[3:6] = [replace(r, returncode=0, failures=(), failure_types=()) for r in runs[3:6]]
    assert validity_reason(runs, ("tests/test_core.py",)) == "oracle_does_not_discriminate"


def test_junit_distinguishes_fail_skip_and_collection_error(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite><testcase classname="tests.test_core" name="ok"/>'
        '<testcase classname="tests.test_core" name="bad"><failure type="AssertionError"/></testcase>'
        '<testcase classname="tests.test_core" name="skip"><skipped/></testcase>'
        '<testcase classname="tests.test_core" name="import"><error/></testcase></testsuite></testsuites>')
    run = parse_junit(junit, "buggy", 0, 1, 2.0)
    assert (run.collected, run.passed, run.skipped) == (4, 1, 1)
    assert run.failures == ("tests.test_core::bad",)
    assert run.errors == ("tests.test_core::import",)


def test_evaluator_command_blocks_network_and_limits_mounts(tmp_path):
    workspace, evidence = tmp_path / "base", tmp_path / "evidence"
    command = docker_command("sha256:fixture", workspace, evidence, "arp-test")
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--user") + 1] == "1000:1000"
    mounts = [command[i + 1] for i, value in enumerate(command) if value == "--mount"]
    assert len(mounts) == 2
    assert mounts[0].endswith("target=/input,readonly")
    assert not any("docker.sock" in part or "auth.json" in part for part in command)
    script = command[-1]
    assert "--no-index" in script and "--no-deps" in script and "--no-build-isolation" in script


def test_real_pytest_junit_without_type_attribute(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite>'
        '<testcase classname="tests.test_core" name="assertion"><failure message="assert False is True"/></testcase>'
        '<testcase classname="tests.test_core" name="expanded"><failure message="AssertionError: expected match"/></testcase>'
        '<testcase classname="tests.test_core" name="exception"><failure message="PermissionError: denied"/></testcase>'
        '</testsuite></testsuites>')
    run = parse_junit(junit, "buggy", 0, 1, 2.0)
    assert run.failure_types == ("AssertionError", "AssertionError", "PermissionError")


def test_unexpected_copy_exception_requires_declared_behavioral_contract():
    runs = executions()
    runs[3:6] = [replace(r, failure_types=("ValueError",)) for r in runs[3:6]]
    assert validity_reason(runs, ("tests/test_core.py",)) == "oracle_failure_not_behavioral_assertion"
    assert validity_reason(runs, ("tests/test_core.py",), behavioral_exception_types=("ValueError",)) is None
