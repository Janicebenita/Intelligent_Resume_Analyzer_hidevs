"""Line-provenanced regex parser with explicit uncertainty and interval union."""

import hashlib
import re
import unicodedata
from datetime import date
from typing import Literal

from app.documents import validate_text
from app.models import Employment, Evidence, Resume, SkillEvidence
from app.skills import ALIASES, canonical, skill_pattern

SECTIONS = {
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "internships",
        "internship",
        "internship experience",
        "technical internship experience",
        "relevant experience",
    },
    "projects": {
        "projects",
        "selected projects",
        "personal projects",
        "academic projects",
        "software projects",
        "selected software projects",
        "project experience",
        "selected software projects & external client work",
    },
    "education": {"education", "academic qualifications", "qualifications"},
    "skills": {"skills", "technical skills", "core competencies", "technologies"},
    "summary": {"summary", "profile", "professional summary", "objective"},
    "certifications": {"certifications", "certificates"},
    "other": {
        "achievements",
        "research",
        "publications",
        "awards",
        "achievements, research & technical learning",
    },
}
MONTHS = {
    name: index
    for index, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1
    )
}
MONTH_TOKEN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE_TOKEN = (
    rf"(?:(?:19|20)\d{{2}}-(?:0[1-9]|1[0-2])|"
    rf"(?:{MONTH_TOKEN}\s+|(?:0?[1-9]|1[0-2])[/.-])?(?:19|20)\d{{2}})"
)
RANGE = re.compile(
    rf"(?<![\w/.-])(?P<start>{DATE_TOKEN})\s*(?:-|–|—|\bto\b)\s*"
    rf"(?P<end>{DATE_TOKEN}|present|current|now)\b(?![\w/]|-\d)",
    re.I,
)
SHARED_YEAR_RANGE = re.compile(
    rf"(?<!\w)(?P<start>{MONTH_TOKEN})\s*[-–—\ufffd]\s*"
    rf"(?P<end>{MONTH_TOKEN})\s+(?P<year>(?:19|20)\d{{2}})\b",
    re.I,
)
EMAIL = re.compile(
    r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9.-]*[A-Z0-9])?\.[A-Z]{2,63}\b",
    re.I,
)
LEARNING = re.compile(
    r"\b(?:learning|studying|beginner|introductory|exposure to|familiar with)\b", re.I
)
NEGATION = re.compile(r"\b(?:no|not|without|lack(?:ing)?|never)\b", re.I)
ACTION = re.compile(
    r"\b(?:built|developed|implemented|deployed|designed|maintained|automated|analyzed|"
    r"led|created|tested|used|optimized|managed|delivered|processed|integrated|"
    r"connected|performed|debugged)\b",
    re.I,
)


def annotated_lines(text: str) -> list[Evidence]:
    """Retain original 1-based line numbers while detecting standard section headers."""
    section = "header"
    lines = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = " ".join(raw.split()).strip("• \t")
        if not line:
            continue
        heading = line.casefold().strip(": ")
        for key, names in SECTIONS.items():
            if heading in names:
                section = key
                break
        lines.append(Evidence(line=number, text=line, section=section))
    return lines


def extract_name(lines: list[Evidence]) -> str | None:
    """Conservative header heuristic; never infer a name from an email address."""
    for item in lines[:8]:
        text = re.sub(r"^(?:name|candidate)\s*:\s*", "", item.text, flags=re.I)
        text = re.split(r"\s*[|•]\s*", text)[0].strip()
        if item.section != "header" or EMAIL.search(text) or any(c.isdigit() for c in text):
            continue
        if text.casefold() in {"resume", "curriculum vitae", "cv", "contact information"}:
            continue
        words = text.split()
        allowed = all(c.isalpha() or c in " .'-’" for c in text)
        if 2 <= len(words) <= 5 and allowed and len(text) <= 80:
            if re.search(
                r"\b(engineer|developer|analyst|manager|scientist|consultant)\b", text, re.I
            ):
                continue
            return text
    return None


def extract_skill(skill: str, lines: list[Evidence]) -> SkillEvidence:
    """Evidence strength: action in experience/projects > mention > learning/negated."""
    pattern = skill_pattern(skill)
    found: dict[str, list[Evidence]] = {}
    for line in lines:
        # Exclude contact/header and education dates from skills evidence.
        if line.section == "header":
            continue
        for match in pattern.finditer(line.text):
            # Bound negation to the same short clause, preventing unrelated skill leakage.
            context = re.split(r";|\.(?=\s|$)|\bbut\b", line.text[: match.start()], flags=re.I)[-1][
                -400:
            ]
            # A shared marker applies to a comma-separated skill list. A later
            # action/learning clause starts a new scope, e.g. "No Java, built Python".
            actions = list(ACTION.finditer(context))
            learning = list(LEARNING.finditer(context))
            negatives = list(NEGATION.finditer(context))
            action_at = actions[-1].start() if actions else -1
            learning_at = learning[-1].start() if learning else -1
            negative_at = negatives[-1].start() if negatives else -1
            negated_learning = (
                learning_at > action_at
                and negative_at >= 0
                and 0 < learning_at - negative_at < 20
                and "," not in context[negative_at:learning_at]
            )
            if negative_at > max(action_at, learning_at) or negated_learning:
                status = "negated"
            elif learning_at > action_at:
                status = "learning"
            elif line.section in {"experience", "projects"} and ACTION.search(context):
                status = "evidenced"
            else:
                status = "mentioned"
            found.setdefault(status, []).append(line)
    for status in ("evidenced", "mentioned", "learning", "negated"):
        if status in found:
            evidence = list({item.line: item for item in found[status]}.values())[:3]
            return SkillEvidence(skill=canonical(skill), status=status, evidence=evidence)  # type: ignore[arg-type]
    return SkillEvidence(skill=canonical(skill), status="not_found")


