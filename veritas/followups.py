"""Follow-up draft context and prompt helpers."""

import datetime
import json
import re

from .text_utils import _brief_text


def normalize_followup_language(language):
    value = str(language or "zh").strip().lower()
    if value in {"en", "english"}:
        return "en"
    if value in {"zh", "cn", "chinese", "中文"}:
        return "zh"
    return "zh"


def normalize_followup_tone(tone):
    value = str(tone or "conservative").strip().lower()
    if value in {"standard", "标准"}:
        return "standard"
    if value in {"firm", "strong", "强硬"}:
        return "firm"
    return "conservative"


def _followup_language_instruction(language):
    language = normalize_followup_language(language)
    if language == "en":
        return (
            "Write the entire draft in English. "
            "Use the phrase 'Based on my reading and understanding of this article' or a close equivalent."
        )
    return (
        "请使用简体中文撰写全文。"
        "请明确写出“基于对这篇文章的阅读和理解，我注意到以下问题”或语义等价表述。"
    )


def _followup_tone_instruction(tone):
    tone = normalize_followup_tone(tone)
    if tone == "firm":
        return (
            "Use a firm but still evidence-limited tone. Be direct about concerns, "
            "but do not state fraud, misconduct, or intent as fact."
        )
    if tone == "standard":
        return (
            "Use a clear standard academic tone. List concerns and requested clarifications, "
            "while avoiding conclusions beyond the evidence."
        )
    return (
        "Use a conservative tone. Phrase concerns as questions or requests for clarification "
        "and avoid accusatory wording."
    )


def _split_author_text(value):
    if isinstance(value, list):
        return [str(author).strip() for author in value if str(author or "").strip()]
    text = str(value or "")
    return [part.strip() for part in re.split(r";|,|\band\b|，|；", text) if part.strip()]


def normalize_article_identity(identity=None, fallback=None):
    identity = identity if isinstance(identity, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}

    def value(key, limit):
        raw = identity.get(key)
        if raw is None or str(raw).strip() == "":
            raw = fallback.get(key, "")
        return _brief_text(str(raw or "").strip(), limit)

    authors = identity.get("authors")
    if authors is None or authors == "":
        authors = fallback.get("authors", [])
    return {
        "title": value("title", 300),
        "journal": value("journal", 220),
        "authors": [_brief_text(author, 120) for author in _split_author_text(authors)][:12],
        "doi": value("doi", 120),
        "year": value("year", 20),
    }


def _normalize_followup_issues(issues):
    normalized = []
    source_items = issues if isinstance(issues, list) else []
    for idx, issue in enumerate(source_items[:20], 1):
        if not isinstance(issue, dict):
            continue
        normalized.append({
            "id": str(issue.get("id") or f"issue-{idx}"),
            "source": str(issue.get("source") or "audit"),
            "category": _brief_text(issue.get("category", ""), 120),
            "item": _brief_text(issue.get("item", ""), 180),
            "verdict": _brief_text(issue.get("verdict", ""), 80),
            "evidence": _brief_text(issue.get("evidence", ""), 900),
            "reason": _brief_text(issue.get("reason", ""), 900),
        })
    return normalized


def _normalize_custom_concerns(concerns):
    if isinstance(concerns, str):
        concerns = [line.strip() for line in concerns.splitlines() if line.strip()]
    normalized = []
    for idx, concern in enumerate((concerns or [])[:10], 1):
        if isinstance(concern, dict):
            text = str(concern.get("text") or concern.get("reason") or "").strip()
        else:
            text = str(concern or "").strip()
        if not text:
            continue
        normalized.append({
            "id": f"user-{idx}",
            "source": "user_added",
            "category": "自定义关注点",
            "severity": "manual",
            "text": _brief_text(text, 900),
        })
    return normalized


def build_followup_generation_context(
    context,
    identity=None,
    selected_issues=None,
    custom_concerns=None,
    tone="conservative",
):
    context = context if isinstance(context, dict) else {}
    artifact_type = context.get("artifact_type") or context.get("report_type") or "complete"
    if artifact_type == "failed":
        raise ValueError("failed_report_followup_blocked")
    fallback_identity = context.get("paper_identity") or {}
    issues = selected_issues if selected_issues is not None else context.get("top_issues")
    prepared = dict(context)
    prepared["artifact_type"] = artifact_type
    prepared["limited_reasons"] = context.get("limited_reasons") or []
    prepared["paper_identity"] = normalize_article_identity(identity, fallback=fallback_identity)
    prepared["selected_issues"] = _normalize_followup_issues(issues)
    prepared["custom_concerns"] = _normalize_custom_concerns(custom_concerns)
    prepared["tone"] = normalize_followup_tone(tone)
    prepared["confirmed_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    return prepared


def build_followup_prompt(kind, context, language="zh", tone=None):
    context = context if isinstance(context, dict) else {}
    language = normalize_followup_language(language)
    tone = normalize_followup_tone(tone or context.get("tone"))
    kind_labels = {
        "pubpeer_comment": "PubPeer comment",
        "journal_letter": "letter to the journal editor",
    }
    if kind not in kind_labels:
        raise ValueError(f"unsupported action kind: {kind}")
    context_text = json.dumps(context, ensure_ascii=False, indent=2)
    identity_instruction = (
        "Use the article identity fields in the Audit context JSON when available: paper_identity.title, "
        "paper_identity.journal, and paper_identity.authors. Match the article title, journal name, and author "
        "information accurately; do not invent missing title, journal, DOI, or author details. "
        "If an identity field is missing, say it is not available in the audit context instead of guessing. "
        + _followup_language_instruction(language)
    )
    scope_instruction = ""
    if context.get("artifact_type") == "limited":
        scope_instruction = (
            "The audit context is marked limited. Include a brief scope limitation statement and avoid implying a complete review. "
        )
    evidence_instruction = (
        "Use selected_issues as the primary evidence list. Treat custom_concerns entries with source=user_added as user-added concerns, "
        "not automated findings. "
    )
    if kind == "pubpeer_comment":
        task = (
            "Draft a concise PubPeer comment based strictly on the audit context. "
            f"{identity_instruction} {_followup_tone_instruction(tone)} {scope_instruction}{evidence_instruction}"
            "Be neutral, evidence-based, and non-defamatory. "
            "Do not claim fraud or misconduct as fact. Ask clear questions and cite only the evidence in context. "
            "Include a short title, an article identification sentence, and 3-6 numbered concerns if warranted."
        )
    else:
        task = (
            "Draft a formal letter to the journal editor based strictly on the audit context. "
            f"{identity_instruction} {_followup_tone_instruction(tone)} {scope_instruction}{evidence_instruction}"
            "Keep a professional, cautious tone. "
            "Do not assert fraud or misconduct as fact. Request editorial assessment and list reproducible concerns. "
            "Include subject, salutation, concise background, article identification, bullet concerns, requested actions, and closing."
        )
    return [
        {
            "role": "system",
            "content": (
                "You are an academic integrity writing assistant. You produce careful drafts grounded only in provided evidence. "
                "You avoid exaggeration, legal conclusions, personal accusations, and unsupported claims."
            ),
        },
        {
            "role": "user",
            "content": f"{task}\n\nAudit context JSON:\n{context_text}",
        },
    ]


__all__ = [
    "normalize_followup_language",
    "normalize_followup_tone",
    "_followup_language_instruction",
    "_followup_tone_instruction",
    "_split_author_text",
    "normalize_article_identity",
    "_normalize_followup_issues",
    "_normalize_custom_concerns",
    "build_followup_generation_context",
    "build_followup_prompt",
]
