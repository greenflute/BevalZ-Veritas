"""External audit capability adapter boundary."""

from .legacy import (
    ProductionImageDetectorAdapter,
    ProductionImageSemanticAdapter,
    ProductionMinerUAdapter,
    ProductionReferenceLookupAdapter,
    ProductionTextLLMAdapter,
    default_audit_adapters,
    fake_audit_adapters,
)
from .adapter_types import (
    AdapterResult,
    AuditAdapters,
    ImageDetectorAdapter,
    ImageSemanticAdapter,
    MinerUAdapter,
    ReferenceLookupAdapter,
    TextLLMAdapter,
)

__all__ = [
    "AdapterResult",
    "AuditAdapters",
    "MinerUAdapter",
    "TextLLMAdapter",
    "ReferenceLookupAdapter",
    "ImageSemanticAdapter",
    "ImageDetectorAdapter",
    "ProductionMinerUAdapter",
    "ProductionTextLLMAdapter",
    "ProductionReferenceLookupAdapter",
    "ProductionImageSemanticAdapter",
    "ProductionImageDetectorAdapter",
    "default_audit_adapters",
    "fake_audit_adapters",
]
