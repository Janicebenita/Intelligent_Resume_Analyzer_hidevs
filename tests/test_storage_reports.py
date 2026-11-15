"""JSON round trips, atomic file behavior, HTML escaping and CSV injection checks."""

import json
from unittest.mock import patch

import pytest

from app.errors import AnalysisError
from app.reports import csv_report, render_report
from app.storage import JsonRepository, dump_report, load_report


def test_json_round_trip_and_local_save_load(report, tmp_path):
    assert load_report(dump_report(report).encode()) == report
    repo = JsonRepository(tmp_path / "reports")
    path = repo.save(report)
    assert path.exists() and repo.load(report.id) == report
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    "content", [b"{", b"null", b"[]", b"\xff", b'{"schema_version":"999"}', b"x" * 2097153]
)
def test_invalid_report_inputs(content):
    with pytest.raises(AnalysisError):
        load_report(content)


def test_modified_score_is_rejected(report):
    data = report.model_dump(mode="json")
    data["match_score"] = 100
    with pytest.raises(AnalysisError, match="rubric"):
        load_report(json.dumps(data).encode())


@pytest.mark.parametrize("identifier", ["../secret", "a/b", "x" * 32, "a" * 31])
def test_path_traversal_and_invalid_ids(identifier, tmp_path):
    with pytest.raises(AnalysisError):
        JsonRepository(tmp_path).load(identifier)


def test_missing_corrupt_and_permission_failures(report, tmp_path):
    repo = JsonRepository(tmp_path)
    with pytest.raises(AnalysisError, match="does not exist"):
        repo.load(report.id)
    repo.save(report)
    (tmp_path / f"{report.id}.json").write_text("{", encoding="utf-8")
    with pytest.raises(AnalysisError):
        repo.load(report.id)
    with (
        patch("app.storage.os.replace", side_effect=PermissionError),
        pytest.raises(AnalysisError, match="save"),
    ):
        repo.save(report)
    assert not list(tmp_path.glob("*.tmp"))
    with (
        patch("pathlib.Path.open", side_effect=PermissionError),
        pytest.raises(AnalysisError, match="read"),
    ):
        repo.load(report.id)


def test_html_escapes_candidate_and_job_content(report):
    report.job.title = '<script>alert("bad")</script>'
    html = render_report(report, standalone=True)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<!doctype html>" in html
    assert report.id in html and "SHA-256" in html


def test_csv_neutralizes_formulas(report):
    report.rows[0].skill = '=HYPERLINK("https://example.com")'
    report.rows[0].evidence[0].text = "not a formula"
    assert "'=HYPERLINK" in csv_report(report)
