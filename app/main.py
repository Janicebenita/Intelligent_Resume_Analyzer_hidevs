"""FastAPI boundary: bounded uploads, private responses, structured safe errors."""

import logging
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.demo import DEMO_RESUME, demo_job
from app.documents import MAX_BYTES, extract_document
from app.errors import AnalysisError
from app.job_parser import extract_job
from app.models import Job, Model
from app.reports import ENV, csv_report, render_report
from app.service import analyze
from app.storage import dump_report, load_report

LOGGER = logging.getLogger("rolelens")
BASE = Path(__file__).parent


class PrivacyMiddleware(BaseHTTPMiddleware):
    """Never cache reports; enforce same-origin responses and bound the HTTP body."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        length = request.headers.get("content-length")
        if length and (not length.isdecimal() or int(length) > 3 * 1024 * 1024):
            return JSONResponse(
                {
                    "error": {
                        "code": "request_too_large",
                        "message": "Maximum request size is 3 MiB.",
                    }
                },
                status_code=413,
            )
        # Enforce actual bytes too, including a client that omits Content-Length.
        if request.method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 3 * 1024 * 1024:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "request_too_large",
                                "message": "Maximum request size is 3 MiB.",
                            }
                        },
                        status_code=413,
                    )
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'self' https://huggingface.co; "
            "base-uri 'self'; form-action 'self'; object-src 'none'"
        )
        return response


def create_app() -> FastAPI:
    """Factory keeps routing independently testable and deploys unchanged on Vercel."""
    application = FastAPI(
        title="RoleLens — Intelligent Resume Analyzer",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
    )
    application.add_middleware(PrivacyMiddleware)
    application.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

    @application.exception_handler(AnalysisError)
    async def domain_error(request: Request, error: AnalysisError) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": error.code, "message": error.message}}, status_code=error.status
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {
                "error": {
                    "code": "invalid_input",
                    "message": "Check the job requirements, date and resume fields.",
                }
            },
            status_code=422,
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        # Do not log candidate text, request bodies, filenames or exception messages.
        LOGGER.error("Unhandled application failure: %s", type(error).__name__)
        return JSONResponse(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Analysis could not finish. Try a smaller plain-text resume.",
                }
            },
            status_code=500,
        )

    @application.get("/", response_class=HTMLResponse)
    def home() -> str:
        return ENV.get_template("index.html").render(today=date.today().isoformat())

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": "1.0.0",
            "engine": "python-regex",
            "storage": "download-only",
        }

    @application.get("/api/demo")
    def demo() -> dict[str, object]:
        return {
            "text": DEMO_RESUME,
            "job": demo_job().model_dump(mode="json"),
            "as_of": "2025-01-01",
        }

    @application.post("/api/analyze")
    async def analyze_route(
        job_json: Annotated[str, Form(max_length=12_000)],
        as_of: Annotated[date, Form()],
        text: Annotated[str, Form(max_length=100_000)] = "",
        file: Annotated[UploadFile | None, File()] = None,
    ) -> dict[str, object]:
        try:
            job = Job.model_validate_json(job_json)
        except ValidationError as error:
            # Validation messages may include candidate input. Return a controlled summary.
            raise AnalysisError(
                "invalid_job",
                "Use 1–30 unique job skills, weights 1–10, and 0–50 years. "
                "Personal characteristics are excluded.",
            ) from error
        if as_of > date.today() or as_of < date(1970, 1, 1):
            raise AnalysisError("invalid_date", "Choose an analysis date between 1970 and today.")
        if file is not None and file.filename:
            if text.strip():
                raise AnalysisError("ambiguous_input", "Provide a file or pasted resume, not both.")
            content = await file.read(MAX_BYTES + 1)
            await file.close()
            text, source_type = extract_document(file.filename, content)
        else:
            source_type = "text"
        result = analyze(text, job, as_of, source_type)
        return {"report": result.model_dump(mode="json"), "html": render_report(result)}

    @application.post("/api/job/extract")
    async def extract_job_route(
        text: Annotated[str, Form(max_length=100_000)] = "",
        file: Annotated[UploadFile | None, File()] = None,
    ) -> dict[str, object]:
        if file is not None and file.filename:
            if text.strip():
                raise AnalysisError("ambiguous_input", "Provide a JD file or pasted JD, not both.")
            content = await file.read(MAX_BYTES + 1)
            await file.close()
            text, _ = extract_document(file.filename, content)
        draft = extract_job(text)
        return {"draft": draft.model_dump(mode="json")}

    class ExportRequest(Model):
        report_json: str
        format: str

    @application.post("/api/export")
    def export(payload: ExportRequest) -> Response:
        report = load_report(payload.report_json.encode())
        if payload.format == "json":
            content, media, extension = dump_report(report), "application/json", "json"
        elif payload.format == "html":
            content, media, extension = render_report(report, standalone=True), "text/html", "html"
        elif payload.format == "csv":
            content, media, extension = csv_report(report), "text/csv", "csv"
        else:
            raise AnalysisError("invalid_export", "Choose JSON, HTML or CSV.")
        return Response(
            content,
            media_type=media,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="rolelens-{report.id[:8]}.{extension}"'
                )
            },
        )

    @application.post("/api/import")
    async def import_report(file: Annotated[UploadFile, File()]) -> dict[str, object]:
        content = await file.read(MAX_BYTES + 1)
        await file.close()
        result = load_report(content)
        return {"report": result.model_dump(mode="json"), "html": render_report(result)}

    return application


app = create_app()
