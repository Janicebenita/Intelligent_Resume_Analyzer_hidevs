# Demo plan — under three minutes

Status: script prepared; no video has been uploaded or submitted.

Use synthetic example data only. Show the actual public deployment and its behavior, then the actual CI result. Do not describe coverage as accuracy or imply that the match score is a HiDevs project score.

1. **0:00–0:20 — Purpose and stack.** “RoleLens is an Intelligent Resume Analyzer built in Python and regular expressions. It turns a resume and a job rubric into evidence a recruiter can inspect. It does not make hiring decisions.” Show the live home screen.
2. **0:20–0:45 — Role and document.** Load the synthetic sample. Explain required versus preferred skills, relative weights and the experience budget. Show a PDF or DOCX upload and analyze it.
3. **0:45–1:15 — Trace the score.** Show the 95-point sample report. Python/FastAPI/Docker have action evidence; Kubernetes is still being learned. Inspect the evidence line numbers. Explain this is alignment to the rubric, not a success probability.
4. **1:15–1:40 — Audit the experience.** Expand employment details. Two concurrent jobs add to 48 unique months, not 54. The resume claims five years, but claims do not replace dated intervals. Contact details do not affect the score.
5. **1:40–2:00 — Personalize and recover.** Change Kubernetes from preferred to required, rerun, and show the gap-focused recommendation. Demonstrate an actionable invalid-input message if time permits.
6. **2:00–2:20 — Save and reopen.** Download JSON, reopen that same file and show the retained rubric/date. Show the printable HTML report and CSV export.
7. **2:20–2:45 — Engineering evidence and boundaries.** Show the latest successful CI run with the real test count, coverage gate and Docker smoke. Mention the small synthetic benchmark, OCR/English-layout limitations, offline CLI and public-demo privacy boundary. State automatic deployment is pending if it still is.

The final recording, narration, exact duration, upload URL and visibility must be verified before this gate can pass. Janice's approval is still required before any HiDevs submission.
