from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import Path

import pytest

from arp.miner import apply_patch, export_base, extract_archive, git, inspect_commit, patches, prepare_agent_workspace, safe_path


def commit(repo: Path, message: str) -> str:
    git(repo, "add", "--all")
    git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost",
        "-c", "commit.gpgsign=false", "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def history(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    (repo / "src/click").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src/click/core.py").write_text("def answer():\n    return 1\n")
    (repo / "tests/test_core.py").write_text("def test_old():\n    assert True\n")
    base = commit(repo, "base")
    (repo / "src/click/core.py").write_text("def answer():\n    return 2\n")
    (repo / "tests/test_core.py").write_text("def test_new():\n    assert answer() == 2\n")
    (repo / "CHANGES.md").write_text("solution disclosure\n")
    fixed = commit(repo, "fix")
    return repo, base, fixed


def test_split_and_reconstruct_without_future_objects(history, tmp_path):
    repo, parent, fixed = history
    candidate = inspect_commit(repo, fixed)
    assert candidate.parent == parent and candidate.reason is None
    production, oracle = patches(repo, candidate)
    assert b"tests/" not in production and b"src/click/" not in oracle
    base = tmp_path / "archive"
    export_base(repo, parent, base)
    # Also exercise nested discovery of a parent checkout.
    git(tmp_path, "init", "-b", "outer")
    apply_patch(base, oracle)
    assert "test_new" in (base / "tests/test_core.py").read_text()
    assert "return 1" in (base / "src/click/core.py").read_text()
    apply_patch(base, production)
    assert "return 2" in (base / "src/click/core.py").read_text()
    assert not (base / "CHANGES.md").exists()


def test_agent_snapshot_has_only_base_and_fresh_history(history, tmp_path):
    repo, parent, fixed = history
    base, agent = tmp_path / "base", tmp_path / "agent"
    export_base(repo, parent, base)
    statement = "Behavioral task only\nSecond line\n"
    prepare_agent_workspace(base, agent, statement)
    assert (agent / "TASK.md").read_bytes() == statement.encode("utf-8")
    assert git(agent, "rev-list", "--count", "HEAD").strip() == b"1"
    assert git(agent, "remote").strip() == b""
    assert fixed.encode() not in git(agent, "log", "--all", "--format=%H")
    with pytest.raises(subprocess.CalledProcessError):
        git(agent, "cat-file", "-e", fixed)
    assert "return 1" in (agent / "src/click/core.py").read_text()
    assert not (agent / "CHANGES.md").exists()
    assert not (agent / "gold.patch").exists()


@pytest.mark.parametrize("name", ["../escape", "/root", "a/../../b", "a\\b", "C:secret", ".git/config", "a/.GIT/objects/x", "a\nfile", "."])
def test_reject_unsafe_paths(name):
    with pytest.raises(ValueError):
        safe_path(name)


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_archive_rejects_links_and_special_files(tmp_path, kind):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        member = tarfile.TarInfo("safe")
        member.type, member.linkname = kind, "../outside"
        archive.addfile(member)
    with pytest.raises(ValueError):
        extract_archive(buffer.getvalue(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_archive_validates_all_members_before_writing(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        safe = tarfile.TarInfo("first.txt")
        archive.addfile(safe)
        archive.addfile(tarfile.TarInfo("../escape"))
    with pytest.raises(ValueError):
        extract_archive(buffer.getvalue(), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_reject_build_changes(history):
    repo, _, _ = history
    (repo / "pyproject.toml").write_text("[build-system]\n")
    (repo / "src/click/core.py").write_text("def answer():\n    return 3\n")
    (repo / "tests/test_core.py").write_text("def test_new():\n    assert answer() == 3\n")
    candidate = inspect_commit(repo, commit(repo, "mixed build change"))
    assert candidate.reason == "inseparable_non_documentation_change"
    with pytest.raises(ValueError):
        patches(repo, candidate)


def test_reject_tests_only(history):
    repo, _, _ = history
    (repo / "tests/test_core.py").write_text("def test_new():\n    assert False\n")
    assert inspect_commit(repo, commit(repo, "test only")).reason == "requires_production_and_test_changes"
