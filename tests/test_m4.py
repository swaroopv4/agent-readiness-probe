from arp.m4_diagnostics import output_diagnostics
import json
from arp.m4_report import embed_json, table


def test_pytest_pass_followed_by_git_failure_is_not_a_failed_test():
    d = output_diagnostics('257 passed, 24 skipped in 0.39s\nwarning: Not a git repository\nusage: git diff')
    assert not d['pytest_failed'] and not d['metadata_collection_error']


def test_visible_failure_is_counted_even_if_later_command_masks_exit_code():
    assert output_diagnostics('2 failed, 12 passed in 0.03s\nscript succeeded')['pytest_failed']
    assert not output_diagnostics('1654 passed, 24 skipped, 31000 deselected, 1 xfailed in 3.50s')['pytest_failed']


def test_metadata_detection_requires_emitted_collection_traceback_not_source_mentions():
    text = ('_________________ ERROR collecting tests/test_deprecations.py __________________\n'
            'E   importlib.metadata.PackageNotFoundError: No package metadata was found for click\n'
            '!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!')
    assert output_diagnostics(text)['metadata_collection_error']
    assert not output_diagnostics('raise PackageNotFoundError(name)\n# ERROR collecting')['metadata_collection_error']
    assert not output_diagnostics('E   importlib.metadata.PackageNotFoundError: No package metadata was found for click')['metadata_collection_error']


def test_full_and_ordinary_summaries_both_detect_actual_test_failures():
    assert output_diagnostics('========= 2 failed, 2068 passed, 24 skipped in 4.13s =========')['pytest_failed']
    assert output_diagnostics('1 error in 2.02s')['pytest_failed']
    assert not output_diagnostics("    assert result == '2 failed, 12 passed in 0.03s'")['pytest_failed']


def test_saved_notes_cannot_break_out_of_embedded_json_or_table_cells():
    note = '</script><img src="https://bad.example" onerror="boom()"> & reviewer'
    snapshot = embed_json({'note': note})
    assert '<' not in snapshot and json.loads(snapshot)['note'] == note
    markup = table(['Human note'], [[note]])
    assert '<img' not in markup and '&lt;/script&gt;' in markup
