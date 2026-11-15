"""Escaped HTML reports and spreadsheet-safe CSV from validated analysis data."""

import csv
import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Analysis

TEMPLATES = Path(__file__).parent / "templates"
ENV = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))


def render_report(report: Analysis, *, standalone: bool = False) -> str:
    """Use the identical report component in the UI and downloadable print report."""
    return ENV.get_template("report.html").render(report=report, standalone=standalone)


def csv_report(report: Analysis) -> str:
    """Export requirement evidence, neutralizing formula-like cell prefixes."""
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(
        [
            "Requirement",
            "Importance",
            "Status",
            "Weight",
            "Points",
            "Matched alternative",
            "Evidence",
        ]
    )
    for row in report.rows:
        values = [
            row.skill,
            row.importance,
            row.status,
            str(row.weight),
            str(row.points),
            row.matched_alternative or "",
            " | ".join(f"L{e.line}: {e.text}" for e in row.evidence),
        ]
        writer.writerow(
            [
                "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
                for value in values
            ]
        )
    return stream.getvalue()
