"""Small HTML report fragment builders."""

from .html_utils import _html_escape

__all__ = ["build_html_report_body_from_namespace", "build_html_status_fragments_from_namespace"]


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


def build_html_report_body_from_namespace(namespace, context):
    """Build the top-level HTML report body from precomputed render context."""
    html_escape = _namespace_value(namespace, "_html_escape", _html_escape)
    time_module = _namespace_value(namespace, "time")
    runtime_year = _namespace_value(namespace, "runtime_utc_year")
    prompt_version = _namespace_value(namespace, "PROMPT_VERSION", "")
    schema_version = _namespace_value(namespace, "SCHEMA_VERSION", "")
    adapter_version = _namespace_value(namespace, "ADAPTER_VERSION", "")
    risk_rule_version = _namespace_value(namespace, "RISK_RULE_VERSION", "")
    now = time_module.strftime("%Y-%m-%d %H:%M:%S") if time_module is not None else ""
    current_year = runtime_year() if callable(runtime_year) else ""

    report = context["report"]
    meta = context["meta"]
    stat_result = context["stat_result"]
    runtime = context["runtime"]

    return f"""<body>
<div class="container">
  <div class="header">
    <div class="report-topline">
      <div>
        <div class="report-kicker">Paper Audit / Veritas</div>
        <h1>学术论文审查报告</h1>
        <div class="report-summary">{context["summary_text"]}</div>
      </div>
      <div class="artifact-badge" style="background:{context["artifact_color"]};">{html_escape(context["artifact_badge"])}</div>
    </div>
    <div class="score-panel">
      <div>
        <div class="score-value">{report.get('detection_score', 0)}</div>
        <div class="score-caption">证据风险分 / 100，越高表示越需要优先复核</div>
      </div>
      <div>
        <div class="priority-label">复核优先级：{html_escape(context["risk_icon"])}</div>
        <div class="score-bar"><div class="score-fill" style="width:{min(report.get('detection_score', 0), 100)}%; background:{context["risk_color"]};"></div></div>
      {context["score_breakdown_html"]}
      </div>
    </div>
    <div class="meta-grid">
      <div><span>文件</span><strong>{html_escape(context["pdf_path"])}</strong></div>
      <div><span>产物类型</span><strong>{html_escape(context["artifact_label"])}</strong></div>
      <div><span>Prompt版本</span><strong>{html_escape(meta.get('prompt_version', prompt_version))}</strong></div>
      <div><span>Schema版本</span><strong>{html_escape(meta.get('schema_version', schema_version))}</strong></div>
      <div><span>Adapter版本</span><strong>{html_escape(meta.get('adapter_version', adapter_version))}</strong></div>
      <div><span>规则版本</span><strong>{html_escape(meta.get('risk_rule_version', report.get('rule_version', risk_rule_version)))}</strong></div>
      <div><span>文件大小</span><strong>{meta.get('size_mb', 'N/A')} MB</strong></div>
      <div><span>提取字符数</span><strong>{context["extracted_chars"]}</strong></div>
      <div><span>提取方式</span><strong>{context["extraction_method"]}</strong></div>
      {context["chunk_info"] if context["chunk_info"] else ''}
      <div><span>审查时间</span><strong>{html_escape(runtime.get('local_time') or now)}</strong></div>
      <div><span>运行时UTC年份</span><strong>{html_escape(runtime.get('utc_year', current_year))}</strong></div>
    </div>
  </div>

  {context["review_overview_html"]}
  {context["coverage_banner"]}
  {context["limited_notice"]}
  {context["action_summary_html"]}

  <div class="section" id="local-statistics">
    <h2>本地统计检测结果</h2>
    <table>
      <thead><tr><th>检测项</th><th>结果</th><th>状态</th></tr></thead>
      <tbody>
        <tr><td>Benford分布偏差</td><td>{context["benford_val"]}</td><td>{context["benford_status"]}</td></tr>
        <tr><td>p值数量/异常</td><td>{stat_result['p_value_count']} / {stat_result['p_value_abnormal']}个&gt;0.05</td><td><span class="{context["p_status_class"]}">{'⚠️异常' if context["p_abnormal"] else '✅正常'}</span></td></tr>
        <tr><td>标准差提及</td><td>{stat_result['sd_count']}处</td><td>N/A</td></tr>
        <tr><td>提取数字数</td><td>{stat_result['number_count']}</td><td>-</td></tr>
        {context["number_consistency"]}
      </tbody>
    </table>
  </div>

  {context["checks_html"]}
  {context["web_action_panel_html"]}
  {context["conclusion_html"]}
  {context["evidence_chain_audit_html"]}
  {context["image_audit_html"]}
  {context["cross_file_audit_html"]}
  {context["resource_audit_html"]}
  {context["reference_audit_html"]}

  <div class="footer">
    Generated by <strong>Veritas</strong> — 学术论文自动审查工具（耿同学标准） | {now}
  </div>
</div>
</body>
</html>"""
