"""Offline CLI using the same parser, scorer and versioned JSON repository."""

import argparse
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from app.documents import MAX_BYTES, extract_document
from app.errors import AnalysisError
from app.models import Job
from app.reports import render_report
from app.service import analyze
from app.storage import JsonRepository, dump_report


def main(argv: list[str] | None = None) -> int:
    """Analyze a file or reopen a saved report; never send documents to an API."""
    parser = argparse.ArgumentParser(description="RoleLens offline resume analysis")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--job", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--store", type=Path, default=Path("data"))
    parser.add_argument("--load", help="Reopen a saved report ID")
    parser.add_argument("--html", type=Path, help="Write a printable HTML report")
    args = parser.parse_args(argv)
    try:
        repository = JsonRepository(args.store)
        if args.load:
            result = repository.load(args.load)
        elif args.resume and args.job:
            with args.resume.open("rb") as stream:
                text, source_type = extract_document(args.resume.name, stream.read(MAX_BYTES + 1))
            with args.job.open("rb") as stream:
                job = Job.model_validate_json(stream.read(12_001))
            result = analyze(text, job, args.as_of, source_type)
            repository.save(result)
        else:
            parser.error("Provide --resume and --job, or --load REPORT_ID.")
        if args.html:
            args.html.write_text(render_report(result, standalone=True), encoding="utf-8")
        print(dump_report(result))
        return 0
    except (AnalysisError, OSError, ValidationError) as error:
        message = (
            error.message
            if isinstance(error, AnalysisError)
            else "Could not read or write valid input files."
        )
        print(f"RoleLens: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
