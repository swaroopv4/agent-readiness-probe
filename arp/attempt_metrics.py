"""Read recorded CLI events; no model or task execution."""
from collections import Counter
import hashlib
import json
import re

TOOL_TYPES = {"command_execution", "file_change", "mcp_tool_call", "web_search"}


def metrics(attempt):
    raw = (attempt/"events.jsonl").read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    result = json.loads((attempt/"result.json").read_text(encoding="utf-8"))
    adapter = result["adapter"]
    types = Counter(e.get("item", {}).get("type") for e in events if e.get("type") == "item.completed")
    test_runs = []
    other_failed_commands = []
    for e in events:
        item = e.get("item", {})
        if e.get("type") != "item.completed" or item.get("type") != "command_execution": continue
        command = item.get("command", "")
        output = item.get("aggregated_output", "")
        summaries = [line for line in output.splitlines() if re.search(
            r"\b(?:\d+ (?:passed|failed|skipped|deselected|xfailed|errors?)|ERROR |E   |AssertionError|[A-Za-z]+Error:)", line)]
        if re.search(r"(?:\bpytest\s+(?:-[\w]|tests|/)|\bpytest\.main\(|\bpython\s+-m\s+pytest\b)", command):
            collection_error = "ERROR collecting" in output or "error during collection" in output
            behavioral_failure = bool(re.search(r"\b[1-9]\d* failed\b", output))
            blocked = "Not a git repository" in output and "&&" in command and not summaries
            if blocked:
                other_failed_commands.append({"item_id":item["id"], "exit_code":item.get("exit_code"), "reason":"git command prevented pytest execution"})
            test_runs.append({"item_id":item["id"], "exit_code":item.get("exit_code"),
                "blocked_before_pytest":blocked,
                "failed_run":not blocked and (collection_error or behavioral_failure or item.get("exit_code") not in (0,None)),
                "collection_error":collection_error, "behavioral_failure":behavioral_failure,
                "summary_lines":summaries, "command_sha256":hashlib.sha256(command.encode()).hexdigest(),
                "output_truncated":bool(re.search(r"(?:truncated|omitted)", output, re.I))})
        elif item.get("exit_code") not in (0, None):
            other_failed_commands.append({"item_id":item["id"], "exit_code":item.get("exit_code"),
                                          "summary_lines":summaries})
    usage_turns = adapter.get("usage", {}).get("turns", []) if isinstance(adapter.get("usage"), dict) else []
    usage = {key:sum(turn.get(key,0) for turn in usage_turns) for key in
             ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")}
    return {"run_id":attempt.name, "task_id":result["task_id"], "split":result["split"],
        "state":result["state"], "model":adapter["model"], "reasoning_effort":adapter["inference_settings"]["reasoning_effort"],
        "agent_wall_seconds":adapter["seconds"], "cli_turns":sum(e.get("type")=="turn.completed" for e in events),
        "native_tool_calls":sum(types[t] for t in TOOL_TYPES), "command_calls":types["command_execution"],
        "file_edit_calls":types["file_change"], "usage":usage if usage_turns else "not measured",
        "public_pytest_runs":test_runs,
        "failed_public_pytest_runs":sum(t["failed_run"] for t in test_runs),
        "other_nonzero_commands":other_failed_commands,
        "evaluation":{k:v for k,v in result.get("evaluation",{}).items() if k in {"returncode","seconds","collected","passed","skipped","timed_out"}},
        "evaluation_failure_count":len(result.get("evaluation",{}).get("failures",[])),
        "evaluation_error_count":len(result.get("evaluation",{}).get("errors",[])), "events_sha256":hashlib.sha256(raw).hexdigest(),
        "result_sha256":hashlib.sha256((attempt/"result.json").read_bytes()).hexdigest()}
