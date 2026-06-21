"""Stable failed-audit diagnostic payload and rendering helpers."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .adapter_types import AdapterResult
from .artifacts import failed_audit_artifact_paths
from .html_utils import _html_escape
from .models import AuditFailure
from .preflight_types import PreflightResult
from .reference_reporting import format_reference_audit_markdown
from .resource_reporting import format_resource_audit_markdown
from .retry_commands import _shell_quote
from .runtime_metadata import ensure_runtime_meta


def failed_audit_payload(failure: AuditFailure, input_path: Path, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """Return the stable JSON payload for a failed audit diagnostic artifact."""
    meta = ensure_runtime_meta(meta)
    payload = {
        "report_type": "failed",
        "complete_report_generated": False,
        "input_path": str(input_path),
        "created_at": failure.created_at,
        "failure": {
            "capability": failure.capability,
            "error_class": failure.error_class,
            "message": failure.message,
            "fix_hints": list(failure.fix_hints),
            "completed_stages": list(failure.completed_stages),
            "retry_command": failure.retry_command,
            "details": dict(failure.details),
        },
        "meta": meta,
    }
    for key in ("reference_audit", "resource_audit", "image_audit"):
        if key in meta:
            payload[key] = meta[key]
    return payload


def preflight_failure_to_audit_failure(
    result: PreflightResult,
    retry_command: str,
    completed_stages: List[str],
) -> AuditFailure:
    hints = {
        "mineru": [
            "检查config.py或环境变量中的MINERU_TOKEN和MINERU_BASE。",
            "确认MinerU第三方服务可访问，网络代理和服务商状态正常。",
            "修复配置或网络后使用下方命令重试。",
        ],
        "text_llm": [
            "检查config.py或环境变量中的LLM_API_KEY、LLM_API_URL和LLM_MODEL。",
            "确认文本语义审查LLM服务可访问，账号额度、模型名和网关状态正常。",
            "修复配置或网络后使用下方命令重试。",
        ],
    }
    return AuditFailure(
        capability=result.capability,
        error_class=result.error_class or "preflight_failed",
        message=result.message or "关键能力预检失败。",
        fix_hints=hints.get(result.capability, ["检查关键服务配置、网络连通性和服务商返回状态后重试。"]),
        completed_stages=list(completed_stages),
        retry_command=retry_command,
        details=result.to_dict(),
        created_at=result.created_at,
    )


def adapter_failure_to_audit_failure(
    capability: str,
    result: AdapterResult,
    retry_command: str,
    completed_stages: List[str],
) -> AuditFailure:
    return AuditFailure(
        capability=capability,
        error_class=result.error_class or "adapter_failed",
        message=result.message or f"{capability} adapter failed",
        fix_hints=[
            "检查第三方服务配置、网络、账号额度和模型/接口参数。",
            "修复后使用下方命令重试。",
        ],
        completed_stages=list(completed_stages),
        retry_command=retry_command,
        details=result.to_dict(),
    )


def format_failed_audit_markdown(failure: AuditFailure, input_path: Path, meta: Dict[str, Any] = None) -> str:
    """Render a failed audit diagnostic report as Markdown."""
    payload = failed_audit_payload(failure, input_path, meta)
    failed = payload["failure"]
    fix_hints = failed["fix_hints"] or ["检查关键服务配置、网络连通性和服务商返回状态后重试。"]
    completed_stages = failed["completed_stages"] or ["无"]
    retry_command = failed["retry_command"] or f"python paper_audit.py {json.dumps(str(input_path), ensure_ascii=False)} --json"
    lines = [
        "# 学术论文审查失败诊断",
        "",
        "> 未生成完整审查报告。关键审查能力失败，本次运行只生成失败诊断产物。",
        "",
        "## 失败恢复面板",
        "",
        f"**文件**: `{input_path}`",
        f"**产物类型**: failed",
        f"**完整审查报告已生成**: 否",
        f"**失败时间**: {payload['created_at']}",
        "",
        "## 失败能力",
        "",
        f"- 能力: `{failed['capability']}`",
        f"- 错误类别: `{failed['error_class']}`",
        f"- 错误信息: {failed['message']}",
        "",
        "## 已完成阶段",
        "",
    ]
    lines.extend(f"- {stage}" for stage in completed_stages)
    lines.extend([
        "",
        "## 修复建议",
        "",
    ])
    lines.extend(f"- {hint}" for hint in fix_hints)
    lines.extend([
        "",
        "## 重试命令",
        "",
        "```bash",
        retry_command,
        "```",
    ])
    if failed["details"]:
        lines.extend([
            "",
            "## 技术细节",
            "",
            "```json",
            json.dumps(failed["details"], ensure_ascii=False, indent=2),
            "```",
        ])
    meta = payload.get("meta") or {}
    completed_sections = []
    if meta.get("resource_audit") is not None:
        completed_sections.extend(format_resource_audit_markdown(meta.get("resource_audit")))
    if meta.get("reference_audit") is not None:
        completed_sections.extend(format_reference_audit_markdown(meta.get("reference_audit")))
    if completed_sections:
        lines.extend([
            "",
            "## 已完成校检摘要",
            "",
            "> 以下为失败前已经完成并写入 JSON 的正式校检结果；失败能力修复后应重新运行以生成完整报告。",
            "",
        ])
        lines.extend(completed_sections)
    return "\n".join(lines)


def format_failed_audit_html(failure: AuditFailure, input_path: Path, meta: Dict[str, Any] = None) -> str:
    payload = failed_audit_payload(failure, input_path, meta)
    failed = payload["failure"]
    runtime = payload.get("meta", {}).get("runtime") or {}
    stages = failed.get("completed_stages") or ["无"]
    hints = failed.get("fix_hints") or ["检查关键服务配置、网络连通性和服务商返回状态后重试。"]
    retry_command = failed.get("retry_command") or f"python paper_audit.py {_shell_quote(str(input_path))} --json"
    details = failed.get("details") or {}
    cache_state = details.get("resume_dir") or details.get("cache_dir") or runtime.get("resume_dir") or "见运行日志/工作区"
    stages_html = "".join(f"<li>{_html_escape(stage)}</li>" for stage in stages)
    hints_html = "".join(f"<li>{_html_escape(hint)}</li>" for hint in hints)
    details_html = ""
    if details:
        details_html = f"""
    <section>
      <h2>技术细节</h2>
      <pre>{_html_escape(json.dumps(details, ensure_ascii=False, indent=2))}</pre>
    </section>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>审查失败诊断</title>
