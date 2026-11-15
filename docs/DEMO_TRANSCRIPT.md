# RoleLens demo transcript

Narrated walkthrough using actual browser screenshots and synthetic candidate data. Windows synthetic voice. This is not continuous screen recording.

## 01 / PURPOSE

Meet RoleLens, an Intelligent Resume Analyzer built in Python and regular expressions. It turns a resume and a job rubric into evidence a recruiter can inspect. This walkthrough uses actual browser screenshots and synthetic candidate data. It does not make hiring decisions.

## 02 / PERSONALIZATION

Start with job relevant skills, mark them required or preferred, and assign relative weights. Configure the experience target before reviewing the resume. Upload a text based PDF, DOCX or text file, or paste text. The public Python deployment supports all three document formats.

## 03 / MATCHING

The sample scores ninety five against this role. That is a resume alignment score, not a project evaluation score or a probability of success. Action evidence gets full credit, mentions receive partial credit, and learning receives less. Every requirement links to the source lines behind it.

## 04 / PARSING

Employment intervals are merged before duration is calculated. These overlapping jobs contribute forty eight unique months, rather than fifty four. The resume claims five years, but claims never replace dated evidence. Name and email are extracted separately and do not contribute to the score.

## 05 / RECOMMENDATIONS

Now make Kubernetes required. The numerical score stays the same because its weight did not change, but the recommendation changes. The system asks the recruiter to clarify the required skill gap before an interview decision. This keeps a high total from hiding a missing requirement.

## 06 / JSON AND REPORTS

Export a versioned JSON report and reopen that same file to retain its original rubric and analysis date. Imports validate the schema and check score consistency. The offline command line saves JSON atomically. Printable HTML includes the audit details, and CSV exports neutralize spreadsheet formulas.

## 07 / ENGINEERING

Verification covers extraction, independently calculated scores, invalid inputs, JSON storage, HTTP uploads, exports and the offline command line. The release has one hundred and five Python tests and six interface behavior tests. Continuous integration also builds the production container and exercises its HTTP flow.

## 08 / RESPONSIBLE USE

Damaged, encrypted, empty and unsupported files produce actionable errors. Scanned PDFs need external OCR, and unusual layouts still require review. The twelve case synthetic benchmark is a regression check, not proof of real world accuracy. Use the offline tool for real candidate data. RoleLens makes the evidence clearer while the recruiter remains accountable.
