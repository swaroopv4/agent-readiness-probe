"""Frozen deterministic M3 trajectory rules; no model inference or gold comparison."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from .attempt_metrics import metrics

LABELS = ("env_setup", "missing_context", "wrong_file_located", "convention_violation",
          "test_flakiness", "reasoning_error", "unclassified", "no_failure")
INFRA = {"infrastructure_abort", "container_setup_abort", "provider_or_transport_failure",
         "tool_runtime_unavailable", "usage_limit", "evaluator_infrastructure_error"}


def label(attempt: Path) -> dict:
    measured = metrics(attempt)
    result = json.loads((attempt/"result.json").read_text(encoding="utf-8"))
    raw = (attempt/"events.jsonl").read_bytes()
    evidence = []
    setup, behavior = [], []
    for line_number, line in enumerate(raw.splitlines(), 1):
        event = json.loads(line)
        item = event.get("item", {})
        if event.get("type") != "item.completed" or item.get("type") != "command_execution": continue
        output = item.get("aggregated_output", "")
        test = next((t for t in measured["public_pytest_runs"] if t["item_id"] == item["id"]), None)
        traceback = "Traceback (most recent call last)" in output
        setup_trace = traceback and re.search(r"(?m)^(?:[A-Za-z_][A-Za-z_0-9]*\.)*(?:PackageNotFoundError|ModuleNotFoundError|ImportError):", output)
        assertion_trace = traceback and re.search(r"(?m)^AssertionError(?::|\s*$)", output)
        kind = None
        if test and test["collection_error"] or setup_trace:
            setup.append(item["id"]); kind = "env_setup"
        elif test and test["behavioral_failure"] or assertion_trace:
            behavior.append(item["id"]); kind = "reasoning_error"
        if kind or test and not test["blocked_before_pytest"]:
            summary = [v.strip() for v in output.splitlines() if re.search(
                r"PackageNotFoundError|ModuleNotFoundError|ERROR collecting|AssertionError|\b\d+ (?:failed|passed|skipped|errors?)\b", v)]
            evidence.append({"item_id":item["id"], "event_line":line_number,
                             "kind":kind or "public_test_run", "exit_code":item.get("exit_code"),
                             "excerpt":"; ".join(summary[-4:])[:900] or "Public test command completed",
                             "command":item.get("command", ""), "output":output})
    secondary = []
    if setup: secondary.append("env_setup")
    if behavior: secondary.append("reasoning_error")
    state = result["state"]
    if state in INFRA:
        primary = "unclassified"; applicability = "infrastructure; outside repository failure taxonomy"
        reason = "Provider/runner infrastructure is separate from task-local failure."
    elif state == "resolved":
        primary = "no_failure"; applicability = "task"
        reason = "Independent evaluator passed; intermediate obstacles are diagnostic secondary labels."
    elif state == "invalid_submission":
        primary = "convention_violation"; applicability = "task"
        reason = "Host rejected a submission against the predeclared immutable-file/source boundary."
    elif state == "test_failure" and behavior:
        primary = "reasoning_error"; applicability = "task"
        reason = "Submitted failure and visible public behavioral test failures; no inference about hidden reasoning."
    elif state in {"test_failure", "cancelled"} and setup and not behavior:
        primary = "env_setup"; applicability = "task"
        reason = "Visible import/collection obstacle without observed public behavioral failure; human causal attribution required."
    else:
        primary = "unclassified"; applicability = "task"
        reason = "Insufficient public trajectory evidence for a narrower terminal failure class."
    if state == "invalid_submission":
        evidence.append({"item_id":"host-submission", "event_line":None, "kind":"convention_violation",
                         "excerpt":result.get("submission_error", "Invalid source submission"), "command":"", "output":""})
    evidence.append({"item_id":"host-evaluation", "event_line":None, "kind":"outcome",
        "excerpt":f"State={state}; evaluator passed={measured['evaluation'].get('passed', 'not evaluated')}; failures={measured['evaluation_failure_count']}; errors={measured['evaluation_error_count']}",
        "command":"", "output":""})
    return {"run_id":attempt.name, "task_id":result["task_id"], "split":result["split"],
        "arm":result["arm"], "repeat":result["repeat"], "state":state,
        "success":True if state == "resolved" else None if state in INFRA else False,
        "rule_primary":primary, "rule_secondary":secondary, "applicability":applicability,
        "rule_reason":reason, "evidence":evidence, "metrics":measured,
        "events_sha256":hashlib.sha256(raw).hexdigest(), "human_primary":"", "human_secondary":"", "human_notes":""}
