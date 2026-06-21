"""Online availability checks for code and deployed resources."""

import re

from .namespace_utils import namespace_value as _namespace_value
from .resource_parsing import _clean_resource_url, extract_paper_resources
from .text_utils import _brief_text

__all__ = [
    "verify_resource_availability_from_namespace",
    "audit_resources_from_namespace",
]


def verify_resource_availability_from_namespace(namespace, resource, timeout=10):
    http_request = _namespace_value(namespace, "_http_request")
    if not callable(http_request):
        raise RuntimeError("resource availability namespace is incomplete")
    url = _clean_resource_url((resource or {}).get("url", ""))
    if not re.match(r"^https?://", url, flags=re.I):
        return {
            "status": "malformed",
            "http_status": None,
            "problem": "malformed_url",
            "message": "URL scheme is malformed or unsupported.",
        }
    headers = {"Accept": "text/html,application/json,*/*;q=0.8"}
    try:
        _, status = http_request(url, "GET", headers=headers, timeout=timeout)
        return {
            "status": "available" if 200 <= int(status) < 400 else "unavailable",
            "http_status": int(status),
            "problem": "",
            "message": "reachable",
        }
    except Exception as e:
        response = getattr(e, "response", None)
        status = getattr(response, "status_code", None)
        if status in {401, 403}:
            availability = "access_restricted"
            problem = "access_restricted"
        elif status in {404, 410}:
            availability = "unavailable"
            problem = "not_found"
        elif status:
            availability = "error"
            problem = f"http_{status}"
        else:
            availability = "error"
            problem = type(e).__name__
        return {
            "status": availability,
            "http_status": status,
            "problem": problem,
            "message": _brief_text(str(e), 240),
        }


def audit_resources_from_namespace(namespace, text, online=True, timeout=10, cache=None):
    verifier = _namespace_value(namespace, "verify_resource_availability")
    if not callable(verifier):
        verifier = lambda resource, timeout=10: verify_resource_availability_from_namespace(namespace, resource, timeout=timeout)
    resources = extract_paper_resources(text)
    resource_cache = cache if isinstance(cache, dict) else {}
    checked = 0
    issues = []
    for idx, resource in enumerate(resources, 1):
        if online:
            cache_key = resource["url"].lower()
            result = resource_cache.get(cache_key)
            if not result:
                result = verifier(resource, timeout=timeout)
                resource_cache[cache_key] = result
            resource["availability"] = result
            checked += 1
            if result.get("status") in {"unavailable", "access_restricted", "malformed", "error"}:
                issues.append({
                    "index": idx,
                    "url": resource.get("url", ""),
                    "type": resource.get("type", ""),
                    "status": result.get("status", ""),
                    "problem": result.get("problem", ""),
                    "context": resource.get("context", ""),
                })
        else:
            resource["availability"] = {"status": "skipped", "problem": "online_disabled"}

    status = "ok"
    if issues:
        error_count = sum(1 for item in issues if item.get("status") == "error")
        status = "error" if resources and online and error_count == len(resources) else "needs_review"
    return {
        "status": status,
        "resource_count": len(resources),
        "online_enabled": bool(online),
        "online_checked": checked,
        "issues": issues,
        "resources": resources[:200],
        "note": "校检论文声明的代码仓库、在线计算器、部署平台等资源是否可访问；URL格式错误会单独标记。",
    }
