"""Stable result types for external audit capability adapters."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AdapterResult:
    """Structured result contract for external audit capability adapters."""
    status: str
    value: Any = None
    error_class: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, value=None, details: Dict[str, Any] = None):
        return cls("success", value=value, details=dict(details or {}))

    @classmethod
    def failure(cls, error_class: str, message: str, details: Dict[str, Any] = None):
        return cls("failure", error_class=error_class, message=message, details=dict(details or {}))

    @classmethod
    def skipped(cls, reason: str, message: str, details: Dict[str, Any] = None):
        return cls("skipped", error_class=reason, message=message, details=dict(details or {}))

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "value": self.value,
            "error_class": self.error_class,
            "message": self.message,
            "details": dict(self.details),
        }


__all__ = ["AdapterResult"]
