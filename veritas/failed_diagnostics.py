"""Stable failed-audit diagnostic payload helpers."""

from pathlib import Path
from typing import Any, Dict

from .models import AuditFailure
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


__all__ = ["failed_audit_payload"]
