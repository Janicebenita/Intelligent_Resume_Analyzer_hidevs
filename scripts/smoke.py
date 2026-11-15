"""Dependency-free deployment smoke test using synthetic data only."""

import argparse
import json
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:7860")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    def read(path, data=None, media="application/x-www-form-urlencoded"):
        request = urllib.request.Request(base + path, data=data, headers={"Content-Type": media})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()

    assert json.loads(read("/health"))["engine"] == "python-regex"
    demo = json.loads(read("/api/demo"))
    body = urllib.parse.urlencode(
        {"job_json": json.dumps(demo["job"]), "as_of": demo["as_of"], "text": demo["text"]}
    ).encode()
    result = json.loads(read("/api/analyze", body))
    assert result["report"]["match_score"] == 95
    assert result["report"]["resume"]["experience_months"] == 48
    report = json.dumps(result["report"])
    exported = read(
        "/api/export",
        json.dumps({"report_json": report, "format": "html"}).encode(),
        "application/json",
    )
    assert b"<!doctype html>" in exported and b"Kubernetes" in exported
    draft = json.loads(
        read(
            "/api/job/extract",
            urllib.parse.urlencode(
                {
                    "text": "Job title: Software Engineering Trainee\n"
                    "Experience: Freshers\nRequired skills: Java or Python"
                }
            ).encode(),
        )
    )["draft"]
    job = {key: value for key, value in draft.items() if key not in {"fields", "warnings"}}
    matched = json.loads(
        read(
            "/api/analyze",
            urllib.parse.urlencode(
                {"job_json": json.dumps(job), "as_of": demo["as_of"], "text": demo["text"]}
            ).encode(),
        )
    )["report"]
    assert matched["match_score"] == 100
    assert matched["rows"][0]["matched_alternative"] == "Python"
    print("PASS: Python health, analysis, date union, export and JD draft-to-match flow")


if __name__ == "__main__":
    main()
