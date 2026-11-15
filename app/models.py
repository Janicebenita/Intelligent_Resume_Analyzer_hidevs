"""Versioned, validated contracts. Scores never use candidate identity."""

from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Model(BaseModel):
    """Reject unknown fields at every serialization boundary."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Requirement(Model):
    skill: str = Field(min_length=1, max_length=60)
    importance: Literal["required", "preferred"] = "required"
    weight: int = Field(default=1, ge=1, le=10, strict=True)

    @field_validator("skill")
    @classmethod
    def clean_skill(cls, value: str) -> str:
        import re

        value = " ".join(value.split())
        if not value or not any(char.isalnum() for char in value):
            raise ValueError("Enter a named job skill.")
        # Deliberately exclude identity / protected traits from structured requirements.
        from app.skills import BLOCKED_CRITERIA

        if any(
            re.search(r"\b" + re.escape(trait) + r"\b", value, re.I) for trait in BLOCKED_CRITERIA
        ):
            raise ValueError("Use job skills, not personal characteristics.")
        return value


class Job(Model):
    title: str = Field(min_length=2, max_length=120)
    requirements: list[Requirement] = Field(min_length=1, max_length=30)
    minimum_years: float = Field(default=0, ge=0, le=50)
    experience_weight: int = Field(default=20, ge=0, le=50, strict=True)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        if len(value.strip()) < 2:
            raise ValueError("Enter a job title.")
        return value.strip()

    @model_validator(mode="after")
    def unique_requirements(self) -> Self:
        from app.skills import canonical

        names = [canonical(item.skill) for item in self.requirements]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate skills or aliases; keep one requirement per skill.")
        if self.minimum_years == 0 and self.experience_weight != 0:
            self.experience_weight = 0
        return self


class Evidence(Model):
    line: int = Field(ge=1)
    text: str
    section: str


class SkillEvidence(Model):
    skill: str
    status: Literal["evidenced", "mentioned", "learning", "negated", "not_found"]
    evidence: list[Evidence] = Field(default_factory=list)


class Employment(Model):
    start: date
    end: date
    precision: Literal["month", "year"]
    evidence: Evidence

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        if self.start >= self.end or self.start.day != 1 or self.end.day != 1:
            raise ValueError("Employment needs increasing first-of-month interval boundaries.")
        return self


class Resume(Model):
    name: str | None
    email: str | None
    skills: list[SkillEvidence]
    employment: list[Employment]
    experience_months: int = Field(ge=0)
    claimed_years: float | None = None
    warnings: list[str]
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: str
    line_count: int = Field(ge=1, le=100_000)

    @model_validator(mode="after")
    def consistent_evidence(self) -> Self:
        from app.parser import union_months

        if union_months(self.employment) != self.experience_months:
            raise ValueError("Experience months must equal the interval union.")
        names = [item.skill.casefold() for item in self.skills]
        if len(names) != len(set(names)):
            raise ValueError("Skill evidence must be unique.")
        for skill in self.skills:
            if (skill.status == "not_found") != (not skill.evidence):
                raise ValueError("Found skills need source evidence; absent skills must have none.")
        return self


class MatchRow(Model):
    skill: str
    importance: str
    weight: int
    status: str
    factor: float = Field(ge=0, le=1)
    points: float = Field(ge=0, le=100)
    evidence: list[Evidence]


class Analysis(Model):
    schema_version: Literal["1.0"] = "1.0"
    algorithm_version: Literal["rolelens-1.0"] = "rolelens-1.0"
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    created_at: datetime
    as_of: date
    job: Job
    resume: Resume
    match_score: float = Field(ge=0, le=100)
    skills_points: float
    experience_points: float
    rows: list[MatchRow]
    missing_required: list[str]
    recommendation: str
    next_steps: list[str]
    limitations: list[str]
