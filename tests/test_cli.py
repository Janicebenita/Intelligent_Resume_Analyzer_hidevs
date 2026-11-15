"""Offline CLI analysis/save/reopen and actionable input failure."""

import json

from app.cli import main
from app.demo import DEMO_RESUME, demo_job


def test_cli_save_and_reopen(tmp_path, capsys):
    resume = tmp_path / "resume.txt"
    resume.write_text(DEMO_RESUME, encoding="utf-8")
    job = tmp_path / "job.json"
    job.write_text(demo_job().model_dump_json(), encoding="utf-8")
    store = str(tmp_path / "store")
    html = tmp_path / "report.html"
    assert (
        main(
            [
                "--resume",
                str(resume),
                "--job",
                str(job),
                "--store",
                store,
                "--as-of",
                "2025-01-01",
                "--html",
                str(html),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["match_score"] == 95
    assert html.exists()
    assert main(["--load", report["id"], "--store", store]) == 0
    assert json.loads(capsys.readouterr().out) == report


def test_cli_missing_file(tmp_path, capsys):
    assert main(["--resume", str(tmp_path / "missing"), "--job", "missing.json"]) == 2
    assert "Could not" in capsys.readouterr().err
