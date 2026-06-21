"""HTML report action panel rendering helpers."""

from .html_utils import _html_escape, _json_for_script_tag
from .report_action_context import _report_action_context

__all__ = ["report_action_service_url", "format_web_action_panel_html"]


def report_action_service_url(host="127.0.0.1", port=8765):
    return f"http://{host}:{int(port)}"


def format_web_action_panel_html(report, pdf_path, meta, stat_result):
    meta = meta or {}
    service = meta.get("report_actions") or {}
    host = service.get("host") or "127.0.0.1"
    port = int(service.get("port") or 8765)
    service_url = report_action_service_url(host, port)
    generate_url = f"{service_url}/generate"
    followups_url = f"{service_url}/followups"
    context = _report_action_context(report, pdf_path, meta, stat_result or {})
    context_json = _json_for_script_tag(context)
    generate_url_json = _json_for_script_tag(generate_url)
    followups_url_json = _json_for_script_tag(followups_url)
    service_url_json = _json_for_script_tag(service_url)
    startup_command_json = _json_for_script_tag(f"python paper_audit.py --serve-report-actions --report-actions-port {port}")
    return f"""
  <div class="section web-action-section">
    <h2>一键生成后续沟通草稿</h2>
    <p class="section-hint">草稿由本地配置的LLM生成。生成前请确认文章身份、证据范围和语气；生成后仍需人工核对。</p>
    <div class="identity-grid" aria-label="文章身份确认">
      <label>标题<input id="followup-title" type="text" placeholder="文章标题"></label>
      <label>期刊<input id="followup-journal" type="text" placeholder="期刊"></label>
      <label>作者<input id="followup-authors" type="text" placeholder="作者，逗号分隔"></label>
      <label>DOI<input id="followup-doi" type="text" placeholder="DOI"></label>
      <label>年份<input id="followup-year" type="text" placeholder="年份"></label>
    </div>
    <div class="web-action-toolbar">
      <label class="inline-control">语言
        <select id="draft-language" class="draft-language-select" aria-label="草稿语言">
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </label>
      <label class="inline-control">语气
        <select id="draft-tone" class="draft-language-select" aria-label="草稿语气">
          <option value="conservative">保守</option>
          <option value="standard">标准</option>
          <option value="firm">强硬</option>
        </select>
      </label>
      <button type="button" class="action-button" data-action-kind="pubpeer_comment">生成 PubPeer Comment</button>
      <button type="button" class="action-button" data-action-kind="journal_letter">生成期刊 Letter</button>
      <button type="button" class="secondary-button" id="copy-generated-draft">复制草稿</button>
    </div>
    <div class="evidence-picker">
      <strong>写入草稿的证据</strong>
      <div id="followup-evidence-list" class="evidence-choice-list"></div>
    </div>
    <label class="custom-concern-label">自定义关注点
      <textarea id="custom-followup-concerns" class="custom-concern-input" placeholder="每行一个人工补充关注点，会标记为 user_added。"></textarea>
    </label>
    <label class="manual-confirmation">
      <input id="manual-review-confirmation" type="checkbox">
      我已确认文章身份、证据选择和语气设置；生成内容仅作为基于阅读和理解文章后的学术问题表达草稿，发送前仍需人工复核。
    </label>
    <div id="existing-followups" class="existing-followups"></div>
    <div id="web-action-status" class="web-action-status">动作服务: <code>{_html_escape(service_url)}</code></div>
    <textarea id="generated-draft" class="generated-draft" spellcheck="false" placeholder="生成的草稿会显示在这里，可直接编辑。"></textarea>
  </div>
  <script id="paper-audit-action-context" type="application/json">{context_json}</script>
  <script>
  (function() {{
    const statusEl = document.getElementById('web-action-status');
    const outputEl = document.getElementById('generated-draft');
    const contextEl = document.getElementById('paper-audit-action-context');
    const languageEl = document.getElementById('draft-language');
    const toneEl = document.getElementById('draft-tone');
    const evidenceEl = document.getElementById('followup-evidence-list');
    const existingEl = document.getElementById('existing-followups');
    const confirmationEl = document.getElementById('manual-review-confirmation');
    const actionLabels = {{
      pubpeer_comment: 'PubPeer comment',
      journal_letter: 'journal letter'
    }};
    const languageLabels = {{ zh: '中文', en: 'English' }};
    const generateUrl = {generate_url_json};
    const followupsUrl = {followups_url_json};
    const serviceUrl = {service_url_json};
    const startupCommand = {startup_command_json};
    let reportContext = {{}};
    function esc(value) {{
      return String(value == null ? '' : value).replace(/[&<>"']/g, function(ch) {{
        return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[ch];
      }});
    }}
    function setStatus(text, isError) {{
      statusEl.textContent = text;
      statusEl.className = 'web-action-status' + (isError ? ' error' : '');
    }}
    function setStatusHtml(html, isError) {{
      statusEl.innerHTML = html;
      statusEl.className = 'web-action-status' + (isError ? ' error' : '');
    }}
    function serviceFailure(prefix, err) {{
      setStatusHtml(
        esc(prefix) + '：本机动作服务未响应。服务地址: <code>' + esc(serviceUrl) + '</code>。请运行: <code>' +
        esc(startupCommand) + '</code>，然后刷新本页面或重新点击生成。详情: ' + esc(err && err.message ? err.message : err),
        true
      );
    }}
    function readContext() {{
      try {{
        reportContext = JSON.parse(contextEl.textContent || '{{}}');
        return reportContext;
      }} catch (err) {{
        setStatus('无法读取报告上下文: ' + err.message, true);
        return {{}};
      }}
    }}
    function populateIdentity(identity) {{
      identity = identity || {{}};
      document.getElementById('followup-title').value = identity.title || '';
      document.getElementById('followup-journal').value = identity.journal || '';
      document.getElementById('followup-authors').value = Array.isArray(identity.authors) ? identity.authors.join(', ') : (identity.authors || '');
      document.getElementById('followup-doi').value = identity.doi || '';
      document.getElementById('followup-year').value = identity.year || '';
    }}
    function identityFromForm() {{
      return {{
        title: document.getElementById('followup-title').value.trim(),
        journal: document.getElementById('followup-journal').value.trim(),
        authors: document.getElementById('followup-authors').value.split(/[,;，；]/).map(function(x) {{ return x.trim(); }}).filter(Boolean),
        doi: document.getElementById('followup-doi').value.trim(),
        year: document.getElementById('followup-year').value.trim()
      }};
    }}
    function renderEvidence(context) {{
      const issues = Array.isArray(context.top_issues) ? context.top_issues : [];
      if (!issues.length) {{
        evidenceEl.innerHTML = '<p class="section-hint">没有可自动勾选的高优先级证据；可在自定义关注点中补充。</p>';
        return;
      }}
      evidenceEl.innerHTML = issues.map(function(issue, idx) {{
        const verdict = String(issue.verdict || '');
        const checked = (issue.default_selected || verdict.indexOf('红旗') >= 0 || verdict.indexOf('高') >= 0 || verdict.indexOf('强证据') >= 0 || idx < 3) ? ' checked' : '';
        const label = [issue.category, issue.item, issue.verdict].filter(Boolean).join(' · ');
        const detail = issue.reason || issue.evidence || '';
        return '<label class="evidence-choice"><input type="checkbox" data-issue-index="' + idx + '"' + checked + '> <span><strong>' +
          esc(label || ('证据 ' + (idx + 1))) + '</strong><small>' + esc(detail).slice(0, 220) + '</small></span></label>';
      }}).join('');
    }}
    function selectedIssues() {{
      const issues = Array.isArray(reportContext.top_issues) ? reportContext.top_issues : [];
      return Array.from(evidenceEl.querySelectorAll('input[type="checkbox"]:checked')).map(function(input) {{
        return issues[Number(input.getAttribute('data-issue-index'))];
      }}).filter(Boolean);
    }}
    function customConcerns() {{
      return document.getElementById('custom-followup-concerns').value.split(/\\n+/).map(function(x) {{ return x.trim(); }}).filter(Boolean);
    }}
    function renderExisting(data) {{
      const drafts = (data && data.drafts) || {{}};
      const kinds = Object.keys(drafts);
      if (!kinds.length) {{
        existingEl.textContent = '当前语言暂无已生成草稿。';
        return;
      }}
      existingEl.innerHTML = '已生成: ' + kinds.map(function(kind) {{
        return '<button type="button" class="secondary-button existing-draft-button" data-existing-kind="' + esc(kind) + '">' + esc(actionLabels[kind] || kind) + '</button>';
      }}).join(' ');
      existingEl.querySelectorAll('[data-existing-kind]').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
          const kind = btn.getAttribute('data-existing-kind');
          outputEl.value = drafts[kind] && drafts[kind].text ? drafts[kind].text : '';
          setStatus('已载入已生成的 ' + (actionLabels[kind] || kind) + '。', false);
        }});
      }});
    }}
    async function loadExisting() {{
      const context = readContext();
      if (context.artifact_type === 'failed') {{
        setStatus('失败诊断报告不允许生成 PubPeer Comment 或期刊 Letter；请先修复关键服务后重新生成审查报告。', true);
        document.querySelectorAll('[data-action-kind]').forEach(function(btn) {{ btn.disabled = true; }});
        return;
      }}
      try {{
        const resp = await fetch(followupsUrl, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ context: context, language: (languageEl && languageEl.value) || 'zh' }})
        }});
        const data = await resp.json();
        if (!resp.ok || !data.ok) {{ throw new Error(data.error || ('HTTP ' + resp.status)); }}
        if (data.identity && (data.identity.title || data.identity.journal || data.identity.authors)) {{
          populateIdentity(data.identity);
        }}
        renderExisting(data);
      }} catch (err) {{
        serviceFailure('读取已生成草稿失败', err);
      }}
    }}
    async function generate(kind) {{
      const context = readContext();
      if (context.artifact_type === 'failed') {{
        setStatus('失败诊断报告不允许生成 PubPeer Comment 或期刊 Letter。', true);
        return;
      }}
      if (!confirmationEl.checked) {{
        setStatus('请先勾选人工复核确认，再生成外部沟通草稿。', true);
        return;
      }}
      const language = (languageEl && languageEl.value) || 'zh';
      setStatus('正在生成 ' + languageLabels[language] + ' ' + actionLabels[kind] + ' ...', false);
      outputEl.value = '';
      try {{
        const resp = await fetch(generateUrl, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            kind,
            context,
            language,
            tone: (toneEl && toneEl.value) || 'conservative',
            identity: identityFromForm(),
            selected_issues: selectedIssues(),
            custom_concerns: customConcerns(),
            disclaimer_confirmed: true
          }})
        }});
        const data = await resp.json();
        if (!resp.ok || !data.ok) {{
          throw new Error(data.error || ('HTTP ' + resp.status));
        }}
        outputEl.value = data.text || '';
        const path = data.paths && data.paths.draft_path ? ' 已保存: ' + data.paths.draft_path : '';
        setStatus('已生成 ' + actionLabels[kind] + '。请人工核对后再使用。' + path, false);
        loadExisting();
      }} catch (err) {{
        serviceFailure('生成失败', err);
      }}
    }}
    document.querySelectorAll('[data-action-kind]').forEach((btn) => {{
      btn.addEventListener('click', () => generate(btn.getAttribute('data-action-kind')));
    }});
    document.getElementById('copy-generated-draft').addEventListener('click', async () => {{
      try {{
        await navigator.clipboard.writeText(outputEl.value || '');
        setStatus('草稿已复制到剪贴板。', false);
      }} catch (err) {{
        outputEl.select();
        setStatus('浏览器未允许自动复制，请手动复制文本框内容。', true);
      }}
    }});
    const initialContext = readContext();
    populateIdentity(initialContext.paper_identity || {{}});
    renderEvidence(initialContext);
    if (languageEl) {{ languageEl.addEventListener('change', loadExisting); }}
    loadExisting();
  }})();
  </script>"""
