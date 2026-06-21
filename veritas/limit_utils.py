"""Shared limit normalization helpers."""

__all__ = ["_effective_limit"]


def _effective_limit(limit, total: int) -> int:
    """Return a non-negative effective item limit, defaulting to all items."""
    return max(0, int(total if limit is None else limit))
