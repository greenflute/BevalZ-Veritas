# Evidence chain audit

## Goal

Add a deterministic evidence-chain audit that aggregates existing LLM, local statistic, reference, image, resource, and cross-file findings into evidence clusters, then checks whether Methods -> Results -> Abstract/Conclusion claims are sufficiently supported and internally consistent.

## Requirements

- Add `meta["evidence_chain_audit"]` with:
  - `clusters`
  - `claim_chain_findings`
  - `status`, `cluster_count`, `finding_count`
  - `strong_count`, `medium_count`, `weak_count`
  - `note`
- Inputs:
  - Extracted full text.
  - Existing per-file text records.
  - `cross_file_consistency_audit.findings`.
  - LLM `report.checks` red flags or suspicious checks.
  - High-priority signals from `stat_result`, `reference_audit`, `image_audit`, and `resource_audit`.
- Chain audit rules:
  - Methods sample-size/group definitions that conflict with Results sample-size/group usage produce strong or medium findings.
  - Abstract/Conclusion strong conclusion wording without nearby Results support produces medium findings.
  - Results figure/table mentions are clustered with relevant image, supplemental, and cross-file concerns.
  - Wording must stay evidence-oriented: “needs review”, “support insufficient”, “cross-paragraph inconsistency”; do not conclude misconduct.
- Report integration:
  - Markdown and HTML reports include a `证据链与证据簇审查` section.
  - JSON report includes complete `meta.evidence_chain_audit`.
  - Action-priority summary ranks strong evidence clusters ahead of isolated findings.
  - HTML follow-up evidence picker defaults to selecting strong evidence clusters.
- Scope:
  - No new third-party services.
  - No LLM prompt/schema changes.
  - No direct risk-rule/scoring changes.
  - Keep implementation primarily in `veritas/legacy.py`.
  - Use extracted directory text when available; single-file input should still run a narrower chain audit.

## Acceptance Criteria

- Synthetic offline tests cover:
  - Methods says `n=42` while Results says same experiment `n=24`, producing a strong chain finding.
  - Abstract has a strong conclusion but Results lack corresponding metric/table/figure support, producing a medium finding.
  - Cross-file sample-size finding plus LLM concern on the same figure aggregate into one evidence cluster.
  - Consistent Methods/Results/Conclusion text produces no finding.
  - Markdown, HTML, JSON/action context, and follow-up context include evidence clusters.
- Regression commands:
  - `python3 -m py_compile paper_audit.py veritas/*.py tests/test_core.py`
  - `python3 paper_audit.py --help`
  - `python3 -m pytest tests/test_core.py -q`

## Assumptions

- MVP optimizes human review ordering and formal draft evidence quality, not automated misconduct judgments.
- Rules are deterministic and intentionally simple; no additional model calls.
- Strong risk comes only from multi-source aggregation or clear Methods/Results numeric conflict.
- Report language remains review-assistant oriented.
