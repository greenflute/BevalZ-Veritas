"""Critical capability preflight boundary."""

from typing import Any, Dict

import requests

from .failed_diagnostics import preflight_failure_to_audit_failure
from .namespace_utils import namespace_value as _namespace_value
from .preflight_types import PreflightResult, run_preflight_once
from .runtime_config import (
    DEFAULT_IMAGE_SEMANTIC_API_URL,
    DEFAULT_IMAGE_SEMANTIC_MODEL,
    DEFAULT_LLM_API_URL,
    DEFAULT_LLM_MODEL,
    DEFAULT_MINERU_BASE,
)

LLM_API_KEY = ""
LLM_API_URL = DEFAULT_LLM_API_URL
LLM_MODEL = DEFAULT_LLM_MODEL
MINERU_TOKEN = ""
MINERU_BASE = DEFAULT_MINERU_BASE
GLM_API_KEY = ""
GLM_API_URL = DEFAULT_IMAGE_SEMANTIC_API_URL
GLM_VISION_MODEL = DEFAULT_IMAGE_SEMANTIC_MODEL


def _chat_completions_endpoint(api_url: str) -> str:
    """Accept either an OpenAI-compatible base URL or a full chat completions URL."""
    base = str(api_url or "").strip().rstrip("/")
    if not base:
        return base
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def preflight_mineru_from_namespace(namespace: Dict[str, Any] = None, timeout=10) -> PreflightResult:
    """Check MinerU reachability/auth using a globals-like namespace."""
    token = _namespace_value(namespace, "MINERU_TOKEN", MINERU_TOKEN)
    base_url = _namespace_value(namespace, "MINERU_BASE", MINERU_BASE)
    requests_module = _namespace_value(namespace, "requests", requests)
    if not token:
        return PreflightResult("mineru", False, "missing_required_config", "MINERU_TOKEN未配置")
    if not base_url:
        return PreflightResult("mineru", False, "missing_required_config", "MINERU_BASE未配置")

    url = f"{base_url.rstrip('/')}/api/v4/extract-results/batch/__paper_audit_preflight__"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "PaperAudit/1.0"}
    try:
        resp = requests_module.get(url, headers=headers, timeout=timeout)
        status = getattr(resp, "status_code", None)
        text = getattr(resp, "text", "") or ""
        details = {"http_status": status, "endpoint": url, "response_preview": text[:300]}
        if status in {401, 403}:
            return PreflightResult("mineru", False, "provider_auth_failed", "MinerU认证失败，请检查MINERU_TOKEN。", details)
        if status and status >= 500:
            return PreflightResult("mineru", False, "provider_unavailable", f"MinerU服务暂不可用: HTTP {status}", details)
        return PreflightResult("mineru", True, details=details)
    except Exception as exc:
        return PreflightResult("mineru", False, "provider_unavailable", f"MinerU预检请求失败: {exc}", {"endpoint": url})


def preflight_text_llm_from_namespace(namespace: Dict[str, Any] = None, timeout=10) -> PreflightResult:
    """Check the text LLM provider using a globals-like namespace."""
    api_key = _namespace_value(namespace, "LLM_API_KEY", LLM_API_KEY)
    api_url = _namespace_value(namespace, "LLM_API_URL", LLM_API_URL)
    model = _namespace_value(namespace, "LLM_MODEL", LLM_MODEL)
    requests_module = _namespace_value(namespace, "requests", requests)
    endpoint_builder = _namespace_value(namespace, "_chat_completions_endpoint", _chat_completions_endpoint)
    if not api_key:
        return PreflightResult("text_llm", False, "missing_required_config", "LLM_API_KEY未配置")
    if not api_url:
        return PreflightResult("text_llm", False, "missing_required_config", "LLM_API_URL未配置")
    if not model:
        return PreflightResult("text_llm", False, "missing_required_config", "LLM_MODEL未配置")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with OK."},
            {"role": "user", "content": "OK"},
        ],
        "temperature": 0,
        "max_tokens": 1,
    }
    endpoint = endpoint_builder(api_url)
    try:
        resp = requests_module.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "PaperAudit/1.0"},
            timeout=timeout,
        )
        status = getattr(resp, "status_code", None)
        details = {"http_status": status, "endpoint": endpoint, "model": model}
        if status in {401, 403}:
            return PreflightResult("text_llm", False, "provider_auth_failed", "文本LLM认证失败，请检查LLM_API_KEY。", details)
        if status and status >= 500:
            return PreflightResult("text_llm", False, "provider_unavailable", f"文本LLM服务暂不可用: HTTP {status}", details)
        if status and status >= 400:
            return PreflightResult("text_llm", False, "preflight_http_error", f"文本LLM预检失败: HTTP {status}", details)
        data = resp.json()
        if not data.get("choices"):
            return PreflightResult("text_llm", False, "preflight_invalid_response", "文本LLM预检未返回choices。", {**details, "response": data})
        return PreflightResult("text_llm", True, details=details)
    except Exception as exc:
        return PreflightResult("text_llm", False, "provider_unavailable", f"文本LLM预检请求失败: {exc}", {"endpoint": endpoint, "model": model})


def preflight_mineru(timeout=10) -> PreflightResult:
    return preflight_mineru_from_namespace(globals(), timeout=timeout)


def preflight_text_llm(timeout=10) -> PreflightResult:
    return preflight_text_llm_from_namespace(globals(), timeout=timeout)


__all__ = [
    "PreflightResult",
    "_chat_completions_endpoint",
    "preflight_mineru_from_namespace",
    "preflight_text_llm_from_namespace",
    "preflight_mineru",
    "preflight_text_llm",
    "run_preflight_once",
    "preflight_failure_to_audit_failure",
]
