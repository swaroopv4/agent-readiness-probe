"""Mine trusted public history without distributing that history to the agent."""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tarfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args], cwd=repo,
        capture_output=True, check=True,
    ).stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or not path.parts or path.is_absolute() or ".." in path.parts
            or "\\" in name or ":" in name
            or any(ord(c) < 32 for c in name)
            or any(p.lower() in {".git", ".hg", ".svn"} for p in path.parts)):
        raise ValueError(f"Unsafe repository path: {name!r}")
    return path


@dataclass(frozen=True)
class Candidate:
    commit: str
    parent: str
    date: str
    subject: str
    production: tuple[str, ...]
    tests: tuple[str, ...]
    other: tuple[str, ...]
    production_lines: int
    reason: str | None

    def record(self) -> dict:
        return asdict(self)


def inspect_commit(repo: Path, commit: str) -> Candidate:
    fields = git(repo, "show", "-s", "--format=%H%n%P%n%cs%n%s", commit).decode("utf-8").splitlines()
    full, parents, date, subject = fields[:4]
    parent_list = parents.split()
    if len(parent_list) != 1:
        return Candidate(full, "", date, subject, (), (), (), 0, "not_single_parent")
    parent = parent_list[0]
    entries = git(repo, "diff", "--name-status", "--no-renames", "-z", parent, full).decode("utf-8").split("\0")
    production: list[str] = []
    tests: list[str] = []
    other: list[str] = []
    reason = None
    for status, name in zip(entries[0::2], entries[1::2]):
        safe_path(name)
        if status not in {"A", "M"}:
            reason = "deleted_or_renamed_file"
        if name.startswith("src/click/") and name.endswith(".py"):
            production.append(name)
        elif name.startswith("tests/") and name.endswith(".py"):
            tests.append(name)
        else:
            other.append(name)
    lines = 0
    if production:
        for row in git(repo, "diff", "--numstat", parent, full, "--", *production).decode("utf-8").splitlines():
            added, removed, _ = row.split("\t", 2)
            if added == "-" or removed == "-":
                reason = "binary_production"
            else:
                lines += int(added) + int(removed)
    if not production or not tests:
        reason = reason or "requires_production_and_test_changes"
    elif len(production) > 5 or lines > 300:
        reason = reason or "production_size_cap"
    # Documentation-only side changes are left at B. Build changes are inseparable.
    if any(not (n.startswith("docs/") or n.startswith("CHANGES")
                or n.startswith("README") or n.endswith(".md") or n.endswith(".rst")) for n in other):
        reason = reason or "inseparable_non_documentation_change"
    return Candidate(full, parent, date, subject, tuple(production), tuple(tests), tuple(other), lines, reason)


def patches(repo: Path, candidate: Candidate) -> tuple[bytes, bytes]:
    if candidate.reason:
        raise ValueError(candidate.reason)
    common = ("diff", "--binary", "--no-renames", candidate.parent, candidate.commit, "--")
    return git(repo, *common, *candidate.production), git(repo, *common, *candidate.tests)


def extract_archive(data: bytes, destination: Path) -> None:
    if destination.exists():
        raise ValueError("Archive destination must be new")
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        members = archive.getmembers()
        for member in members:
            safe_path(member.name)
            if not (member.isdir() or member.isfile()):
                raise ValueError("Links and special archive entries are not allowed")
        destination.mkdir(parents=True)
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                assert source is not None
                target.write_bytes(source.read())
                target.chmod(member.mode & 0o777)


def export_base(repo: Path, parent: str, destination: Path) -> str:
    data = git(repo, "archive", "--format=tar", parent)
    extract_archive(data, destination)
    return digest(data)


def apply_patch(workspace: Path, patch: bytes) -> None:
    # git apply also validates patch traversal. Patch files are never left in workspace.
    environment = os.environ.copy()
    # These archives can live under the probe's own Git checkout. Never discover it.
    environment["GIT_CEILING_DIRECTORIES"] = str(workspace.resolve().parent)
    environment.pop("GIT_DIR", None)
    environment.pop("GIT_WORK_TREE", None)
    subprocess.run(["git", "apply", "--check", "--whitespace=nowarn", "-"],
                   cwd=workspace, input=patch, check=True, capture_output=True, env=environment)
    subprocess.run(["git", "apply", "--whitespace=nowarn", "-"],
                   cwd=workspace, input=patch, check=True, capture_output=True, env=environment)


def prepare_agent_workspace(base: Path, destination: Path, statement: str) -> None:
    """Copy B only, then create unrelated local history with no remotes."""
    if destination.exists():
        raise ValueError("Agent destination must be new")
    for path in base.rglob("*"):
        safe_path(path.relative_to(base).as_posix())
        if path.is_symlink():
            raise ValueError("Agent base contains a link")
    shutil.copytree(base, destination)
    (destination / "TASK.md").write_text(statement, encoding="utf-8", newline="\n")
    git(destination, "init", "-b", "task")
    git(destination, "add", "--all")
    git(destination, "-c", "user.name=Probe", "-c", "user.email=probe@localhost",
        "-c", "commit.gpgsign=false", "commit", "-m", "Initial task snapshot")
