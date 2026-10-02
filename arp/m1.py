"""Reproduce M1 without inference, API keys, or paid services."""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import time
from pathlib import Path

from .miner import apply_patch, digest, export_base, git, inspect_commit, patches, prepare_agent_workspace
from .validation import docker_command, execute, parse_junit, validity_reason

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/pallets/click.git"
SOURCE_HEAD = "06b2a678741131fd577ce170e23e5ca0aeba0309"
BASE_IMAGE = "python:3.11.14-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d"
SEED = 20260930


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_image() -> str:
    subprocess.run([
        "docker", "build", "--build-arg", f"BASE_IMAGE={BASE_IMAGE}",
        "--tag", "arp-m1-evaluator:v1", "--file", str(ROOT / "docker/Dockerfile.evaluator"),
        str(ROOT / "docker"),
    ], check=True)
    return subprocess.check_output([
        "docker", "image", "inspect", "arp-m1-evaluator:v1", "--format", "{{.Id}}",
    ], encoding="utf-8").strip()


def reusable_execution(previous: Path, state: str, old_evidence: Path, image_id: str,
                       workspace: Path, gold_patch: bytes, oracle_patch: bytes) -> bool:
    required = ("result.json", "command.json", "junit.xml", "stdout.txt", "stderr.txt")
    if any(not (old_evidence / name).is_file() for name in required):
        return False
    old_command = json.loads((old_evidence / "command.json").read_text(encoding="utf-8"))
    if len(old_command) < 4:
        return False
    expected = docker_command(image_id, previous / state, old_evidence, old_command[3])
    if old_command != expected:
        return False
    if any(p.is_symlink() for p in (previous / state).rglob("*")):
        return False
    old_files = {p.relative_to(previous / state).as_posix(): digest(p.read_bytes())
                 for p in (previous / state).rglob("*") if p.is_file()}
    new_files = {p.relative_to(workspace).as_posix(): digest(p.read_bytes())
                 for p in workspace.rglob("*") if p.is_file()}
    return (old_files == new_files and (previous / "gold.patch").read_bytes() == gold_patch
            and (previous / "oracle.patch").read_bytes() == oracle_patch)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/private/m1-v1")
    parser.add_argument("--limit", type=int, default=12, help="Use 12 for the milestone")
    parser.add_argument("--image", help="Reuse an already built evaluator image ID")
    parser.add_argument("--reuse-evidence", type=Path, help="Reuse completed executions only when image, command and inputs match")
    parser.add_argument("--recorded-only", action="store_true", help="Audit existing executions without launching or inspecting Docker")
    args = parser.parse_args()
    output = args.output.resolve()
    private = (ROOT / "artifacts/private").resolve()
    if not output.is_relative_to(private) or output == private:
        parser.error("M1 output must be a new child of artifacts/private")
    if args.limit < 1 or args.limit > 12:
        parser.error("Task limit must be between one and 12")
    reuse = args.reuse_evidence.resolve() if args.reuse_evidence else None
    if reuse and (not reuse.is_relative_to(private) or not reuse.is_dir()):
        parser.error("Reused evidence must be in the private host store")
    if args.recorded_only and (not reuse or not args.image):
        parser.error("Recorded-only mode requires --reuse-evidence and its exact recorded --image")
    if output.exists():
        parser.error("Output exists. Choose a new version, without overwriting evidence")
    if shutil.disk_usage(ROOT).free < 10 * 1024**3:
        raise RuntimeError("Less than 10 GiB free. Stop before M1")
    if not args.recorded_only:
        subprocess.run(["docker", "info", "--format", "{{.ServerVersion}} {{.OSType}}"], check=True)
    repo = ROOT / "artifacts/private/source/click"
    if not repo.exists():
        repo.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", SOURCE_URL, str(repo)], check=True)
    if git(repo, "remote", "get-url", "origin").decode().strip() != SOURCE_URL:
        raise RuntimeError("Source origin is not the approved public repository")
    if git(repo, "rev-parse", SOURCE_HEAD).decode().strip() != SOURCE_HEAD:
        raise RuntimeError("Pinned source head unavailable")
    output.mkdir(parents=True)
    start = time.monotonic()
    if args.recorded_only:
        image_id = args.image
        environment = (reuse / "environment.txt").read_text(encoding="utf-8")
    else:
        image = args.image or build_image()
        image_id = subprocess.check_output(["docker", "image", "inspect", image, "--format", "{{.Id}}"], encoding="utf-8").strip()
        environment = subprocess.check_output([
            "docker", "run", "--rm", "--network", "none", "--read-only", image_id,
            "sh", "-c", "cat /opt/environment.txt /opt/wheel-hashes.txt && dpkg-query -W less",
        ], encoding="utf-8")
    (output / "environment.txt").write_text(environment, encoding="utf-8")
    population = git(repo, "rev-list", "--since=2026-01-01", "--until=2026-09-30", SOURCE_HEAD).decode().splitlines()
    audit = [inspect_commit(repo, commit).record() for commit in population]
    write_json(output / "candidate_audit.json", audit)
    curated = json.loads((ROOT / "datasets/click_candidates.json").read_text(encoding="utf-8"))
    records = []
    rejected = []
    all_runs = []
    reused_count = 0
    for spec in curated:
        if len(records) >= args.limit:
            break
        if shutil.disk_usage(ROOT).free < 10 * 1024**3:
            raise RuntimeError("Disk floor reached. Preserve evidence and stop")
        candidate = inspect_commit(repo, spec["commit"])
        if candidate.commit not in population:
            raise RuntimeError("Candidate is outside the frozen population")
        if spec.get("exclusion_reason"):
            rejected.append({"commit": candidate.commit, "reason": spec["exclusion_reason"]})
            write_json(output / "rejections.json", rejected)
            continue
        if candidate.reason:
            rejected.append({"commit": candidate.commit, "reason": candidate.reason})
            continue
        task_id = f"click-{len(records) + 1:03}"
        print(f"Validating {task_id}: {spec['title']}", flush=True)
        task = output / "candidates" / candidate.commit
        base = task / "base"
        archive_hash = export_base(repo, candidate.parent, base)
        gold_patch, oracle_patch = patches(repo, candidate)
        (task / "gold.patch").write_bytes(gold_patch)
        (task / "oracle.patch").write_bytes(oracle_patch)
        buggy = task / "buggy"
        gold = task / "gold"
        shutil.copytree(base, buggy)
        apply_patch(buggy, oracle_patch)
        shutil.copytree(buggy, gold)
        apply_patch(gold, gold_patch)
        runs = []
        for state, workspace in (("base", base), ("buggy", buggy), ("gold", gold)):
            for repeat in range(3):
                evidence = task / "evidence" / f"{state}-{repeat}"
                previous = reuse / "candidates" / candidate.commit if reuse else None
                old_evidence = previous / "evidence" / f"{state}-{repeat}" if previous else None
                reusable = False
                if old_evidence and (old_evidence / "result.json").exists():
                    prior = json.loads((old_evidence / "result.json").read_text(encoding="utf-8"))
                    reusable = reusable_execution(previous, state, old_evidence, image_id,
                                                   workspace, gold_patch, oracle_patch)
                if reusable:
                    shutil.copytree(old_evidence, evidence)
                    run = parse_junit(evidence / "junit.xml", state, repeat, prior["returncode"],
                                      prior["seconds"], prior["timed_out"])
                    (evidence / "reused_from.txt").write_text(str(old_evidence), encoding="utf-8")
                    write_json(evidence / "result.json", run.record())
                    reused_count += 1
                else:
                    if args.recorded_only:
                        raise RuntimeError(f"Missing or incompatible recorded execution: {candidate.commit} {state} {repeat}")
                    run = execute(image_id, workspace, evidence, state, repeat)
                runs.append(run)
                all_runs.append(run.record())
                print(f"  {state} {repeat + 1}/3: exit={run.returncode} "
                      f"passed={run.passed} failed={len(run.failures)} skipped={run.skipped} "
                      f"seconds={run.seconds:.1f}", flush=True)
                write_json(output / "progress.json", {
                    "execution_count": len(all_runs), "validated_count": len(records),
                    "active_commit": candidate.commit, "last_execution": run.record(),
                })
        exception_types = tuple(spec.get("behavioral_exception_types", []))
        reason = validity_reason(runs, candidate.tests, behavioral_exception_types=exception_types)
        if reason:
            rejected.append({"commit": candidate.commit, "reason": reason})
            print(f"  REJECTED: {reason}", flush=True)
        else:
            statement = "# Task\n\n" + spec["statement"] + "\n"
            agent = output / "agent_workspaces" / task_id
            prepare_agent_workspace(base, agent, statement)
            if git(agent, "remote").strip() or git(agent, "rev-list", "--count", "HEAD").strip() != b"1":
                raise RuntimeError("Fresh agent history audit failed")
            if (agent / "gold.patch").exists() or (agent / "oracle.patch").exists():
                raise RuntimeError("Hidden artifacts leaked into agent workspace")
            records.append({
                "task_id": task_id, "title": spec["title"], "category": spec["category"],
                "statement": statement, "statement_sha256": digest(statement.encode()),
                "statement_origin": "assistant reconstructed behavioral contract from public change and tests",
                "human_acceptance": "pending user review", "exposure_risk": "unknown",
                "known_overlap": "not measured, public benchmark metadata checks incomplete",
                "repo_url": SOURCE_URL, "license": "BSD-3-Clause",
                "fix_commit": candidate.commit, "base_commit": candidate.parent,
                "date": candidate.date, "archive_sha256": archive_hash,
                "gold_sha256": digest(gold_patch), "oracle_sha256": digest(oracle_patch),
                "production_files": candidate.production, "production_lines": candidate.production_lines,
                "oracle_files": candidate.tests, "ignored_documentation_changes": candidate.other,
                "behavioral_exception_types": exception_types,
                "image_id": image_id, "agent_workspace": str(agent.relative_to(ROOT)),
                "evidence": str((task / "evidence").relative_to(ROOT)),
                "runs": [run.record() for run in runs],
                "review_notes": spec.get("review_notes", "Behavioral correctness and alternate solutions need user review"),
            })
            print(f"  EXECUTION VALIDATED: {task_id}", flush=True)
        write_json(output / "rejections.json", rejected)
        write_json(output / "tasks.json", records)
    shuffled = list(range(len(records)))
    random.Random(SEED).shuffle(shuffled)
    development = set(shuffled[:4])
    for index, record in enumerate(records):
        record["split"] = "development" if index in development else "confirmation"
    write_json(output / "tasks.json", records)
    summary = {
        "dataset_version": output.name, "repo_url": SOURCE_URL, "source_head": SOURCE_HEAD,
        "selection": "purposive behavioral shortlist, fixed order, first 12 execution-valid tasks",
        "assignment": "seeded random task split, four development and eight confirmation, no stratification",
        "seed": SEED, "population_count": len(population),
        "structurally_eligible_count": sum(row["reason"] is None for row in audit),
        "curated_count": len(curated), "execution_validated_count": len(records),
        "human_accepted_count": 0, "human_acceptance": "pending user review",
        "execution_count": len(all_runs), "rejected_after_shortlist_count": len(rejected),
        "reused_execution_count": reused_count, "fresh_execution_count": len(all_runs) - reused_count,
        "image_id": image_id, "base_image": BASE_IMAGE,
        "recorded_only_freeze": args.recorded_only,
        "docker_engine_at_freeze": "not rechecked, no Docker calls in recorded-only mode" if args.recorded_only else "verified reachable",
        "seconds": round(time.monotonic() - start, 2), "paid_api_spend_usd": 0,
        "agent_runs": 0, "dollar_cost": "not measured", "usage": "not measured",
        "disk_free_gib": round(shutil.disk_usage(ROOT).free / 1024**3, 2),
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    if len(records) != args.limit:
        raise SystemExit("Insufficient valid tasks. Stop for review without weakening gates")


if __name__ == "__main__":
    main()
