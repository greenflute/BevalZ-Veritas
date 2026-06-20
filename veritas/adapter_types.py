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


class MinerUAdapter:
    def preflight(self) -> AdapterResult:
        raise NotImplementedError

    def extract(self, file_path, language="ch", output_dir=None) -> AdapterResult:
        raise NotImplementedError


class TextLLMAdapter:
    def preflight(self) -> AdapterResult:
        raise NotImplementedError

    def review(self, text: str, chunk_info=None) -> AdapterResult:
        raise NotImplementedError


class ReferenceLookupAdapter:
    def audit(self, references_text: str, online=False, online_limit=50, timeout=10, cache=None) -> AdapterResult:
        raise NotImplementedError


class ImageSemanticAdapter:
    def analyze(self, image_path: str, timeout=45) -> AdapterResult:
        raise NotImplementedError


class ImageDetectorAdapter:
    def detect(self, image_path: str, timeout=60) -> AdapterResult:
        raise NotImplementedError


@dataclass
class AuditAdapters:
    mineru: MinerUAdapter
    text_llm: TextLLMAdapter
    reference_lookup: ReferenceLookupAdapter
    image_semantic: ImageSemanticAdapter
    image_detector: ImageDetectorAdapter


__all__ = [
    "AdapterResult",
    "MinerUAdapter",
    "TextLLMAdapter",
    "ReferenceLookupAdapter",
    "ImageSemanticAdapter",
    "ImageDetectorAdapter",
    "AuditAdapters",
]
