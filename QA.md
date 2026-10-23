# Verification record — 22 October 2026

- 210 active entries: exactly 70 English, 70 Russian and 70 Kazakh, with unique stable IDs.
- Every English string matches its upstream source row verbatim. Categories, duplicates and blank source IDs are preserved.
- The source CSV checksum matches the file fetched at the recorded upstream commit.
- Six dataset integrity tests and four HTTP/API contract tests passed. API contract tests use explicitly mocked model output, not measured model responses.
- Python compilation and JavaScript syntax checks passed.
- Browser checks confirmed language/category filtering, Kazakh prompt display, and insertion of the selected prompt into the chat composer.
- Live inference check at the initial 8,192-token context setting timed out. The UI correctly marked the run interrupted with zero completed responses. This is not a successful benchmark.
- The final configuration uses 4,096 context tokens to reduce local resource requirements. Real inference at that setting, completed-run export, and the manual-review UI flow have not been revalidated in this update.
- The full 420-response experiment has not been run. No new scores are claimed.
- Translations were produced through the Google Translate public web endpoint. Independent linguistic review remains pending.
- A screenshot of the final prompt library is included. Existing report/slides refer to the earlier synthetic-secret experiment and were not rewritten.
