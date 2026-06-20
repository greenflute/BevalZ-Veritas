"""Strict evidence schema normalization for text LLM audit reports."""

import json
import re
from typing import Any, Dict, List


LLM_REQUIRED_FINDING_FIELDS = ("verdict", "source", "evidence", "reason", "recommendation", "confidence")


def _brief_text(text, limit=180):
    """Compress long text while preserving report readability."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _missing_finding_fields(check: Dict[str, Any]) -> List[str]:
    missing = []
    for field_name in LLM_REQUIRED_FINDING_FIELDS:
        if field_name == "source":
            if not (check.get("source") or check.get("source_text") or check.get("quote")):
                missing.append("source")
        elif field_name not in check or check.get(field_name) in {None, ""}:
            missing.append(field_name)
    return missing


def normalize_llm_report_schema(report: Dict[str, Any], raw_output: str = "") -> Dict[str, Any]:
    """Validate and normalize the strict LLM evidence schema."""
    if not isinstance(report, dict):
        return {"parse_error": True, "schema_error": True, "schema_errors": ["report_not_object"], "raw_output": raw_output}
    checks = report.get("checks")
    if checks is None:
        checks = []
    if not isinstance(checks, list):
        return {"parse_error": True, "schema_error": True, "schema_errors": ["checks_not_list"], "raw_output": raw_output}

    errors = []
    normalized_checks = []
    recovered_schema = False
    for idx, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append(f"checks[{idx}]: not_object")
            continue
        missing = _missing_finding_fields(check)
        if missing:
            recovered_schema = True
        normalized = dict(check)
        normalized.setdefault("category", "未分类")
        normalized.setdefault("item", "未命名检查项")
        normalized.setdefault("verdict", "⚠️疑点")
        normalized["source_text"] = normalized.get("source_text") or normalized.get("source") or normalized.get("quote") or "未找到直接原文证据"
        normalized["source"] = normalized.get("source") or normalized["source_text"]
        normalized.setdefault("evidence", normalized["source_text"])
        normalized.setdefault("reason", "LLM未完整返回该字段，已按需人工复核处理。")
        normalized.setdefault("recommendation", "人工复核该检查项对应原文和模型输出。")
        try:
            normalized["confidence"] = float(normalized.get("confidence"))
        except (TypeError, ValueError):
            normalized["confidence"] = 0.2
            recovered_schema = True
        if missing:
            normalized["_schema_recovered_missing_fields"] = missing
        normalized_checks.append(normalized)

    if errors:
        return {"parse_error": True, "schema_error": True, "schema_errors": errors, "raw_output": raw_output}

    normalized_report = dict(report)
    normalized_report["checks"] = normalized_checks
    normalized_report.setdefault("summary", "N/A")
    normalized_report.setdefault("risk_level", "未知")
    normalized_report.setdefault("detection_score", 0)
    normalized_report.setdefault("conclusion", "")
    if recovered_schema:
        normalized_report["_schema_recovered"] = True
        normalized_report.setdefault("schema_errors", []).append("missing_or_invalid_check_fields")
    if raw_output:
        normalized_report["_raw_response_preserved"] = True
    return normalized_report


def parse_report(content):
    """Parse LLM JSON report responses with recovery for common truncation cases."""
    content = str(content or "").strip()
    try:
        return normalize_llm_report_schema(json.loads(content), raw_output=content)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content, re.IGNORECASE)
    if m:
        fenced = m.group(1).strip()
        try:
            return normalize_llm_report_schema(json.loads(fenced), raw_output=fenced)
        except json.JSONDecodeError:
            content = fenced
    m = re.search(r'\{[\s\S]*\}', content)
    if m:
        try:
            raw_object = m.group()
            return normalize_llm_report_schema(json.loads(raw_object), raw_output=raw_object)
        except json.JSONDecodeError:
            pass

    # Preserve partial findings as manual-review evidence instead of silently
    # dropping a malformed but informative chunk.
    summary = re.search(r'"summary"\s*:\s*"((?:\\.|[^"\\])*)"', content)
    risk = re.search(r'"risk_level"\s*:\s*"((?:\\.|[^"\\])*)"', content)
    score = re.search(r'"detection_score"\s*:\s*([0-9]+(?:\.[0-9]+)?)', content)
    verdict = re.search(r'"verdict"\s*:\s*"((?:\\.|[^"\\])*)"', content)
    category = re.search(r'"category"\s*:\s*"((?:\\.|[^"\\])*)"', content)
    item = re.search(r'"item"\s*:\s*"((?:\\.|[^"\\])*)"', content)
    if summary or risk or verdict:
        recovered_summary = _json_string_unescape(summary.group(1)) if summary else "LLM返回JSON不完整，已转为需人工复核项。"
        recovered_risk = _json_string_unescape(risk.group(1)) if risk else "中"
        try:
            recovered_score = float(score.group(1)) if score else 50
        except Exception:
            recovered_score = 50
        recovered_verdict = _json_string_unescape(verdict.group(1)) if verdict else "⚠️疑点"
        recovered_category = _json_string_unescape(category.group(1)) if category else "结构与引用"
        recovered_item = _json_string_unescape(item.group(1)) if item else "LLM输出结构异常"
        return {
            "summary": recovered_summary,
            "risk_level": recovered_risk,
            "detection_score": recovered_score,
            "checks": [{
                "category": recovered_category,
                "item": recovered_item,
                "verdict": recovered_verdict,
                "source": "LLM分块输出",
                "source_text": "该分块模型返回了截断或非严格JSON，需人工复核原文和模型原始输出。",
                "evidence": _brief_text(content, 240),
                "reason": "模型返回内容包含审查结论但不满足严格JSON schema；为避免丢弃该分块，保留为需人工复核项。",
                "recommendation": "人工复核该分块原文；必要时更换更稳定的文本LLM后重跑。",
                "confidence": 0.2,
                "detail": "由截断/非严格JSON自动恢复，不能作为单独定论。",
            }],
            "conclusion": "该分块存在LLM输出结构异常，已降级为人工复核项纳入合并报告。",
            "_schema_recovered": True,
            "schema_errors": ["truncated_json"],
            "partial_fields": {
                "summary": recovered_summary,
                "risk_level": recovered_risk,
                "detection_score": recovered_score,
                "category": recovered_category,
                "item": recovered_item,
                "verdict": recovered_verdict,
            },
            "raw_output": content,
        }
    return {"raw_output": content, "parse_error": True}


def _json_string_unescape(value):
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value


__all__ = [
    "LLM_REQUIRED_FINDING_FIELDS",
    "normalize_llm_report_schema",
    "parse_report",
]
