# Evaluation methodology

This release is evaluated against the six Intelligent Resume Analyzer criteria, not a generic GenAI checklist. Its expected stack is Python and regular expressions, verified on the HiDevs project listing and overview on 2026-11-15.

The parser corpus (`tests/fixtures/parser_cases.json`) contains twelve authored synthetic resumes. The evaluation script computes exact match counts for name (including intentional absence), email, complete positive/learning skill set and unique employment months at 2025-01-01. It reports every mismatch and exits nonzero on regression. Cases include accented/hyphenated names, aliases, concurrent roles, ongoing roles, education dates, ISO and numeric dates, negated skills, reversed/future dates and self-reported years.

The dataset is not independent, representative or large enough for a real-world accuracy claim. Real production evaluation would require permissioned, independently annotated resumes across formats, languages, layouts and demographic groups; precision/recall by field; interval-level duration error; subgroup analysis; and recruiter review of evidence and recommendations.

Python tests additionally exercise actual generated PDF and DOCX bytes, not mocked extraction functions. They verify text extraction, table cells, encrypted/image-only/corrupted files, expansion/page/byte limits, scoring arithmetic, identity counterfactuals, JSON corruption and CLI persistence. HTTP tests run real multipart requests through the FastAPI app and validate complete analysis/export/import flows.

The small JavaScript interface has DOM-level tests. These do not replace real browser interaction or layout inspection. Browser checks and deployed smoke results belong in the release record, with exact URLs/commits and any unresolved failures.

The 95% application coverage gate includes branches and the CLI, extraction, HTTP boundary, reports and storage. Passing coverage does not prove semantic correctness, fairness, security or hiring validity.
