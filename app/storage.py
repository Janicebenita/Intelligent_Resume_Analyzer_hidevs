"""Validated JSON interchange and atomic local persistence without shared web history."""

import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.errors import AnalysisError
from app.matching import match_resume
from app.models import Analysis

MAX_REPORT_BYTES = 2 * 1024 * 1024


def dump_report(report: Analysis) -> str:
    """Portable UTF-8 JSON including schema, rubric, evidence and date provenance."""
    return report.model_dump_json(indent=2)


def load_report(content: bytes) -> Analysis:
    """Reject unknown schemas, malformed data and internally inconsistent scores."""
    if len(content) > MAX_REPORT_BYTES:
        raise AnalysisError("report_too_large", "The JSON report exceeds 2 MiB.", 413)
    try:
        data = json.loads(content)
        report = Analysis.model_validate(data)
        recalculated = match_resume(report.resume, report.job, report.as_of)
        for field in (
            "match_score",
            "skills_points",
            "experience_points",
            "rows",
            "missing_required",
            "recommendation",
            "next_steps",
            "limitations",
        ):
            if getattr(report, field) != getattr(recalculated, field):
                raise AnalysisError(
                    "inconsistent_report", "The report does not match its scoring rubric."
                )
        return report
    except (json.JSONDecodeError, UnicodeError, ValidationError, TypeError) as error:
        raise AnalysisError(
            "invalid_report", "Upload a valid RoleLens schema 1.0 JSON report."
        ) from error


class JsonRepository:
    """Local CLI storage with opaque identifiers, bounded reads and atomic replacement."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()

    def _path(self, identifier: str) -> Path:
        import re

        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise AnalysisError("invalid_identifier", "Use the report's 32-character identifier.")
        return self.directory / f"{identifier}.json"

    def save(self, report: Analysis) -> Path:
        """Write+fsync a same-directory temp file before atomically replacing the report."""
        destination = self._path(report.id)
        temporary: str | None = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.directory, suffix=".tmp", delete=False
            ) as stream:
                temporary = stream.name
                stream.write(dump_report(report))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            return destination
        except OSError as error:
            raise AnalysisError(
                "storage_unavailable", "Could not save the report. Check folder permissions.", 503
            ) from error
        finally:
            if temporary and Path(temporary).exists():
                Path(temporary).unlink(missing_ok=True)

    def load(self, identifier: str) -> Analysis:
        path = self._path(identifier)
        try:
            with path.open("rb") as stream:
                return load_report(stream.read(MAX_REPORT_BYTES + 1))
        except FileNotFoundError as error:
            raise AnalysisError(
                "report_not_found", "The requested report does not exist.", 404
            ) from error
        except OSError as error:
            raise AnalysisError(
                "storage_unavailable", "Could not read the report. Check folder permissions.", 503
            ) from error
