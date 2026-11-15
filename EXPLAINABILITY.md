## 1. System Overview

RoleLens is a deterministic, evidence-based resume analysis application built with Python and FastAPI. It extracts candidate information from uploaded resumes, evaluates detected skills against a recruiter-defined job rubric, calculates employment duration, and generates traceable analysis reports.

The application does not depend on an external large language model, generative AI API, or vector database to make its matching decisions. Its analysis is based on document extraction, regular-expression parsing, evidence classification, validated data models, and deterministic weighted calculations.

## 2. Decision

RoleLens calculates a candidate-to-job match score using two components: skill evidence and employment experience. The skill component uses recruiter-configured required and preferred skills, skill aliases, individual weights, and evidence factors.

For each skill, the implementation classifies available resume evidence into one of four categories:

- **Evidenced (1.00):** The skill appears after a recognized action verb in an Experience or Projects clause.
- **Mentioned (0.60):** The skill is present in the resume but without qualifying action evidence.
- **Learning (0.25):** The skill appears alongside a learning or familiarity indicator.
- **Negated or Not Found (0.00):** The resume explicitly negates the skill or contains no matching evidence.

The skill score is calculated using the configured experience budget and skill weights:

`Skill points = (100 - E) × (skill weight / total skill weights) × evidence factor`

Here, `E` represents the experience budget, configured between 0 and 50.

Experience points are calculated using unique employment months and the target experience specified in the job rubric:

`Experience points = E × min(1, unique employment months / (12 × target years))`

The final match score is the sum of skill points and experience points, rounded to two decimal places and capped at 100.

The matching implementation also generates follow-up recommendations. If a required skill is missing, negated, or only classified as learning, the recommendation is adjusted to request clarification about the skill gap rather than relying solely on the numerical score.

The score thresholds of 80 and 55, along with the evidence factors, are explicit design choices. They are not empirically calibrated hiring thresholds, and the score is not a probability of job success.

## 3. Inputs

The analysis begins with a resume supplied as a PDF, DOCX, TXT file, or supported text input. The document-processing component in `app/documents.py` checks format signatures and applies size, page, and document-expansion limits before extracting text.

The parser and skill-processing components in `app/parser.py` and `app/skills.py` identify candidate information, email addresses, skill mentions, aliases, employment clauses, and date evidence. The implementation retains source evidence with line references, section context, evidence strength, source hash, and analysis date so that reviewers can trace how findings were produced.

The matching process also receives a validated job rubric. This rubric contains required and preferred skills, skill aliases, skill weights, target experience, and an experience budget. The Pydantic models in `app/models.py` define the input contracts, validate data, and enforce model invariants.

Employment calculations use dated employment evidence rather than accepting a candidate's self-reported total experience as proof. Education and project periods are excluded from the employment-month calculation.

## 4. Processing and Implementation

The application follows a defined processing pipeline:

1. **Document validation:** Check the uploaded file's format signature and enforce extraction limits.
2. **Text extraction:** Extract supported PDF, DOCX, and TXT content.
3. **Candidate parsing:** Identify names, email addresses, skills, aliases, and employment information.
4. **Evidence classification:** Associate detected skills with their source clauses and classify the strength of the evidence.
5. **Experience calculation:** Interpret employment dates and calculate unique employment months.
6. **Rubric validation:** Validate job requirements, weights, and experience settings.
7. **Deterministic matching:** Apply the evidence factors, skill weights, and experience formula.
8. **Analysis validation:** Build a versioned analysis model and check its score consistency.
9. **Report generation:** Produce HTML, CSV, and JSON representations of the analysis.
10. **Delivery and persistence:** Return results through the FastAPI interface or CLI and support local JSON storage and interchange.

The `app/service.py` module provides shared orchestration for the web application, command-line interface, and evaluation workflow. The `app/main.py` and `app/cli.py` modules provide the HTTP and command-line entry points.

## 5. Employment Experience Reasoning

Employment dates are interpreted as half-open month intervals. Past employment end months are treated as inclusive, while Present employment counts completed months.

The implementation unions overlapping employment intervals so that concurrent jobs do not cause the same calendar months to be counted more than once. Education and project periods are excluded from this calculation.

When only years are available, January boundaries are used and an uncertainty warning is recorded. A resume statement such as "15 years of experience" does not replace the dated employment evidence.

The resulting total employment duration is not treated as verified experience in any particular skill. Skill-specific evidence and total employment duration remain separate parts of the analysis.

## 6. Evidence and Traceability

RoleLens preserves evidence supporting extracted candidate details and skill classifications. Source line references, section context, evidence strength, source hash, and analysis date help a reviewer identify where the system obtained its findings.

The system distinguishes between a skill that is demonstrated through an action-oriented clause and a skill that is merely listed or associated with learning. This distinction affects the numerical contribution of each skill to the match score.

The application provides an auditable calculation rather than an unexplained recommendation. Reviewers can inspect the skill evidence, configured weights, experience contribution, and resulting score to understand how the analysis was produced.

## 7. Reports, Validation, and Storage

The `app/reports.py` module and `app/templates/` directory generate HTML reports and support safe CSV and JSON output. HTML rendering uses escaping, and CSV output applies protections against spreadsheet formula injection.

The `app/storage.py` module supports JSON interchange, schema validation, consistency checks, and atomic local JSON persistence. The versioned analysis model preserves the original rubric and analysis date when reports are exported and imported.

The public web application deliberately does not maintain a shared server-side report library. Users can export and reopen JSON reports without exposing one visitor's report to another. The application does not claim durable cloud storage because serverless filesystems may be ephemeral.

The repository's tests cover document uploads, independently calculated scores, overlapping employment dates, candidate extraction, aliases, substring collisions, JSON round trips, malformed imports, path traversal, permission errors, HTML escaping, CSV formula handling, HTTP privacy headers, and offline CLI operation.

## 8. Limitations

RoleLens uses deterministic parsing and rule-based evidence classification. It does not understand every possible resume structure or the full semantic meaning of every sentence, and its English-centric heuristics may miss skills or misclassify unusual wording.

Scanned PDFs require external OCR before their contents can be analyzed. Extracted claims are not independently verified, and the application cannot establish whether a candidate genuinely possesses a listed skill or performed a described responsibility.

The employment calculation estimates total dated employment duration. It does not prove continuous employment, professional competence, or the number of years spent using a specific technology. Year-only dates also introduce uncertainty.

The evidence factors, skill weights, and recommendation thresholds are configurable design choices rather than scientifically validated hiring criteria. A match score must not be interpreted as a probability of hiring success, job performance, or candidate suitability.

The public application does not provide a shared persistent report library. JSON report files are portable data and should not be treated as authenticated records merely because they pass schema validation.

The system is not an autonomous hiring or rejection system. Recruiters and authorized human reviewers must inspect the source evidence, consider contextual information, verify candidate claims, and make all employment decisions. RoleLens should be used as an assistive analysis tool rather than a replacement for human judgment.

## 9. Human Oversight

The final responsibility for interpreting the analysis rests with the human reviewer. Recruiters should verify important evidence against the original resume, examine missing or uncertain information, and assess whether the configured job rubric reflects the actual position.

A numerical score or automated recommendation must never be the sole basis for rejecting or selecting a candidate. The purpose of RoleLens is to make resume analysis more structured, traceable, and explainable while keeping employment decisions under human control.
"""
path = "/mnt/data/EXPLAINABILITY.md"
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print(f"Created {path} ({len(content)} characters)")
