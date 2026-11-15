"""Real multipart API, browser response contract and private exports end to end."""

import json
from unittest.mock import patch

import pytest

from app.demo import DEMO_RESUME, demo_job
from tests.test_documents import docx_bytes, pdf_bytes


def payload(**extra):
    return {"job_json": demo_job().model_dump_json(), "as_of": "2025-01-01", **extra}


def test_home_health_demo_and_assets(client):
    home = client.get("/")
    assert home.status_code == 200 and "RoleLens" in home.text
    assert home.headers["cache-control"] == "no-store"
    assert "object-src 'none'" in home.headers["content-security-policy"]
    assert client.get("/health").json()["engine"] == "python-regex"
    assert client.get("/api/demo").json()["text"] == DEMO_RESUME
    assert client.get("/static/app.js").status_code == 200


def test_complete_analysis_export_import_flow(client):
    response = client.post("/api/analyze", data=payload(text=DEMO_RESUME))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["report"]["match_score"] == 95
    assert result["report"]["resume"]["experience_months"] == 48
    assert "Kubernetes" in result["html"] and "L9" in result["html"]
    report_json = json.dumps(result["report"])
    for format_, media in [
        ("json", "application/json"),
        ("html", "text/html"),
        ("csv", "text/csv"),
    ]:
        exported = client.post("/api/export", json={"report_json": report_json, "format": format_})
        assert exported.status_code == 200, exported.text
        assert media in exported.headers["content-type"]
        assert "attachment" in exported.headers["content-disposition"]
        if format_ == "json":
            reopened = client.post("/api/import", files={"file": ("report.json", exported.content)})
            assert reopened.status_code == 200
            assert reopened.json()["report"] == result["report"]
    invalid = client.post("/api/export", json={"report_json": report_json, "format": "exe"})
    assert invalid.status_code == 422


@pytest.mark.parametrize(
    "name,content",
    [
        ("resume.pdf", pdf_bytes()),
        ("resume.docx", docx_bytes()),
        ("resume.txt", DEMO_RESUME.encode()),
    ],
)
def test_real_file_uploads(client, name, content):
    response = client.post("/api/analyze", data=payload(), files={"file": (name, content)})
    assert response.status_code == 200, response.text
    assert response.json()["report"]["resume"]["email"] == "alex.morgan@example.com"


@pytest.mark.parametrize(
    "data,code",
    [
        (payload(text=""), "empty_document"),
        (payload(text=DEMO_RESUME, as_of="2099-01-01"), "invalid_date"),
        (payload(text=DEMO_RESUME, as_of="1960-01-01"), "invalid_date"),
        (payload(text=DEMO_RESUME, job_json="{}"), "invalid_job"),
        ({"text": DEMO_RESUME}, "invalid_input"),
    ],
)
def test_api_input_errors(client, data, code):
    response = client.post("/api/analyze", data=data)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code
    assert "alex.morgan" not in response.text


def test_api_ambiguous_file_and_text(client):
    response = client.post(
        "/api/analyze", data=payload(text=DEMO_RESUME), files={"file": ("x.txt", b"other")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ambiguous_input"


def test_request_size_and_internal_exception_do_not_leak(client):
    response = client.post("/api/analyze", content=b"x" * (3 * 1024 * 1024 + 1))
    assert response.status_code == 413
    with patch("app.main.analyze", side_effect=RuntimeError("private candidate secret")):
        response = client.post("/api/analyze", data=payload(text=DEMO_RESUME))
    assert response.status_code == 500
    assert "private candidate secret" not in response.text


def test_invalid_import_and_empty_upload(client):
    response = client.post("/api/import", files={"file": ("report.json", b"garbage")})
    assert response.status_code == 422
    response = client.post("/api/analyze", data=payload(), files={"file": ("x.txt", b"")})
    assert response.status_code == 422
