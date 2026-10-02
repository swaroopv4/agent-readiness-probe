"""Audit recorded M1 evidence and generate a host-only human review packet."""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from pathlib import Path

from .m1 import ROOT, write_json
from .miner import digest, git
from .validation import parse_junit, validity_reason


def file_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): digest(path.read_bytes())
            for path in root.rglob("*") if path.is_file() and ".git" not in path.relative_to(root).parts}


def read_reviews(path: Path, records: list[dict]) -> dict[str, dict[str, str]]:
    """Validate actual review rows without inferring missing decisions."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {record["task_id"]: record["split"] for record in records}
    if len(rows) != len(expected) or {row.get("task_id") for row in rows} != set(expected):
        raise ValueError("Human review task IDs must match the frozen manifest exactly")
    result = {}
    for row in rows:
        if row.get("split") != expected[row["task_id"]]:
            raise ValueError("Human review split differs from the frozen manifest")
        if row.get("decision", "") not in {"", "accept", "reject"}:
            raise ValueError("Unsupported human review decision")
        if row.get("decision") and (not row.get("reviewer") or not row.get("reviewed_at")):
            raise ValueError("Human decisions require reviewer and review time")
        result[row["task_id"]] = row
    return result


def audit(output: Path) -> dict:
    private = (ROOT / "artifacts/private").resolve()
    if not output.resolve().is_relative_to(private):
        raise ValueError("Evidence belongs in the private host store")
    records = json.loads((output / "tasks.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    if len(records) != 12 or {r["task_id"] for r in records} != {f"click-{n:03}" for n in range(1, 13)}:
        raise ValueError("M1 requires exactly 12 unique task records")
    if sum(r["split"] == "development" for r in records) != 4:
        raise ValueError("Development split must contain four tasks")
    if sum(r["split"] == "confirmation" for r in records) != 8:
        raise ValueError("Confirmation split must contain eight tasks")
    reviews = read_reviews(output / "human_review.csv", records)
    accepted_count = 0
    evidence_runs = []
    for record in records:
        candidate = output / "candidates" / record["fix_commit"]
        agent = ROOT / record["agent_workspace"]
        if digest((candidate / "gold.patch").read_bytes()) != record["gold_sha256"]:
            raise ValueError("Gold hash mismatch")
        if digest((candidate / "oracle.patch").read_bytes()) != record["oracle_sha256"]:
            raise ValueError("Oracle hash mismatch")
        if digest(record["statement"].encode()) != record["statement_sha256"]:
            raise ValueError("Statement hash mismatch")
        base_hashes, agent_hashes = file_hashes(candidate / "base"), file_hashes(agent)
        if agent_hashes.pop("TASK.md", None) != record["statement_sha256"] or base_hashes != agent_hashes:
            raise ValueError("Agent workspace differs from B beyond task statement")
        if git(agent, "remote").strip() or git(agent, "rev-list", "--count", "--all").strip() != b"1":
            raise ValueError("Agent history is not an isolated single snapshot")
        if git(agent, "status", "--porcelain").strip():
            raise ValueError("Prepared agent workspace was modified")
        for original_commit in (record["base_commit"], record["fix_commit"]):
            try:
                git(agent, "cat-file", "-e", original_commit)
            except subprocess.CalledProcessError:
                pass
            else:
                raise ValueError("Original history object leaked into agent workspace")
        runs = []
        for state in ("base", "buggy", "gold"):
            for repeat in range(3):
                evidence = candidate / "evidence" / f"{state}-{repeat}"
                stored = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
                run = parse_junit(evidence / "junit.xml", state, repeat, stored["returncode"],
                                  stored["seconds"], stored["timed_out"])
                if json.loads(json.dumps(run.record())) != stored:
                    raise ValueError("Parsed evidence differs from recorded result")
                command = json.loads((evidence / "command.json").read_text(encoding="utf-8"))
                if command[command.index("--network") + 1] != "none" or "--read-only" not in command:
                    raise ValueError("Evaluator isolation was not enabled")
                if command[command.index("--user") + 1] != "1000:1000":
                    raise ValueError("Evaluator must run without root")
                if record["image_id"] not in command:
                    raise ValueError("Wrong evaluator image")
                runs.append(run)
                evidence_runs.append(run.record())
        reason = validity_reason(runs, tuple(record["oracle_files"]),
                                behavioral_exception_types=tuple(record.get("behavioral_exception_types", [])))
        if reason:
            raise ValueError(f"{record['task_id']} is invalid: {reason}")
        review = reviews.get(record["task_id"], {})
        if record["human_acceptance"] == "accepted":
            if review.get("decision") != "accept":
                raise ValueError("Accepted task lacks a matching human decision")
            if record.get("human_review") != review:
                raise ValueError("Recorded human review differs from the review CSV")
            accepted_count += 1
        elif record["human_acceptance"] == "pending user review":
            if review.get("decision"):
                raise ValueError("Human decision must be incorporated in a new dataset version")
        else:
            raise ValueError("Task is not pending or human accepted")
    if summary["human_accepted_count"] != accepted_count:
        raise ValueError("Summary human acceptance count differs from actual review records")
    if accepted_count and digest((output / "human_review.csv").read_bytes()) != summary.get("human_review_sha256"):
        raise ValueError("Human review file hash mismatch")
    result = {
        "status": "M1 checks passed, all tasks human accepted" if accepted_count == 12 else "M1 mechanical checks passed, user acceptance pending",
        "execution_validated_tasks": 12, "development_tasks": 4, "confirmation_tasks": 8,
        "accepted_task_evidence_executions": len(evidence_runs),
        "all_measured_attempts_in_dataset": summary["execution_count"],
        "human_accepted_tasks": accepted_count, "agent_runs": 0, "incremental_paid_api_spend_usd": 0,
        "dollar_cost": "not measured", "usage": "not measured",
        "image_id": summary["image_id"], "private_output": str(output.relative_to(ROOT)),
        "task_ids": [record["task_id"] for record in records],
    }
    write_json(output / "checks.json", result)
    packet = ["# M1 task review packet", "", "Host-only review material. Do not copy this packet into an agent workspace.", "",
              "These are 12 execution-validated tasks. Human acceptance is recorded in human_review.csv for accepted tasks. Blank decisions remain pending. All statements were reconstructed by the assistant from public source changes and regression tests. Exposure risk is unknown. Public benchmark queries were incomplete, so absence of known overlap is not established.", "",
              "For each task, check that the requirement is clear, every hidden assertion follows from it, alternate correct implementations can pass, and the task is meaningful. Mark accept or reject and describe any revision in human_review.csv. Code edits alone do not count as human review.", "",
              "The split is frozen by seed 20260930. Do not use confirmation solutions to choose or write the later preparation fix. Source and oracle links below are available for validity review only. No confirmation agent trajectories exist.", ""]
    for record in records:
        candidate = output / "candidates" / record["fix_commit"]
        relative = candidate.relative_to(output).as_posix()
        base_run, buggy_run, gold_run = record["runs"][0], record["runs"][3], record["runs"][6]
        packet.extend([
            f"## {record['task_id']}: {record['title']}", "",
            f"Split: {record['split']}. Category: {record['category']}. Fix published: {record['date']}.", "",
            record["statement"].removeprefix("# Task\n\n").strip(), "",
            f"Three stable runs in each state: base {base_run['passed']} passed, buggy {len(buggy_run['failures'])} failed, gold {gold_run['passed']} passed. Platform skips and xfails remain recorded, and the base default stress-test deselection is preserved.", "",
            f"[Public provenance](https://github.com/pallets/click/commit/{record['fix_commit']}). "
            f"[Hidden test delta]({relative}/oracle.patch). [Gold production delta]({relative}/gold.patch). "
            f"[Buggy test output]({relative}/evidence/buggy-0/stdout.txt).", "",
            "Review evidence: " + record["review_notes"], "",
            "Failing oracle cases:", "",
        ])
        packet.extend("- " + name for name in buggy_run["failures"])
        packet.append("")
    (output / "review_packet.md").write_text("\n".join(packet), encoding="utf-8")
    review_csv = output / "human_review.csv"
    if not review_csv.exists():
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["task_id", "split", "decision", "clear_specification", "assertions_aligned",
                         "alternate_solutions_allowed", "meaningful_task", "notes", "reviewer", "reviewed_at"])
        for record in records:
            writer.writerow([record["task_id"], record["split"], "", "", "", "", "", "", "", ""])
        review_csv.write_text(stream.getvalue(), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
