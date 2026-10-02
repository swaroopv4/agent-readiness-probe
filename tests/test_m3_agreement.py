import pytest
from arp.m3_agreement import compare


def row(primary, human, rule_secondary='', human_secondary='', outcome='pass', trajectory='example'):
    return dict(rule_primary=primary, human_primary=human, rule_secondary=rule_secondary,
                human_secondary=human_secondary, outcome=outcome, trajectory=trajectory)


def test_abstentions_count_as_disagreements_and_failure_coverage_is_separate():
    rows = [row('no_failure', 'no_failure') for _ in range(6)] + [
        row('unclassified', 'reasoning_error', human_secondary='missing_context', outcome='fail', trajectory='A'),
        row('unclassified', 'reasoning_error', outcome='fail', trajectory='B')]
    result = compare(rows)
    assert result['primary_exact_matches'] == 6
    assert result['primary_kappa'] == pytest.approx(3/7)
    assert result['coverage'] == .75 and result['abstentions'] == 2
    assert result['covered_exact_agreement'] == 1
    assert result['failed_outcome_coverage'] == 0
    assert result['secondary_exact_matches'] == 7 and result['joint_exact_matches'] == 6
    assert result['primary_per_class']['reasoning_error']['precision'] is None
    assert result['primary_per_class']['reasoning_error']['recall'] == 0
    assert result['primary_per_class']['unclassified']['precision'] == 0
    assert result['primary_per_class']['unclassified']['recall'] is None
    assert result['disagreements'] == ['A', 'B']


def test_secondary_sets_ignore_order_and_absent_classes_are_not_measured():
    result = compare([row('reasoning_error', 'reasoning_error', 'env_setup, reasoning_error', 'reasoning_error, env_setup', outcome='fail')])
    assert result['secondary_exact_agreement'] == 1
    assert result['primary_kappa'] is None
    assert result['primary_per_class']['test_flakiness']['status'] == 'not measured (absent in both)'
    assert result['secondary_per_class']['missing_context']['precision'] is None


def test_empty_review_is_not_perfect_agreement():
    with pytest.raises(ValueError):
        compare([])