def parse_date(token: str, *, as_of: date, end: bool) -> tuple[date, str]:
    """Past end months are inclusive; Present counts completed calendar months."""
    if token.casefold() in {"present", "current", "now"}:
        return as_of.replace(day=1), "month"
    year = int(re.search(r"(?:19|20)\d{2}", token)[0])  # type: ignore[index]
    iso = re.fullmatch(r"\d{4}-(\d{2})", token)
    month_match = re.match(r"([A-Za-z]+)|([0-9]{1,2})[/.-]", token)
    if iso:
        result = date(year, int(iso[1]), 1)
        precision = "month"
    elif month_match:
        month = MONTHS[month_match[1][:3].casefold()] if month_match[1] else int(month_match[2])
        result = date(year, month, 1)
        precision = "month"
    else:
        # Year-only ranges are conservative: Jan YYYY to Jan YYYY, no invented extra year.
        result = date(year, 1, 1)
        precision = "year"
    if end and precision == "month":
        result = date(result.year + (result.month == 12), result.month % 12 + 1, 1)
    return result, precision


def union_months(intervals: list[Employment]) -> int:
    """Measure union of [start, end) month intervals; concurrent roles count once."""
    spans = sorted(
        (i.start.year * 12 + i.start.month, i.end.year * 12 + i.end.month) for i in intervals
    )
    total = 0
    last_end = -1
    for start, end in spans:
        total += max(0, end - max(start, last_end))
        last_end = max(last_end, end)
    return total


def parse_resume(
    text: str, extra_skills: list[str], as_of: date, source_type: str = "text"
) -> Resume:
    """Extract verifiable fields; missing or ambiguous information remains explicit."""
    text = validate_text(unicodedata.normalize("NFKC", text))
    lines = annotated_lines(text)
    warnings: list[str] = []
    if "\ufffd" in text:
        warnings.append(
            "Some PDF characters could not be decoded. Verify names and date separators "
            "against the original document."
        )
    emails = list(dict.fromkeys(EMAIL.findall(text)))
    name = extract_name(lines)
    if not name:
        warnings.append("Name could not be reliably identified. Confirm it manually.")
    if not emails:
        warnings.append("No valid email found; contact extraction does not affect the score.")
    elif len(emails) > 1:
        warnings.append("Multiple emails found; the first is displayed for manual confirmation.")
    if not any(line.section != "header" for line in lines):
        warnings.append("No standard section headings found; add Skills and Experience headings.")
        # Still support unsectioned evidence, but avoid scoring identity/header lines.
        lines = [
            item.model_copy(update={"section": "summary"}) if item.line > 2 else item
            for item in lines
        ]
    skills = [
        extract_skill(skill, lines)
        for skill in dict.fromkeys(list(ALIASES) + [canonical(skill) for skill in extra_skills])
    ]
    employment: list[Employment] = []
    for item in lines:
        if item.section != "experience":
            continue
        tokens = [(match["start"], match["end"]) for match in RANGE.finditer(item.text)]
        tokens.extend(
            (f"{match['start']} {match['year']}", f"{match['end']} {match['year']}")
            for match in SHARED_YEAR_RANGE.finditer(item.text)
        )
        for start_token, end_token in tokens:
            start, start_precision = parse_date(start_token, as_of=as_of, end=False)
            end, end_precision = parse_date(end_token, as_of=as_of, end=True)
            cutoff = as_of.replace(day=1)
            if start >= end or start >= cutoff:
                warnings.append(
                    f"Ignored reversed, empty or future employment dates on line {item.line}."
                )
                continue
            if end > cutoff:
                warnings.append(
                    f"Employment ending after the analysis date clipped on line {item.line}."
                )
                end = cutoff
            precision: Literal["month", "year"] = (
                "year" if "year" in (start_precision, end_precision) else "month"
            )
            if precision == "year":
                warnings.append("Year-only employment dates are estimates; confirm exact months.")
            employment.append(Employment(start=start, end=end, precision=precision, evidence=item))
    months = union_months(employment)
    claimed = re.search(
        r"\b(\d{1,2}(?:\.\d)?)\+?\s+years?\s+(?:of\s+)?(?:professional\s+|work\s+)?experience\b",
        text,
        re.I,
    )
    claimed_years = float(claimed[1]) if claimed else None
    if not employment:
        warnings.append(
            "No dated employment intervals found under Experience. Experience points remain zero."
        )
    if claimed_years is not None:
        warnings.append(
            "Self-reported years are displayed separately and never substituted for dated evidence."
        )
    return Resume(
        name=name,
        email=emails[0] if emails else None,
        skills=skills,
        employment=employment,
        experience_months=months,
        claimed_years=claimed_years,
        warnings=list(dict.fromkeys(warnings)),
        source_type=source_type,
        source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        line_count=len(text.splitlines()),
    )
