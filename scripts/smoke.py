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
    print("PASS: Python health, analysis, score arithmetic, date union and report export")


if __name__ == "__main__":
    main()
