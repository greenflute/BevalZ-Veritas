"""Reference audit Markdown and HTML rendering helpers."""

from .evidence_rendering import _escaped_html_table_fragment_to_html, render_evidence_summary_html
from .html_utils import _html_escape
from .markdown_utils import _md_escape_cell
from .reference_parsing import _looks_like_reference_table_noise, build_reference_query
from .text_utils import _brief_text

__all__ = [
    "REFERENCE_ISSUE_LABELS",
    "_reference_online_summary",
    "_reference_issue_text",
    "_reference_display_title",
    "_reference_text_html",
    "_reference_query_text",
    "format_reference_audit_markdown",
    "format_reference_audit_html",
]


def _reference_online_summary(online):
    if not online:
        return "未联网检索"
    status = online.get("online_status", "N/A")
    confidence = online.get("confidence", 0)
    sources = []
    for match in online.get("matched_sources") or []:
        label = match.get("source", "")
        if label and label not in sources:
            sources.append(label)
    source_text = "/".join(sources) if sources else "无命中"
    return f"{status} / {confidence} / {source_text}"


REFERENCE_ISSUE_LABELS = {
    "missing_year": "缺少年份",
    "future_year": "年份晚于运行时当前年份",
    "missing_doi": "缺少DOI",
    "missing_journal_or_source": "缺少期刊/来源",
    "too_short": "引用过短",
    "online_not_found": "在线未检索到",
    "online_weak": "在线弱匹配",
    "online_error": "在线检索异常",
    "doi_not_found": "DOI未命中",
    "no_online_match": "无在线命中",
    "all_sources_error": "外部源均异常",
    "partial_source_error": "部分外部源异常",
    "doi_mismatch": "DOI不一致",
    "title_low_similarity": "题名相似度低",
    "year_mismatch": "年份不一致",
    "year_near_mismatch": "年份接近但不一致",
    "source_marks_retracted": "来源标记撤稿",
}


def _reference_issue_text(issues):
    labels = [REFERENCE_ISSUE_LABELS.get(str(issue), str(issue)) for issue in (issues or [])]
    return ", ".join(dict.fromkeys(labels))


def _reference_display_title(ref):
    raw = ref.get("title_hint") or ref.get("text", "")
    if _looks_like_reference_table_noise(raw):
        return "疑似表格片段，未作为有效参考文献"
    return _brief_text(raw, 140)


def _reference_text_html(text):
    if _looks_like_reference_table_noise(text):
        table_html = _escaped_html_table_fragment_to_html(text) or render_evidence_summary_html(text)
        return (
            '<div class="reference-table-note">该条内容看起来是表格提取噪声，不应作为参考文献核验对象。</div>'
            f"{table_html}"
        )
    return _html_escape(text)


def _reference_query_text(ref, query):
    raw = ref.get("text", "")
    if _looks_like_reference_table_noise(raw):
        return "疑似表格提取噪声，未生成参考文献检索式"
    return query.get("doi") or query.get("bibliographic") or ""


def format_reference_audit_markdown(reference_audit):
    if reference_audit is None:
        return []
    lines = [
        '<a id="reference-audit"></a>',
        "## 📚 参考文献真实性/可核验性校检",
        "",
        f"**状态**: {reference_audit.get('status', 'N/A')}",
        f"**参考文献数量**: {reference_audit.get('reference_count', 0)}",
        f"**含 DOI 数量**: {reference_audit.get('doi_count', 0)}",
        f"**含年份数量**: {reference_audit.get('year_count', 0)}",
        f"**在线检索**: {'启用' if reference_audit.get('online_enabled') else '未启用'}"
        + (f"（已检索 {reference_audit.get('online_checked', 0)} 条）" if reference_audit.get("online_enabled") else ""),
        f"> {reference_audit.get('note', '')}",
        "",
    ]
    issues = reference_audit.get("issues", [])
    if issues:
        lines.append("| # | 问题 | 在线证据 | 引用摘录 |")
        lines.append("|---|------|----------|----------|")
        refs_by_index = {i + 1: ref for i, ref in enumerate(reference_audit.get("references", []))}
        for item in issues[:30]:
            ref = refs_by_index.get(item.get("index"), {})
            lines.append(
                f"| {item.get('index')} | {_md_escape_cell(_reference_issue_text(item.get('issues', [])))} | "
                f"{_md_escape_cell(_reference_online_summary(ref.get('online')))} | "
                f"{_md_escape_cell(_brief_text(item.get('text', ''), 220))} |"
            )
    else:
        lines.append("> 未发现明显格式缺失；仍建议对关键引用进行数据库/DOI人工核验。")
    lines.append("")
    return lines


