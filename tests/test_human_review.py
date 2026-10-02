from __future__ import annotations

import csv

import pytest

from arp.check_m1 import read_reviews
from arp.review_m1 import freeze


def review_file(tmp_path, rows):
    path = tmp_path / "review.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["task_id", "split", "decision", "reviewer", "reviewed_at"])
        writer.writeheader()
        writer.writerows(rows)
    return path


RECORDS = [{"task_id": "click-001", "split": "confirmation"}]
ROW = {"task_id": "click-001", "split": "confirmation", "decision": "accept",
       "reviewer": "Swaroop", "reviewed_at": "2026-09-30T00:00:00+00:00"}


def test_pending_review_is_not_inferred_as_acceptance(tmp_path):
    row = {**ROW, "decision": "", "reviewer": "", "reviewed_at": ""}
    assert read_reviews(review_file(tmp_path, [row]), RECORDS)["click-001"]["decision"] == ""
    assert read_reviews(tmp_path / "absent.csv", RECORDS) == {}


def test_supplied_review_preserves_reviewer_and_decision(tmp_path):
    assert read_reviews(review_file(tmp_path, [ROW]), RECORDS) == {"click-001": ROW}


@pytest.mark.parametrize("change", [
    {"task_id": "click-002"}, {"split": "development"}, {"decision": "maybe"},
    {"reviewer": ""}, {"reviewed_at": ""},
])
def test_mismatched_or_incomplete_review_is_rejected(tmp_path, change):
    with pytest.raises(ValueError):
        read_reviews(review_file(tmp_path, [{**ROW, **change}]), RECORDS)


def test_duplicate_rows_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        read_reviews(review_file(tmp_path, [ROW, ROW]), RECORDS)


def test_review_freeze_refuses_external_output_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr("arp.review_m1.ROOT", tmp_path / "project")
    with pytest.raises(ValueError, match="private host store"):
        freeze(tmp_path / "previous", tmp_path / "new", tmp_path / "review.csv")
    assert not (tmp_path / "new").exists()
