"""Small HTML report fragment builders."""

from .html_utils import _html_escape

__all__ = ["build_html_status_fragments_from_namespace"]


def _namespace_value(namespace, name, default=None):
    return (namespace or {}).get(name, default)


def build_html_status_fragments_from_namespace(namespace, report, meta, stat_result):
    """Build status fragments used by the top-level HTML report."""
    html_escape = _namespace_value(namespace, "_html_escape", _html_escape)

    limited_notice = ""
    if meta.get("limited_reasons"):
        limited_notice = f"""
  <div class="section coverage-warning">
    <h2>范围受限审查</h2>
    <p>{html_escape('；'.join(meta.get('limited_reasons') or []))}</p>
  </div>"""

    chunk_info = ""
    if meta.get("chunk_count") and meta["chunk_count"] > 1:
        chunk_info = f"""
        <div class="meta-item">
            <span>审查方式</span>
            <strong>分块审查 · {meta['chunk_count']}块 · 单块{meta['chunk_size']}字符 · 重叠{meta['overlap']}字符</strong>
        </div>"""

    number_consistency = ""
    if stat_result.get("number_consistency"):
        number_consistency = f"""
        <tr>
            <td>数字自洽性</td>
            <td>{stat_result['number_consistency']}</td>
            <td><span class="status-warn">⚠️ 矛盾</span></td>
        </tr>"""

    coverage_banner = ""
    if meta.get("llm_coverage"):
        failed_chunks = meta.get("llm_failed_chunks") or []
        if meta.get("llm_partial_report") or failed_chunks:
            coverage_banner = f"""
  <div class="section coverage-warning">
    <h2>LLM覆盖不足</h2>
    <p><strong>成功审查分块</strong>: {html_escape(meta.get('llm_coverage'))}</p>
    <p><strong>失败块</strong>: {html_escape(failed_chunks or '无')}</p>
    <p>本报告只基于成功返回的LLM分块合并，未覆盖失败分块全文；结论只能作为阶段性结果。建议稍后使用 <code>--llm-cache-only</code> 复用成功缓存，或切换更稳定API补跑。</p>
  </div>"""
        else:
            coverage_banner = f"""
  <div class="section coverage-ok">
    <h2>LLM覆盖率</h2>
    <p>{html_escape(meta.get('llm_coverage'))} 个分块全部成功。</p>
  </div>"""

    breakdown = report.get("score_breakdown") or {}
    score_breakdown_html = ""
    if breakdown:
        score_breakdown_html = f"""
      <div class="score-breakdown">
        红旗 {breakdown.get('red_flags', 0)} · 证据型疑点 {breakdown.get('evidence_warnings', 0)} · 提取质量疑点 {breakdown.get('extraction_warnings', 0)} · 统计调整 {html_escape(', '.join(breakdown.get('stat_adjustments') or []) or '无')}
      </div>"""

    return {
        "limited_notice": limited_notice,
        "chunk_info": chunk_info,
        "number_consistency": number_consistency,
        "coverage_banner": coverage_banner,
        "score_breakdown_html": score_breakdown_html,
    }
