from __future__ import annotations

import json
from pathlib import Path

import pytest

from arp.m1 import reusable_execution
from arp.validation import docker_command


@pytest.fixture
def previous_execution(tmp_path: Path):
    previous, workspace = tmp_path / "previous", tmp_path / "current"
    old_input, evidence = previous / "base", previous / "evidence/base-0"
    for directory in (old_input, evidence, workspace):
        directory.mkdir(parents=True)
    (old_input / "source.py").write_text("buggy source")
    (workspace / "source.py").write_text("buggy source")
    (previous / "gold.patch").write_bytes(b"gold")
    (previous / "oracle.patch").write_bytes(b"oracle")
    command = docker_command("sha256:fixture", old_input, evidence, "arp-fixture")
    (evidence / "command.json").write_text(json.dumps(command))
    for name in ("result.json", "junit.xml", "stdout.txt", "stderr.txt"):
        (evidence / name).write_text("complete evidence")
    return previous, workspace, evidence


def test_reuse_identical_recorded_execution(previous_execution):
    previous, workspace, evidence = previous_execution
    assert reusable_execution(previous, "base", evidence, "sha256:fixture", workspace, b"gold", b"oracle")


@pytest.mark.parametrize("changed", ["image", "input", "oracle", "command", "incomplete"])
def test_changed_or_incomplete_execution_never_reused(previous_execution, changed):
    previous, workspace, evidence = previous_execution
    image = "sha256:fixture"
    if changed == "image":
        image = "sha256:other"
    elif changed == "input":
        (workspace / "source.py").write_text("different source")
    elif changed == "oracle":
        (previous / "oracle.patch").write_bytes(b"other oracle")
    elif changed == "command":
        command = json.loads((evidence / "command.json").read_text())
        command[command.index("--network") + 1] = "bridge"
        (evidence / "command.json").write_text(json.dumps(command))
    else:
        (evidence / "junit.xml").unlink()
    assert not reusable_execution(previous, "base", evidence, image, workspace, b"gold", b"oracle")
