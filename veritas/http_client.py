"""Shared HTTP client helpers."""

import requests

__all__ = ["_http_request"]

_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def _http_request(url, method="GET", headers=None, data=None, timeout=60):
    """Send an HTTP request with the browser-like UA used by provider adapters."""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", _BROWSER_UA)
    if method.upper() == "GET":
        resp = requests.get(url, headers=headers, timeout=timeout)
    elif method.upper() == "POST":
        resp = requests.post(url, headers=headers, data=data, timeout=timeout)
    else:
        resp = requests.request(method, url, headers=headers, data=data, timeout=timeout)
    resp.raise_for_status()
    return resp.content, resp.status_code
