"""Deterministic scoring: a disclosed rubric, not a probability of job success."""

from datetime import UTC, date, datetime
from uuid import uuid4

from app.models import Analysis, Job, MatchRow, Resume
from app.skills import canonical

FACTORS = {"evidenced": 1.0, "mentioned": 0.6, "learning": 0.25, "negated": 0.0, "not_found": 0.0}
LIMITATIONS = [
    "A match score measures this configured rubric; "
    "it is not a hiring decision or a success probability.",
    "Resume claims are unverified. An action sentence is stronger text evidence, "
    "not proof of proficiency.",
    "Employment duration is total dated employment, not verified years using any particular skill.",
    "English section headings and Gregorian dates are supported. Scanned PDFs need external OCR.",
    "Names, contact details and personal characteristics do not contribute to the match score.",
]


def match_resume(resume: Resume, job: Job, as_of: date) -> Analysis:
    """Allocate the skill budget proportionally; missing evidence never earns full credit."""
    skills_budget = 100 - job.experience_weight
    total_weight = sum(item.weight for item in job.requirements)
    lookup = {canonical(item.skill): item for item in resume.skills}
    rows = []
    missing = []
    for requirement in job.requirements:
        candidates = [
            lookup[canonical(term)] for term in requirement.terms if canonical(term) in lookup
        ]
        evidence = max(candidates, key=lambda item: FACTORS[item.status], default=None)
        status = evidence.status if evidence else "not_found"
        factor = FACTORS[status]
        points = skills_budget * requirement.weight / total_weight * factor
        rows.append(
            MatchRow(
                skill=requirement.skill,
                importance=requirement.importance,
                weight=requirement.weight,
                status=status,
                factor=factor,
                points=round(points, 4),
                evidence=evidence.evidence if evidence else [],
                matched_alternative=(
                    evidence.skill if requirement.alternatives and evidence and factor > 0 else None
                ),
            )
        )
        if requirement.importance == "required" and status in {"not_found", "negated", "learning"}:
            missing.append(requirement.skill)
    skills_points = sum(row.points for row in rows)
    experience_points = (
        (job.experience_weight * min(1, resume.experience_months / (job.minimum_years * 12)))
        if job.minimum_years > 0
        else 0.0
    )
    score = round(min(100, skills_points + experience_points), 2)
    if missing:
        recommendation = "Clarify required-skill gaps before an interview decision"
    elif score >= 80:
        recommendation = "Consider a structured skills interview after verifying the evidence"
    elif score >= 55:
        recommendation = "Recruiter review recommended; validate partial evidence"
    else:
        recommendation = "Request more relevant evidence before proceeding"
    steps = [f"Ask for a concrete example demonstrating {skill}." for skill in missing]
    steps.extend(
        f"Verify practical depth in {row.skill}; it is only {row.status} in the resume."
        for row in rows
        if row.status in {"mentioned", "learning"}
    )
    if job.minimum_years and resume.experience_months < job.minimum_years * 12:
        steps.append(
            "Confirm employment dates and relevance; "
            "dated experience is below the configured target."
        )
    if not steps:
        steps.append(
            "Use the same structured work-sample assessment for every candidate for this role."
        )
    return Analysis(
        id=uuid4().hex,
        created_at=datetime.now(UTC),
        as_of=as_of,
        job=job,
        resume=resume,
        match_score=score,
        skills_points=round(skills_points, 4),
        experience_points=round(experience_points, 4),
        rows=rows,
        missing_required=missing,
        recommendation=recommendation,
        next_steps=steps,
        limitations=LIMITATIONS,
    )
