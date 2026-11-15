# Release readiness

Status: **application verified, public walkthrough published, and HiDevs submission confirmed on 2026-11-15; evaluation pending**.

The JD workflow was introduced at `b55d39e` (algorithm rolelens-1.1). The subsequent pre-submission audit fixes shared negation/learning markers in comma-separated skill lists and recognizes the singular Internship heading. Latest commit checks are available in GitHub Actions.

| Gate | Verified evidence |
|---|---|
| Required stack | Python + regular expressions; FastAPI backend on Vercel |
| JD import | PDF/DOCX/TXT or pasted English text → reviewable draft → source evidence → explicit apply to editable rubric |
| JD boundaries | Curated skills only; defaults and omissions disclosed; no autonomous eligibility checks; original JD file not retained in analysis exports |
| Python checks | 160 tests, 98.28% combined line/branch coverage; strict mypy and Ruff passed |
| UI checks | Ten DOM behavior tests; ESLint and formatting passed |
| Labeled parsing evaluation | All 12 authored synthetic cases passed; not independent production validation |
| Linux CI and container | [Run 43737141748](https://github.com/Janicebenita/Intelligent_Resume_Analyzer_hidevs/actions/runs/43737141748): quality and container jobs succeeded |
| Public deployment | [RoleLens](https://rolelens-resume-mu.vercel.app), production READY; deployment `dpl_5puafz8Vus1E43VnQLZmVtcRcoiq` at reviewed source |
| Live flow | HTTP smoke includes JD extraction → OR matching; browser upload → review → apply → fictional resume result verified at 78.33 for the authored default rubric |
| JSON and reports | Actual JSON/CSV/HTML downloads, validated JSON reopen, and offline atomic save/reopen verified |
| New public video | [Updated walkthrough](https://youtu.be/Pqh0LnDSt_I), 3:37, 1920×1080 H.264/AAC, 48 kHz audio; HD complete; YouTube checks reported no issues |
| Channel replacement | New video visible first on @JaniceBenita-d6x Videos tab; previous video zbdmmfNSYxw saved as Unlisted |
| Submission video duration | Janice explicitly instructed that video duration is not a constraint and selected the full 3:37 walkthrough. The published guidelines still say under three minutes; this difference is recorded rather than represented as compliance. |
| HiDevs | Submission confirmed on 2026-11-15. The site displayed "Submission successful" and said review would follow within 24 hours. No official score or approval has been issued. |

The video uses actual verified browser screenshots and command outputs, fictional JD/candidate examples and Indian English male neural synthetic narration (en-IN-PrabhatNeural). It is not continuous screen recording and does not claim a human narrator. Detail-view pairs are labeled. Measured scene audio controls the timeline; each screen remains visible through its narration, with silent margins around transitions. Full decode completed without errors. Audio peak was -1.1 dBFS, without clipping. See the transcript and timeline for the exact narration and source screens.

The public demo is unauthenticated and intended for synthetic data. Real resume files and private analyses remain outside the tracked repository and deployment. JD drafts need recruiter review: unknown technologies and ambiguous wording can be missed, and defaults are not employer-approved priorities. No OCR, LLM, automated hire/reject, calibrated success prediction or durable shared cloud report library is claimed.

Vercel Hobby is the approved hosting target; no paid upgrade or billable add-on was activated. The existing Git integration is restricted to the user-approved repository selection. Vercel builds and GitHub checks run independently; an enforced deployment gate is not claimed.

## Criterion-focused pre-submission review

All six published criteria have implementation and test evidence: modular typed Python; contact/skill/date extraction; independently calculated weighted scores; actual JSON save/reopen; professional evidence reports and follow-ups; bounded invalid-input recovery. New adversarial checks cover shared learning/negation lists, positive-clause resets, and singular internship headings. A local spot-check of a permissioned user-provided PDF passed expected extraction checks; the document and personal analysis are not published. This is one spot-check, not an independent accuracy benchmark.

The video accurately records the earlier b55d39e build and its 152-test count. The eight later regression cases improve existing parsing behavior without changing the demonstrated workflow or sample results. The 160-test current suite supersedes that historical count. No project score has been awarded by HiDevs at this stage.

## Submitted release

Submitted repository: https://github.com/Janicebenita/Intelligent_Resume_Analyzer_hidevs

Submitted demo: https://youtu.be/Pqh0LnDSt_I

Submitted application source: `d42d38270fe8c4bc8208da7d00ebb204e9cb1029`. [Quality/container run 43739341513](https://github.com/Janicebenita/Intelligent_Resume_Analyzer_hidevs/actions/runs/43739341513) passed. Vercel deployment `dpl_FbDNHDrDubwudKwtajopmGd8XrD1` was production READY. Live API probes independently confirmed 25/0/100 points for a shared learning list, shared negated list and action-evidence list respectively. [Submission receipt](submission-receipt.json) records the observed confirmation; it is not an evaluation result.
