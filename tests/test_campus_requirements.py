"""Fictional campus examples: alternative requirements and common resume layouts."""

import csv
import io
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import Job, Requirement
from app.parser import parse_resume
from app.reports import csv_report, render_report
from app.service import analyze
from app.storage import dump_report, load_report

DAY = date(2026, 11, 15)


def language_job():
    return Job(
        title="Software Engineering Trainee",
        minimum_years=0,
        experience_weight=0,
        requirements=[Requirement(skill="Java OR Python", alternatives=["Java", "Python"])],
    )


@pytest.mark.parametrize(
    "text,score,selected",
    [
        ("Built Python services.", 100, "Python"),
        ("Built Java services.", 100, "Java"),
        ("Built Java and Python services.", 100, "Java"),
        ("Python", 60, "Python"),
        ("Learning Python.", 25, "Python"),
        ("No Java experience; built Python services.", 100, "Python"),
        ("Pottery and woodworking", 0, None),
    ],
)
def test_alternative_group_earns_credit_once(text, score, selected):
    resume = f"Casey Blake\ncasey@example.com\nPROJECTS\n{text}"
    result = analyze(resume, language_job(), DAY)
    assert result.match_score == score
    assert len(result.rows) == 1
    assert result.rows[0].matched_alternative == selected
    assert load_report(dump_report(result).encode()) == result


def test_alternative_is_visible_in_html_and_csv():
    result = analyze(
        "Casey Blake\ncasey@example.com\nPROJECTS\nBuilt Python services.", language_job(), DAY
    )
    assert "Best supported alternative: Python" in render_report(result)
    rows = list(csv.reader(io.StringIO(csv_report(result))))
    assert len(rows[0]) == len(rows[1]) == 7
    assert rows[1][5] == "Python"


@pytest.mark.parametrize(
    "alternatives",
    [
        ["Python"],
        ["Python", "python3"],
        ["Python", "gender"],
        ["Python", " "],
        ["Python", "x" * 61],
    ],
)
def test_invalid_alternative_groups_rejected(alternatives):
    with pytest.raises(ValidationError):
        Requirement(skill="Programming language", alternatives=alternatives)


def test_legacy_version_one_report_still_opens():
    report = load_report(Path("docs/examples/sample-report.json").read_bytes())
    assert report.match_score == 95
    assert report.algorithm_version == "rolelens-1.0"


@pytest.mark.parametrize("separator", ["-", "–", "—", "\ufffd"])
def test_internship_heading_shared_year_and_decoding_notice(separator):
    text = (
        "Casey Blake\ncasey@example.com\nTECHNICAL INTERNSHIP EXPERIENCE\n"
        f"Example Labs | May{separator}Jul 2025\nProcessed data using Python and SQL.\n"
        "SELECTED SOFTWARE PROJECTS & EXTERNAL CLIENT WORK\n"
        "Built a web application using HTML, CSS, and JavaScript."
    )
    resume = parse_resume(text, ["HTML", "CSS"], DAY)
    lookup = {item.skill: item.status for item in resume.skills}
    assert resume.experience_months == 3
    assert lookup["Python"] == lookup["SQL"] == "evidenced"
    assert lookup["HTML"] == lookup["CSS"] == lookup["JavaScript"] == "evidenced"
    assert any("decoded" in warning for warning in resume.warnings) == (separator == "\ufffd")


def test_fundamentals_aliases_and_ai_collaboration_not_human_teamwork():
    text = (
        "Casey Blake\ncasey@example.com\nTECHNICAL SKILLS\n"
        "OOP, DSA Fundamentals\nPROJECTS\nBuilt collaborative AI workflows."
    )
    resume = parse_resume(text, [], DAY)
    lookup = {item.skill: item.status for item in resume.skills}
    assert lookup["Object-Oriented Programming"] == "mentioned"
    assert lookup["Data Structures and Algorithms"] == "mentioned"
    assert lookup["Teamwork"] == "not_found"