<style>
body {{ margin:0; padding:24px; font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif; background:#f6f6f6; color:#171717; line-height:1.6; }}
main {{ max-width:1080px; margin:0 auto; }}
.hero, section {{ background:#fff; border:1px solid #d4d4d4; border-radius:8px; padding:18px; margin-bottom:14px; }}
.status {{ display:inline-block; border-radius:6px; background:#b42318; color:#fff; padding:6px 10px; font-weight:800; margin-bottom:10px; }}
h1 {{ font-size:24px; margin:0 0 8px; }}
h2 {{ font-size:17px; margin:0 0 10px; border-bottom:1px solid #d4d4d4; padding-bottom:6px; }}
.grid {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:8px; margin-top:12px; }}
.cell {{ border:1px solid #d4d4d4; border-radius:6px; background:#fafafa; padding:9px; font-size:13px; color:#666; }}
.cell strong {{ display:block; color:#171717; overflow-wrap:anywhere; }}
pre, code {{ white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; background:#f1f1f1; border:1px solid #d4d4d4; border-radius:6px; padding:10px; display:block; }}
ul {{ padding-left:22px; }}
@media (max-width:760px) {{ body {{ padding:12px; }} .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<main>
  <div class="hero" id="failed-diagnostics">
    <div class="status">失败诊断 failed</div>
    <h1>失败恢复面板</h1>
    <p>关键审查能力失败，本次运行只生成失败诊断产物；修复后可使用下方命令断点续跑。</p>
    <div class="grid">
      <div class="cell"><span>文件</span><strong>{_html_escape(str(input_path))}</strong></div>
      <div class="cell"><span>失败能力</span><strong>{_html_escape(failed.get('capability'))}</strong></div>
      <div class="cell"><span>错误类别</span><strong>{_html_escape(failed.get('error_class'))}</strong></div>
      <div class="cell"><span>运行时间</span><strong>{_html_escape(runtime.get('local_time') or payload.get('created_at'))}</strong></div>
      <div class="cell"><span>运行时 UTC 年份</span><strong>{_html_escape(runtime.get('utc_year'))}</strong></div>
      <div class="cell"><span>缓存/恢复状态</span><strong>{_html_escape(cache_state)}</strong></div>
      <div class="cell"><span>产物类型</span><strong>failed</strong></div>
    </div>
  </div>
  <section>
    <h2>失败原因</h2>
    <p>{_html_escape(failed.get('message'))}</p>
  </section>
  <section>
    <h2>断点续跑命令</h2>
    <code>{_html_escape(retry_command)}</code>
  </section>
  <section>
    <h2>已完成阶段</h2>
    <ul>{stages_html}</ul>
  </section>
  <section>
    <h2>修复建议</h2>
    <ul>{hints_html}</ul>
  </section>
  {details_html}
</main>
</body>
</html>"""


def save_failed_audit_diagnostics(
    failure: AuditFailure,
    input_path: Path,
    output_dir: Path = None,
    output_stem: str = None,
    meta: Dict[str, Any] = None,
) -> Tuple[Path, Path]:
    """Write failed audit Markdown and JSON artifacts to the formal output location."""
    md_path, html_path, json_path = failed_audit_artifact_paths(input_path, output_dir=output_dir, output_stem=output_stem)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(format_failed_audit_markdown(failure, input_path, meta=meta), encoding="utf-8")
    html_path.write_text(format_failed_audit_html(failure, input_path, meta=meta), encoding="utf-8")
    json_path.write_text(json.dumps(failed_audit_payload(failure, input_path, meta=meta), ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


__all__ = [
    "failed_audit_payload",
    "preflight_failure_to_audit_failure",
    "adapter_failure_to_audit_failure",
    "format_failed_audit_markdown",
    "format_failed_audit_html",
    "save_failed_audit_diagnostics",
]
