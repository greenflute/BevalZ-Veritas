"""Retry command builders for failed audit diagnostics."""

import shlex
from pathlib import Path
from typing import Any, List


def _shell_quote(value: Any) -> str:
    return shlex.quote(str(value))


def _append_flag(parts: List[str], enabled: bool, flag: str):
    if enabled:
        parts.append(flag)


def retry_command_from_args(args, input_path: Path) -> str:
    """Build a retry command that keeps the current audit scope and reuses resume caches."""
    parts = ["python", "paper_audit.py", str(input_path)]

    option_pairs = [
        ("output", "--output"),
        ("mineru_model", "--mineru-model"),
        ("mineru_lang", "--mineru-lang"),
        ("max_chars", "--max-chars"),
        ("reference_online_limit", "--reference-online-limit"),
        ("reference_timeout", "--reference-timeout"),
        ("resource_timeout", "--resource-timeout"),
        ("image_audit_limit", "--image-audit-limit"),
        ("image_semantic_limit", "--image-semantic-limit"),
        ("image_semantic_timeout", "--image-semantic-timeout"),
        ("image_detector_limit", "--image-detector-limit"),
        ("image_detector_timeout", "--image-detector-timeout"),
        ("llm_timeout", "--llm-timeout"),
        ("llm_retries", "--llm-retries"),
    ]
    for attr, flag in option_pairs:
        value = getattr(args, attr, None)
        if value is not None and value != "":
            parts.extend([flag, str(value)])

    _append_flag(parts, bool(getattr(args, "json", False)), "--json")
    _append_flag(parts, bool(getattr(args, "no_open", False)), "--no-open")
    _append_flag(parts, bool(getattr(args, "mineru", False)), "--mineru")
    _append_flag(parts, bool(getattr(args, "no_mineru", False)), "--no-mineru")
    _append_flag(parts, bool(getattr(args, "no_reference_online", False)), "--no-reference-online")
    _append_flag(parts, bool(getattr(args, "no_resource_online", False)), "--no-resource-online")
    _append_flag(parts, bool(getattr(args, "no_image_semantic", False)), "--no-image-semantic")
    _append_flag(parts, bool(getattr(args, "no_image_detector", False)), "--no-image-detector")
    _append_flag(parts, bool(getattr(args, "strict_failed_chunks", False)), "--strict-failed-chunks")
    _append_flag(parts, bool(getattr(args, "ai_detect", False)), "--ai-detect")
    _append_flag(parts, bool(getattr(args, "image_detect", False)), "--image-detect")

    return " ".join(_shell_quote(part) for part in parts)


def default_retry_command(input_path: Path) -> str:
    return f"python paper_audit.py {_shell_quote(str(input_path))} --json"


__all__ = [
    "_shell_quote",
    "retry_command_from_args",
    "default_retry_command",
]