def format_reference_audit_html(reference_audit):
    if reference_audit is None:
        return ""
    status_labels = {
        "verified": "已验证",
        "likely": "较可能真实",
        "weak": "弱匹配",
        "not_found": "未检索到",
        "error": "检索异常",
        "skipped": "未检索",
    }
    issue_map = {item.get("index"): item for item in reference_audit.get("issues", [])}
    cards = ""
    for idx, ref in enumerate(reference_audit.get("references", [])[:60], 1):
        online = ref.get("online") or {}
        status = online.get("online_status", "offline")
        status_text = status_labels.get(status, status if status != "offline" else "离线检查")
        confidence = online.get("confidence", 0)
        issue = issue_map.get(idx, {})
        issue_text = _reference_issue_text(issue.get("issues", [])) if issue else "未发现明显问题"
        matches = ""
        for match in (online.get("matched_sources") or [])[:3]:
            title = _html_escape(_brief_text(match.get("title", ""), 150))
            meta = _html_escape(" | ".join(str(x) for x in (match.get("source"), match.get("year"), match.get("doi")) if x))
            url = _html_escape(match.get("url", ""))
            link = f' <a href="{url}" target="_blank" rel="noopener">来源</a>' if url else ""
            matches += f"<li><strong>{title or '无题名'}</strong><br><span>{meta}</span>{link}</li>"
        if not matches:
            matches = "<li>无在线命中记录</li>"
        query = online.get("query") or build_reference_query(ref)
        cards += f"""
        <details class="reference-card" id="reference-{idx}">
          <summary class="reference-summary">
            <span class="reference-index">#{idx}</span>
            <span class="reference-status reference-{_html_escape(status)}">{_html_escape(status_text)}</span>
            <span class="reference-title">{_html_escape(_reference_display_title(ref))}</span>
            <span class="reference-confidence">置信度 {confidence}</span>
            <span class="reference-issues">{_html_escape(_brief_text(issue_text, 140))}</span>
          </summary>
          <div class="reference-body">
            <div><strong>引用原文</strong>: {_reference_text_html(ref.get('text', ''))}</div>
            <p><strong>检索式</strong>: {_html_escape(_reference_query_text(ref, query))}</p>
            <p><strong>问题</strong>: {_html_escape(issue_text)}</p>
            <ul class="reference-matches">{matches}</ul>
          </div>
        </details>"""

    if not cards:
        cards = '<div class="muted">未发现可解析参考文献。</div>'
    return f"""
  <div class="section reference-section" id="reference-audit">
    <h2>参考文献真实性/可核验性校检</h2>
    <p><strong>状态</strong>: {_html_escape(reference_audit.get('status', 'N/A'))} | <strong>数量</strong>: {reference_audit.get('reference_count', 0)} | <strong>DOI</strong>: {reference_audit.get('doi_count', 0)} | <strong>年份</strong>: {reference_audit.get('year_count', 0)} | <strong>在线检索</strong>: {'启用' if reference_audit.get('online_enabled') else '未启用'}（{reference_audit.get('online_checked', 0)}条）</p>
    <p class="section-hint">{_html_escape(reference_audit.get('note', ''))}</p>
    <div class="reference-list">{cards}</div>
  </div>"""
