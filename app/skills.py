"""Curated aliases and bounded regex matching; no fuzzy identity inference."""

import re

ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python", "python3", "python 3"),
    "JavaScript": ("javascript", "ecmascript"),
    "TypeScript": ("typescript",),
    "Java": ("java",),
    "Data Structures and Algorithms": (
        "data structures and algorithms",
        "data structures & algorithms",
        "dsa",
    ),
    "Object-Oriented Programming": (
        "object-oriented programming",
        "object oriented programming",
        "oop",
        "oops",
    ),
    "HTML": ("html", "html5"),
    "CSS": ("css", "css3"),
    "NoSQL": ("nosql", "no sql"),
    "Debugging": ("debugging", "debugged", "troubleshooting", "troubleshoot"),
    "Problem Solving": ("problem solving", "problem-solving", "analytical thinking"),
    "Teamwork": ("teamwork", "collaboration", "collaborated"),
    "Agile/Scrum": ("agile", "scrum", "agile/scrum"),
    "C++": ("c++", "cpp"),
    "C#": ("c#", "c sharp"),
    "SQL": ("sql", "structured query language"),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "MongoDB": ("mongodb", "mongo db"),
    "FastAPI": ("fastapi", "fast api"),
    "Django": ("django",),
    "Flask": ("flask",),
    "React": ("react", "reactjs", "react.js"),
    "Node.js": ("node.js", "nodejs"),
    "Git": ("git",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure", "microsoft azure"),
    "GCP": ("gcp", "google cloud", "google cloud platform"),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Machine Learning": ("machine learning",),
    "PyTorch": ("pytorch",),
    "TensorFlow": ("tensorflow",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "REST APIs": ("rest api", "rest apis", "restful api", "restful apis"),
    "Testing": ("pytest", "unit testing", "automated tests", "automated testing"),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery"),
    "Excel": ("excel", "microsoft excel"),
    "Power BI": ("power bi", "powerbi"),
    "Tableau": ("tableau",),
    "Communication": (
        "communication",
        "communicated",
    ),
    "Leadership": ("leadership",),
}
BLOCKED_CRITERIA = {
    "age",
    "gender",
    "sex",
    "religion",
    "race",
    "ethnicity",
    "nationality",
    "marital status",
    "disability",
    "pregnancy",
    "caste",
    "name",
    "email",
    "date of birth",
    "address",
    "school prestige",
    "photograph",
    "citizenship",
}


def canonical(value: str) -> str:
    """Resolve known aliases, preserving explicit custom job skills."""
    folded = " ".join(value.casefold().split())
    for name, aliases in ALIASES.items():
        if folded == name.casefold() or folded in aliases:
            return name
    return folded


def skill_pattern(skill: str) -> re.Pattern[str]:
    """Escape custom text and prevent Java/JavaScript or C++ substring collisions."""
    name = canonical(skill)
    choices = ALIASES.get(name, (name,))
    terms = "|".join(re.escape(term) for term in sorted(choices, key=len, reverse=True))
    return re.compile(r"(?<![\w+#])(?:" + terms + r")(?![\w+#])", re.IGNORECASE)
