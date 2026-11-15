"""Reproducible small synthetic extraction benchmark; not real-world validation."""

import json
import sys
from datetime import date
from pathlib import Path
from time import perf_counter

from app.parser import parse_resume

ROOT = Path(__file__).resolve().parents[1]


def evaluate():
    cases = json.loads((ROOT / "tests/fixtures/parser_cases.json").read_text(encoding="utf-8"))
    metrics = {"name": 0, "email": 0, "experience_months": 0, "skill_set": 0}
    failures = []
    start = perf_counter()
    for case in cases:
        result = parse_resume(case["text"], [], date(2025, 1, 1))
        skills = {s.skill for s in result.skills if s.status not in {"not_found", "negated"}}
        actual = {
            "name": result.name,
            "email": result.email,
            "experience_months": result.experience_months,
            "skill_set": sorted(skills),
        }
        expected = {
            "name": case["name"],
            "email": case["email"],
            "experience_months": case["months"],
            "skill_set": sorted(case["skills"]),
        }
        for field in metrics:
            if actual[field] == expected[field]:
                metrics[field] += 1
            else:
                failures.append(
                    {
                        "case": case["id"],
                        "field": field,
                        "expected": expected[field],
                        "actual": actual[field],
                    }
                )
    return {
        "dataset": "12 authored synthetic English resumes; fixed as-of 2025-01-01",
        "case_count": len(cases),
        "exact_matches": metrics,
        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
        "failures": failures,
        "scope": "Regression benchmark only. Authored by the project, not independently labeled. "
        "Does not establish real-world parsing accuracy or hiring validity.",
    }


if __name__ == "__main__":
    result = evaluate()
    path = ROOT / "artifacts/evaluation.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(bool(result["failures"]))
