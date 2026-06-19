# Known Gaps

Things intentionally deferred, with a one-line reason. No `TODO` comments are
left in committed code — they live here instead.

- **Scenario/coding questions are not auto-graded.** Only `mcq` and `short`
  questions are auto-graded (normalized exact match). `scenario`/`coding`
  answers are stored but contribute 0 marks — a manual grading UI/endpoint is
  out of scope for this build.
- **Assessments allow unlimited attempts.** Each submit creates a new result
  row; there is no attempt cap or "best/latest" selection. Kept simple so the
  demo can retake freely.
