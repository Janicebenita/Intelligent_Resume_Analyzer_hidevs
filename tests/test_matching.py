"""Independent rubric arithmetic, invariants and protected identity counterfactuals."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import Job, Requirement
from app.service import analyze

DAY = date(2025, 1, 1)


def job(**kwargs):
    return Job(
        title="Test Engineer",
        requirements=[Requirement(skill="Python", weight=3), Requirement(skill="Docker", weight=1)],
        **kwargs,
    )


def test_independent_score_calculation():
    text = (
        "Alex Morgan\na@example.com\nSKILLS\nDocker\n"
        "EXPERIENCE\nJan 2023 - Dec 2024\nBuilt Python APIs."
    )
    report = analyze(text, job(minimum_years=4, experience_weight=20), DAY)
    # Python: 80*3/4*1=60; Docker:80*1/4*.6=12; experience:20*24/48=10.
    assert report.match_score == 82
    assert report.skills_points == 72
    assert report.experience_points == 10


@pytest.mark.parametrize("weight", [0, 10, 20, 50])
def test_full_match_is_capped_and_components_sum(weight):
    text = (
        "Alex Morgan\na@example.com\nEXPERIENCE\nJan 2000 - Dec 2024\n"
        "Built Python and Docker services."
    )
    report = analyze(text, job(minimum_years=2, experience_weight=weight), DAY)
    assert report.match_score == 100
    assert round(report.skills_points + report.experience_points, 2) == report.match_score


def test_missing_required_and_no_evidence_score_zero():
    report = analyze("Alex Morgan\na@example.com\nSKILLS\nPottery and woodworking", job(), DAY)
    assert report.match_score == 0
    assert report.missing_required == ["Python", "Docker"]
    assert "Clarify" in report.recommendation


def test_identity_does_not_change_score():
    suffix = (
        "\nSKILLS\nPython, Docker\nEXPERIENCE\nJan 2021 - Dec 2024\n"
        "Built Python and Docker services."
    )
    a = analyze("Alex Morgan\nalex@example.com" + suffix, job(), DAY)
    b = analyze("María García\nmaria@example.com" + suffix, job(), DAY)
    assert a.match_score == b.match_score
    assert a.rows == b.rows


def test_no_experience_requirement_reallocates_to_skills():
    report = analyze(
        "Alex Morgan\na@example.com\nPROJECTS\nBuilt Python and Docker services.",
        job(minimum_years=0, experience_weight=20),
        DAY,
    )
    assert report.job.experience_weight == 0
    assert report.match_score == 100


@pytest.mark.parametrize(
    "requirements", [[], [Requirement(skill="Python"), Requirement(skill="python3")]]
)
def test_empty_or_duplicate_aliases_rejected(requirements):
    with pytest.raises(ValidationError):
        Job(title="Engineer", requirements=requirements)


@pytest.mark.parametrize(
    "field,value",
    [("weight", 0), ("weight", 11), ("weight", True), ("skill", " "), ("skill", "gender")],
)
def test_invalid_requirements(field, value):
    with pytest.raises(ValidationError):
        Requirement(**{"skill": "Python", field: value})


def test_learning_required_gap_and_low_partial_recommendation():
    report = analyze("Alex Morgan\na@example.com\nSKILLS\nLearning Python", job(), DAY)
    assert report.match_score == 18.75
    assert "Python" in report.missing_required


def test_medium_score_recommendation():
    report = analyze("Alex Morgan\na@example.com\nSKILLS\nPython, Docker", job(), DAY)
    assert report.match_score == 60
    assert "Recruiter review" in report.recommendation
