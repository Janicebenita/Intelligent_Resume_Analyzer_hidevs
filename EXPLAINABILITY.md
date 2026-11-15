# RoleLens Explainability

## Decision

RoleLens calculates a resume-to-role alignment score
between 0 and 100 using a deterministic weighted scoring
algorithm. The score combines skill evidence and employment
duration according to the recruiter-defined job rubric.

Skills receive different evidence factors: 1.00 for
demonstrated evidence, 0.60 for mentions, 0.25 for learning
references, and 0.00 for missing or negated evidence.

The application also checks required skill gaps and
generates follow-up recommendations. Its thresholds and
weights are explicit design choices rather than empirically
calibrated hiring predictions.

## Inputs

RoleLens accepts PDF, DOCX, and TXT resume documents.
It extracts names, email addresses, skills, employment
history, and relevant text evidence using Python,
regular expressions, and document extraction libraries.

The recruiter supplies a job rubric containing required
and preferred skills, aliases, skill weights, experience
targets, and budget allocation. Employment dates are
normalized into month intervals, with overlapping periods
merged to prevent double-counting.

The application produces versioned JSON reports, HTML
reports, and CSV exports. Imported JSON reports undergo
schema and score-consistency validation.

## Limitations

RoleLens uses rule-based extraction rather than an external
large language model. Unusual names, complex document
layouts, mixed-language resumes, and unconventional date
formats may cause extraction errors.

Scanned PDFs require external OCR because this release
does not include an OCR engine. Recognized resume claims
are not independently verified, and keyword matches do
not prove actual skill proficiency.

The scoring algorithm measures alignment with the
configured rubric, not job-success probability or
candidate ability. Its thresholds and evidence factors
have not been empirically calibrated.

JSON validation does not authenticate the report author
or prove that the original resume is genuine. The public
hosted demonstration is intended for synthetic data,
not real candidate information.

RoleLens must remain a human-supervised decision-support
tool. It must not autonomously reject candidates or make
high-stakes hiring decisions.
