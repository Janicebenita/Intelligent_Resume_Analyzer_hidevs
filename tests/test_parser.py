"""Labeled extraction cases, dates, alias boundaries and evidence strength."""

from datetime import date

import pytest

from app.parser import parse_resume

AS_OF = date(2025, 1, 1)


@pytest.mark.parametrize("name", ["Alex Morgan", "María García", "O'Neil Patel", "Jean-Luc Martin"])
def test_names_with_unicode_and_punctuation(name):
    result = parse_resume(f"{name}\nuser@example.com\nSKILLS\nPython", [], AS_OF)
    assert result.name == name
    assert result.email == "user@example.com"


@pytest.mark.parametrize(
    "text,status",
    [
        ("Python", "mentioned"),
        ("Currently learning Python.", "learning"),
        ("No Python experience.", "negated"),
        ("Built Python services.", "evidenced"),
        ("Built JavaScript services.", "not_found"),
        ("Built pythonic systems.", "not_found"),
    ],
)
def test_evidence_classification(text, status):
    result = parse_resume(f"Alex Morgan\na@example.com\nPROJECTS\n{text}", ["Python"], AS_OF)
    skill = next(s for s in result.skills if s.skill == "Python")
    assert skill.status == status
    if skill.evidence:
        assert skill.evidence[0].line == 4
        assert skill.evidence[0].text == text


@pytest.mark.parametrize(
    "target,text,found",
    [
        ("Java", "JavaScript", False),
        ("C++", "C++", True),
        ("C++", "C", False),
        ("C#", "C#", True),
        ("Git", "GitHub", False),
        ("SQL", "PostgreSQL", False),
        ("Kubernetes", "k8s", True),
        ("PostgreSQL", "Postgres", True),
        ("a.b", "aXb", False),
        ("a.b", "a.b", True),
    ],
)
def test_aliases_and_substring_collisions(target, text, found):
    result = parse_resume(f"Alex Morgan\na@example.com\nSKILLS\n{text}", [target], AS_OF)
    from app.skills import canonical

    assert (
        next(s for s in result.skills if s.skill == canonical(target)).status != "not_found"
    ) == found


@pytest.mark.parametrize(
    "ranges,months",
    [
        (["Jan 2021 - Dec 2023", "Jul 2023 - Dec 2024"], 48),
        (["01/2020 - 12/2020", "01/2020 - 12/2020"], 12),
        (["January 2020 to March 2020", "Jun 2020 – Aug 2020"], 6),
        (["Jan 2024 - Present"], 12),
        (["2020 - 2022"], 24),
        (["Dec 2024 - Jan 2024"], 0),
        (["Jan 2027 - Present"], 0),
        (["Jan 2024 - Dec 2027"], 12),
        (["2021-01 - 2022-06"], 18),
        (["13/2020 - 01/2021"], 0),
        (["01/2020 - 14/2021"], 0),
    ],
)
def test_employment_union_and_clock(ranges, months):
    result = parse_resume("Alex Morgan\na@example.com\nEXPERIENCE\n" + "\n".join(ranges), [], AS_OF)
    assert result.experience_months == months


def test_education_and_project_dates_are_not_employment():
    text = "Alex Morgan\na@example.com\nEDUCATION\n2010 - 2020\nPROJECTS\nJan 2020 - Dec 2024"
    assert parse_resume(text, [], AS_OF).experience_months == 0


def test_claimed_years_do_not_inflate_dated_experience():
    result = parse_resume(
        "Alex Morgan\na@example.com\nSUMMARY\n20 years of experience.\n"
        "EXPERIENCE\nJan 2024 - Dec 2024",
        [],
        AS_OF,
    )
    assert result.claimed_years == 20
    assert result.experience_months == 12
    assert result.warnings


def test_contact_missing_multiple_and_unstructured():
    missing = parse_resume("RESUME\nSoftware Engineer\nSKILLS\nPython", [], AS_OF)
    assert missing.name is None and missing.email is None
    result = parse_resume(
        "Alex Morgan\na@example.com b@example.com\nBuilt Python services for APIs.", [], AS_OF
    )
    assert result.email == "a@example.com"
    assert any("Multiple" in w for w in result.warnings)
    assert any("headings" in w for w in result.warnings)


def test_negative_and_positive_separate_clauses():
    result = parse_resume(
        "Alex Morgan\na@example.com\nPROJECTS\nNo Java experience; built Python services.",
        ["Java", "Python"],
        AS_OF,
    )
    lookup = {s.skill: s.status for s in result.skills}
    assert lookup["Java"] == "negated"
    assert lookup["Python"] == "evidenced"


@pytest.mark.parametrize(
    "clause,expected",
    [
        ("Currently learning Python, Java and SQL.", ["learning"] * 3),
        ("No experience with Python, Java or SQL.", ["negated"] * 3),
        ("Built Python, Java and SQL services.", ["evidenced"] * 3),
        ("Not learning Python, Java or SQL.", ["negated"] * 3),
        ("No Java, learning Python and SQL.", ["learning", "negated", "learning"]),
        (
            "No Java experience, built Python and SQL services.",
            ["evidenced", "negated", "evidenced"],
        ),
        (
            "Built Java services, currently learning Python and SQL.",
            ["learning", "evidenced", "learning"],
        ),
    ],
)
def test_shared_skill_list_markers_and_clause_resets(clause, expected):
    resume = parse_resume(f"Casey Blake\ncasey@example.com\nPROJECTS\n{clause}", [], AS_OF)
    lookup = {skill.skill: skill.status for skill in resume.skills}
    assert [lookup[name] for name in ["Python", "Java", "SQL"]] == expected


def test_singular_internship_heading_is_employment():
    resume = parse_resume(
        "Casey Blake\ncasey@example.com\nInternship\n"
        "Example Labs | May-Jul 2024\nBuilt Python services.",
        [],
        AS_OF,
    )
    assert resume.experience_months == 3
    assert next(s for s in resume.skills if s.skill == "Python").status == "evidenced"
