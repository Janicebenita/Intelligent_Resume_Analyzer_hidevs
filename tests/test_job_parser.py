"""Fictional job descriptions exercise drafting, upload boundaries and scoring handoff."""

import io
from datetime import date

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from app.job_parser import extract_job
from app.models import Job
from app.service import analyze
from app.skills import ALIASES

CAMPUS = """Designation: Software Engineering Trainee
Experience: Final-Year Students
Internship duration: 6 months up to 1 year
Eligibility
BTech in related disciplines, CGPA 8.0, no backlogs
KEY SKILLS REQUIRED
DSA and OOP fundamentals
At least one programming language such as Java, Python, C++ or JavaScript
Basic SQL/NoSQL databases
REST APIs, HTML, CSS and Git
PREFERRED SKILLS
Docker
"""


def test_campus_preserves_alternatives_and_fresher_target():
    draft = extract_job(CAMPUS)
    assert draft.title == "Software Engineering Trainee"
    assert draft.minimum_years == draft.experience_weight == 0
    groups = {r.skill: r for r in draft.requirements}
    assert groups["Java OR Python OR C++ OR JavaScript"].alternatives == [
        "Java",
        "Python",
        "C++",
        "JavaScript",
    ]
    assert groups["SQL OR NoSQL"].alternatives == ["SQL", "NoSQL"]
    assert groups["Docker"].importance == "preferred"
    assert "Python" not in groups
    assert draft.fields[0].evidence.line == 1
    job = Job(**draft.model_dump(exclude={"fields", "warnings"}))
    result = analyze(
        "Casey Blake\ncasey@example.com\nPROJECTS\nBuilt Python REST APIs.", job, date(2026, 11, 15)
    )
    assert any(row.matched_alternative == "Python" for row in result.rows)


@pytest.mark.parametrize("word", ["Job title", "Designation", "Position", "Role"])
def test_explicit_title(word):
    assert extract_job(f"{word}: Python Engineer\nRequired: Python").title == "Python Engineer"


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("3+ years of experience", 3),
        ("2-4 years experience", 2),
        ("At least 2.5 years experience", 2.5),
        ("Experience: 6 months", 0.5),
        ("Experience: 3 months", 0.25),
        ("Freshers welcome", 0),
        ("No prior experience required", 0),
    ],
)
def test_experience_targets(phrase, expected):
    draft = extract_job(f"Python Engineer\n{phrase}\nRequired: Python")
    assert draft.minimum_years == expected
    assert draft.experience_weight == (20 if expected else 0)


def test_preferred_benefits_and_unknown_fields_are_not_invented():
    draft = extract_job("""About the company
We build products.
Required skills
Python
Docker preferred
Git
Benefits
Free Java training
Preferred skills
AWS
""")
    assert draft.title == "Untitled role - review"
    skills = {r.skill: r.importance for r in draft.requirements}
    assert skills == {
        "Python": "required",
        "Docker": "preferred",
        "Git": "required",
        "AWS": "preferred",
    }
    assert any("No explicit job title" in w for w in draft.warnings)
    assert any("No reliable required experience" in w for w in draft.warnings)


def test_required_overrides_preferred_and_explicit_lack_is_skipped():
    draft = extract_job("""Software Engineer
Preferred skills
Python
Required skills
Python, SQL
Docker is not required.
""")
    assert {r.skill: r.importance for r in draft.requirements} == {
        "Python": "required",
        "SQL": "required",
    }


def test_unknown_jd_returns_reviewable_empty_draft():
    draft = extract_job("Role: Archivist\nCatalog preservation and book restoration.")
    assert draft.requirements == []
    assert any("No known skills" in w for w in draft.warnings)


@pytest.mark.parametrize(
    "text,warning",
    [
        ("Experience: 2 years\nExperience: 4 years", "Multiple experience"),
        ("Experience: 2 years\nFreshers welcome", "Conflicting experience"),
        ("Experience: 51 years", "No reliable required experience"),
        ("Preferred: 3 years experience", "No reliable required experience"),
    ],
)
def test_ambiguous_experience_is_visible(text, warning):
    assert any(
        warning in w for w in extract_job(f"Python Engineer\n{text}\nRequired: Python").warnings
    )


def test_requirement_limit_and_empty_validation():
    draft = extract_job("Required skills\n" + "\n".join(ALIASES))
    assert len(draft.requirements) == 30
    assert any("first 30" in w for w in draft.warnings)


@pytest.mark.parametrize("kind", ["txt", "pdf", "docx"])
def test_real_jd_uploads(client, kind):
    if kind == "txt":
        content = CAMPUS.encode()
    elif kind == "docx":
        document = Document()
        for line in CAMPUS.splitlines():
            document.add_paragraph(line)
        stream = io.BytesIO()
        document.save(stream)
        content = stream.getvalue()
    else:
        stream = io.BytesIO()
        pdf = canvas.Canvas(stream)
        for i, line in enumerate(CAMPUS.splitlines()):
            pdf.drawString(30, 800 - i * 20, line)
        pdf.save()
        content = stream.getvalue()
    response = client.post("/api/job/extract", files={"file": (f"job.{kind}", content)})
    assert response.status_code == 200
    assert response.json()["draft"]["title"] == "Software Engineering Trainee"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "data,files,code",
    [
        ({"text": "short"}, None, "empty_document"),
        ({"text": CAMPUS}, {"file": ("job.txt", CAMPUS.encode())}, "ambiguous_input"),
        ({}, {"file": ("job.pdf", b"not a PDF")}, "invalid_pdf"),
        ({}, {"file": ("job.exe", b"x" * 20)}, "unsupported_format"),
    ],
)
def test_jd_errors_are_actionable(client, data, files, code):
    response = client.post("/api/job/extract", data=data, files=files)
    assert response.status_code >= 400
    assert response.json()["error"]["code"] == code


def test_pasted_jd_and_no_shared_storage(client):
    response = client.post("/api/job/extract", data={"text": CAMPUS})
    assert response.status_code == 200
    assert set(response.json()) == {"draft"}
