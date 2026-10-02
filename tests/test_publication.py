from arp.check_publication import forbidden_path, scan_bytes


def test_private_paths_are_forbidden_but_documentation_and_empty_template_are_allowed():
    assert all(forbidden_path(p) for p in ['.env', 'sub/.env.local', 'artifacts/private/a.txt', 'workspaces/task/a.py', 'nested/auth.json', 'gold.patch'])
    assert not any(forbidden_path(p) for p in ['.env.example', 'docs/m3_human_review.md', 'results/m5_plan.json'])


def test_credential_findings_are_redacted_and_detect_nonstandard_known_values():
    secret = b'not-a-standard-key-' + b'X'*40
    synthetic_key = b'sk-' + b'A'*48
    hits = scan_bytes(secret + b'\n' + synthetic_key, [secret], [])
    assert 'Known local credential value' in hits and 'OpenAI-shaped key' in hits
    assert all(secret.decode() not in h and synthetic_key.decode() not in h for h in hits)


def test_private_payload_comparison_does_not_flag_a_digest_or_path_reference():
    private = b'diff ' + b'private-change\n'*30
    assert scan_bytes(private, [], [private]) == ['Known full private gold/oracle payload']
    assert not scan_bytes(b'gold_sha256=abc; artifacts/private/gold.patch', [], [private])
