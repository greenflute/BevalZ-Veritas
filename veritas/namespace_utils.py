"""Small helpers for legacy namespace-aware compatibility seams."""

from collections.abc import Mapping
from typing import Any

__all__ = ["namespace_value"]


def namespace_value(namespace: Any, name: str, default: Any = None) -> Any:
    """Return a value from a legacy namespace mapping with a default fallback."""
    if namespace is None:
        return default
    if isinstance(namespace, Mapping):
        return namespace.get(name, default)
    return getattr(namespace, name, default)
