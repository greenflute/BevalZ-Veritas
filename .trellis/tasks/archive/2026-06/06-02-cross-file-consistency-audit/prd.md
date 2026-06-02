# Cross-file Consistency Audit

## Goal

Add a first-pass scientific integrity risk check that compares extracted content
across the main paper, supplements, and data files. The feature should surface
evidence-oriented inconsistencies such as mismatched sample sizes, group labels,
and table/figure references without claiming misconduct.

## What I already know

- Existing directory extraction classifies main paper, supplements, data files,
  references, and other files through `find_project_files()`.
- Existing reports already write Markdown, HTML, and JSON artifacts.
- Default tests must not call Crossref, OpenAlex, PubMed, MinerU, text LLMs,
  image semantic LLMs, or imagedetector.
- The first version should use deterministic extracted-text comparison, not
  third-party services.

## Requirements

- Add `meta["cross_file_consistency_audit"]` to completed and limited audit
  JSON output.
- Add a `跨文件一致性审查` section to Markdown and HTML reports.
- Enable the audit for directory inputs using per-file extracted text from main
  paper, supplements, data files, and other non-reference files.
- Skip gracefully for single-file inputs or directory inputs without enough
  cross-file material.
- Detect at least:
  - same-context sample size mismatches as strong findings;
  - group label mismatches as medium findings;
  - figure/table reference coverage gaps as weak or medium findings.
- Every finding must include claim text, counter-evidence text, source category,
  source file, excerpts, severity, reason, and manual check guidance.
- Keep output wording evidence-based and avoid misconduct conclusions.

## Acceptance Criteria

- [x] Main text says `n=42` and supplement says `n=24` for the same nearby
      context, producing a `sample_size_mismatch` strong finding.
- [x] Main text says `Control group` while supplement/data context only exposes
      `Vehicle group`, producing a medium group-label finding.
- [x] Matching main/supplement sample sizes produce no false positive.
- [x] Noisy OCR/table-like text produces at most weak findings, not strong
      findings.
- [x] Markdown, HTML, JSON, and follow-up action context expose the new audit.
- [x] Existing default tests remain offline and deterministic.

## Out of Scope

- Image pixel duplication detection.
- Author, journal, or paper network profiling.
- New external APIs, local LLM services, or local OCR services.
- Automatic misconduct conclusions.

## Technical Notes

- Likely implementation file: `veritas/legacy.py`.
- Likely tests: `tests/test_core.py`.
- Required verification after backend edits:
  - `python3 -m py_compile paper_audit.py veritas/*.py tests/test_core.py`
  - `python3 paper_audit.py --help`
  - `python3 -m pytest tests/test_core.py -q`
