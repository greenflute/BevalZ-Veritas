"""External audit capability adapter boundary."""

from .legacy import (
    AuditAdapters,
    ProductionImageDetectorAdapter,
    ProductionImageSemanticAdapter,
    ProductionMinerUAdapter,
    ProductionReferenceLookupAdapter,
    ProductionTextLLMAdapter,
    default_audit_adapters,
    fake_audit_adapters,
)
from .adapter_types import AdapterResult

__all__ = [
    "AdapterResult",
    "AuditAdapters",
    "ProductionMinerUAdapter",
    "ProductionTextLLMAdapter",
    "ProductionReferenceLookupAdapter",
    "ProductionImageSemanticAdapter",
    "ProductionImageDetectorAdapter",
    "default_audit_adapters",
    "fake_audit_adapters",
]
