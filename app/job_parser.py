"""Conservative job-description drafting; recruiters review every extracted field."""

import re
from typing import Literal

from pydantic import Field

from app.documents import validate_text
from app.models import Evidence, Model, Requirement
from app.skills import ALIASES, skill_pattern


class DraftField(Model):
    field: str
    value: str
    evidence: Evidence


class JobDraft(Model):
    title: str
    requirements: list[Requirement] = Field(default_factory=list)
    minimum_years: float
    experience_weight: int
    fields: list[DraftField]
    warnings: list[str]


TITLE = re.compile(r"^(?:job title|designation|position|role)\s*[:–-]\s*(.{2,120})$", re.I)
YEARS = re.compile(
    r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*(?:\+|[-–—]\s*\d{1,2}(?:\.\d+)?)?"
    r"\s*(years?|yrs?|months?)\b",
    re.I,
)
LANGUAGES = {"Python", "Java", "JavaScript", "TypeScript", "C++", "C#"}
PREFERRED = re.compile(r"\b(?:preferred|desirable|nice.to.have|bonus|optional)\b", re.I)
REQUIRED = re.compile(r"\b(?:required|requirements|essential|must.have|key skills)\b", re.I)
SKIP = re.compile(
    r"^(?:benefits|compensation|salary|about (?:us|the company)|equal opportunity|"
    r"eligibility|qualifications|education)(?:\s.*)?$",
    re.I,
)


def extract_job(text: str) -> JobDraft:
    """Draft known skills and explicit experience only; never invent missing fields."""
    text = validate_text(text)
    lines = [
        Evidence(line=i, text=" ".join(raw.strip(" #*•\t").split()), section="job description")
        for i, raw in enumerate(text.splitlines(), 1)
        if raw.strip()
    ]
    warnings = [
        "Review this heuristic draft before applying it. Unrecognized skills may be missing.",
        "Skill weights default to 1; experience receives 20 points only when a positive "
        "target is extracted. These are editable defaults, not employer priorities.",
        "Academic eligibility, location, compensation and availability are not scored. "
        "Check these separately against the original JD.",
    ]
    fields: list[DraftField] = []
    title = "Untitled role - review"
    title_line = -1
    for line in lines:
        match = TITLE.match(line.text)
        if match:
            title, title_line = match[1].strip(), line.line
            break
    if title_line < 0:
        for line in lines[:6]:
            if (
                len(line.text) <= 120
                and re.search(
                    r"\b(?:engineer|developer|analyst|designer|trainee|manager|scientist)\b",
                    line.text,
                    re.I,
                )
                and not re.search(
                    r"\b(?:reporting|seeking|hiring|looking|responsibilities)\b", line.text, re.I
                )
            ):
                title, title_line = line.text, line.line
                break
    if title_line > 0:
        source = next(line for line in lines if line.line == title_line)
        fields.append(DraftField(field="Job title", value=title, evidence=source))
    else:
        warnings.append("No explicit job title found. Enter the title manually.")

    years: float | None = None
    for line in lines:
        if re.search(
            r"\b(?:freshers?|final.year|no (?:prior |professional )?experience)\b", line.text, re.I
        ):
            if years not in {None, 0}:
                warnings.append("Conflicting experience statements found; review the minimum.")
            years = 0
            fields.append(DraftField(field="Minimum years", value="0", evidence=line))
            break
        if "experience" not in line.text.casefold() or PREFERRED.search(line.text):
            continue
        match = YEARS.search(line.text)
        if match:
            candidate = float(match[1]) / (12 if match[2].lower().startswith("month") else 1)
            if candidate <= 50:
                if years is not None and years != candidate:
                    warnings.append(
                        "Multiple experience targets found; review the selected minimum."
                    )
                    continue
                years = candidate
                fields.append(DraftField(field="Minimum years", value=f"{years:g}", evidence=line))
    if years is None:
        years = 0
        warnings.append(
            "No reliable required experience target found; draft minimum is 0. Review it."
        )

    found: dict[str, tuple[Requirement, Evidence]] = {}
    groups: dict[str, tuple[Requirement, Evidence]] = {}
    importance: Literal["required", "preferred"] = "required"
    skip = False
    for line in lines:
        if line.line == title_line:
            continue
        heading = line.text.strip(": ")
        if SKIP.fullmatch(heading):
            skip = True
            continue
        if re.match(r"^(?:preferred|desirable|nice.to.have|bonus|optional)\b", heading, re.I):
            importance, skip = "preferred", False
        elif REQUIRED.search(heading) or re.match(
            r"^(?:skills|responsibilities|experience)\b", heading, re.I
        ):
            importance, skip = "required", False
        if skip:
            continue
        if re.search(r"\b(?:not required|no .{0,30} required)\b", line.text, re.I):
            continue
        local_importance: Literal["required", "preferred"] = (
            "preferred" if PREFERRED.search(line.text) else importance
        )
        skills = sorted(
            (name for name in ALIASES if skill_pattern(name).search(line.text)),
            key=lambda name: skill_pattern(name).search(line.text).start(),  # type: ignore[union-attr]
        )
        alternatives: list[str] = []
        language_members = [name for name in skills if name in LANGUAGES]
        if len(language_members) >= 2 and re.search(
            r"\bor\b|at least one|any one", line.text, re.I
        ):
            alternatives = language_members
        if alternatives:
            label = " OR ".join(alternatives)
            groups[label] = (
                Requirement(skill=label, alternatives=alternatives, importance=local_importance),
                line,
            )
        if {"SQL", "NoSQL"}.issubset(skills) and re.search(
            r"SQL\s*(?:/|or)\s*NoSQL", line.text, re.I
        ):
            groups["SQL OR NoSQL"] = (
                Requirement(
                    skill="SQL OR NoSQL", alternatives=["SQL", "NoSQL"], importance=local_importance
                ),
                line,
            )
        for name in skills:
            if name not in found or local_importance == "required":
                found[name] = (Requirement(skill=name, importance=local_importance), line)
    grouped = {term for requirement, _ in groups.values() for term in requirement.terms}
    entries = list(groups.values()) + [item for name, item in found.items() if name not in grouped]
    entries.sort(key=lambda item: (item[1].line, item[0].skill))
    if len(entries) > 30:
        warnings.append("Only the first 30 recognized requirements are included; review the rest.")
        entries = entries[:30]
    if not entries:
        warnings.append("No known skills found. Add job-relevant requirements manually.")
    for requirement, source in entries:
        fields.append(DraftField(field="Requirement", value=requirement.skill, evidence=source))
    return JobDraft(
        title=title,
        requirements=[item[0] for item in entries],
        minimum_years=years,
        experience_weight=20 if years else 0,
        fields=fields,
        warnings=list(dict.fromkeys(warnings)),
    )
