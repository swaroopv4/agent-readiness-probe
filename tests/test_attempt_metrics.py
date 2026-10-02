import json
from arp.attempt_metrics import metrics


def test_failed_test_detected_despite_shell_exit_zero_and_git_short_circuit(tmp_path):
    events=[{"type":"turn.completed","usage":{"input_tokens":10}},
        {"type":"item.completed","item":{"id":"test","type":"command_execution","command":"pytest -q > /tmp/test.log; tail /tmp/test.log","exit_code":0,"aggregated_output":"1 failed, 4 passed in 1s"}},
        {"type":"item.completed","item":{"id":"git","type":"command_execution","command":"git diff && pytest -q","exit_code":129,"aggregated_output":"warning: Not a git repository"}},
        {"type":"item.completed","item":{"id":"read","type":"command_execution","command":"cat pyproject.toml","exit_code":0,"aggregated_output":"[tool.pytest]"}}]
    (tmp_path/'events.jsonl').write_text('\n'.join(map(json.dumps,events)))
    (tmp_path/'result.json').write_text(json.dumps({"task_id":"fake","split":"development","state":"test_failure", "adapter":{"model":"fake","seconds":1,"inference_settings":{"reasoning_effort":"low"},"usage":{"turns":[{"input_tokens":10,"output_tokens":2}]}}}))
    result=metrics(tmp_path)
    assert result['failed_public_pytest_runs']==1
    assert len(result['public_pytest_runs'])==2
    assert result['public_pytest_runs'][1]['blocked_before_pytest']
    assert result['cli_turns']==1 and result['native_tool_calls']==3
