"""Freeze revised statements and supplied human decisions without new executions."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .check_m1 import audit, read_reviews
from .m1 import ROOT, write_json
from .miner import digest, prepare_agent_workspace


def freeze(previous: Path, output: Path, review_path: Path) -> dict:
    private = (ROOT / "artifacts/private").resolve()
    previous, output = previous.resolve(), output.resolve()
    if not previous.is_relative_to(private) or not output.is_relative_to(private) or output == private:
        raise ValueError("Dataset versions must be children of the private host store")
    if not previous.is_dir() or output.exists() or not review_path.is_file():
        raise ValueError("Require existing source/review and a new output version")
    records = json.loads((previous / "tasks.json").read_text(encoding="utf-8"))
    reviews = read_reviews(review_path, records)
    if len(reviews) != 12 or any(row["decision"] != "accept" for row in reviews.values()):
        raise ValueError("This freeze requires all 12 supplied human acceptance decisions")
    specs = json.loads((ROOT / "datasets/click_candidates.json").read_text(encoding="utf-8"))
    statements = {row["commit"]: "# Task\n\n" + row["statement"] + "\n" for row in specs}
    if any(record["fix_commit"][:7] not in statements for record in records):
        raise ValueError("Revised statement missing for a frozen task")
    output.mkdir(parents=True)
    shutil.copytree(previous / "candidates", output / "candidates")
    for name in ("environment.txt", "candidate_audit.json", "rejections.json"):
        shutil.copyfile(previous / name, output / name)
    shutil.copyfile(review_path, output / "human_review.csv")
    revised_ids = []
    for record in records:
        statement = statements[record["fix_commit"][:7]]
        if statement != record["statement"]:
            revised_ids.append(record["task_id"])
        record["statement"] = statement
        record["statement_sha256"] = digest(statement.encode("utf-8"))
        record["human_acceptance"] = "accepted"
        record["human_review"] = reviews[record["task_id"]]
        candidate = output / "candidates" / record["fix_commit"]
        agent = output / "agent_workspaces" / record["task_id"]
        prepare_agent_workspace(candidate / "base", agent, statement)
        record["agent_workspace"] = str(agent.relative_to(ROOT))
        record["evidence"] = str((candidate / "evidence").relative_to(ROOT))
    summary = json.loads((previous / "summary.json").read_text(encoding="utf-8"))
    summary.update({
        "dataset_version": output.name, "parent_dataset_version": previous.name,
        "human_accepted_count": 12, "human_acceptance": "accepted by supplied user decisions",
        "human_review_sha256": digest((output / "human_review.csv").read_bytes()),
        "statement_revised_tasks": revised_ids,
        "fresh_execution_count": 0, "reused_execution_count": 108,
        "recorded_only_freeze": True,
        "docker_engine_at_freeze": "not rechecked, no Docker calls during review freeze",
        "limitations": [
            "Statements were revised to match hidden assertions before any agent run. Revised tasks are more precisely specified than typical real-world tickets.",
            "click-005 names _ansi_re because the hidden test inspects it directly.",
            "click-010 is development only and its oracle includes an unrelated duplicate-option warning check.",
        ],
    })
    summary.pop("seconds", None)
    write_json(output / "tasks.json", records)
    write_json(output / "summary.json", summary)
    return audit(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("review_csv", type=Path)
    args = parser.parse_args()
    print(json.dumps(freeze(args.previous, args.output, args.review_csv), indent=2))


if __name__ == "__main__":
    main()
