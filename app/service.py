"""Application orchestration shared by web, CLI and evaluation scripts."""

from datetime import date

from app.matching import match_resume
from app.models import Analysis, Job
from app.parser import parse_resume


def analyze(text: str, job: Job, as_of: date, source_type: str = "text") -> Analysis:
    """Parse once, match once; inject the clock for reproducible comparisons."""
    resume = parse_resume(text, [item.skill for item in job.requirements], as_of, source_type)
    return match_resume(resume, job, as_of)
