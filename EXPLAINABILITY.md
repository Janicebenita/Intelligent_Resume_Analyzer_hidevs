content = """# EXPLAINABILITY.md

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

Employment calculations use dated employment evidence rather than accepting a candidate's self-reported total experience as
