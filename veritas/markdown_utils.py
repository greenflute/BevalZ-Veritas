"""Markdown rendering utility helpers."""

import re

__all__ = ["_md_escape_cell"]


def _md_escape_cell(text):
    """Escape and normalize a Markdown table cell value."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text.replace("|", "\\|")
