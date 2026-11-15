"""Authored synthetic examples. No real candidate data is distributed."""

from app.models import Job, Requirement

DEMO_RESUME = """Alex Morgan
alex.morgan@example.com
SUMMARY
Backend developer with 5 years of experience delivering reliable web services.
SKILLS
Python, PostgreSQL, Docker, Git, AWS, FastAPI
EXPERIENCE
Backend Developer | Example Cloud Labs | Jan 2021 - Dec 2023
Built Python and FastAPI services backed by PostgreSQL for an inventory platform.
Implemented automated tests with pytest and maintained CI/CD pipelines.
Software Engineer | Sample Systems | Jul 2023 - Dec 2024
Deployed Docker services and designed REST APIs with Python.
PROJECTS
Built an open-source Python log analyzer with automated tests.
Currently learning Kubernetes.
EDUCATION
BSc Computer Science | Example University | 2017 - 2020
"""


def demo_job() -> Job:
    """A fully editable rubric with a deliberate Kubernetes evidence gap."""
    return Job(
        title="Backend Python Engineer",
        minimum_years=4,
        experience_weight=20,
        requirements=[
            Requirement(skill=skill, weight=weight)
            for skill, weight in [
                ("Python", 3),
                ("FastAPI", 2),
                ("PostgreSQL", 2),
                ("Docker", 2),
                ("Testing", 2),
            ]
        ]
        + [Requirement(skill="Kubernetes", importance="preferred", weight=1)],
    )
