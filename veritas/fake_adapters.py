"""Deterministic fake audit capability adapters for tests and replay harnesses."""

from pathlib import Path
from typing import Any, Dict

from .adapter_types import (
    AdapterResult,
    AuditAdapters,
    ImageDetectorAdapter,
    ImageSemanticAdapter,
    MinerUAdapter,
    ReferenceLookupAdapter,
    TextLLMAdapter,
)


class FakeScenarioMixin:
    SCENARIOS = {
        "auth_failure": ("failure", "provider_auth_failed", "fake auth failure"),
        "network_failure": ("failure", "provider_unavailable", "fake network failure"),
        "rate_limit": ("failure", "provider_rate_limited", "fake rate limit"),
        "schema_error": ("failure", "schema_error", "fake schema error"),
        "unsupported_content": ("skipped", "unsupported_content", "fake unsupported content"),
    }

    def __init__(self, scenario="success", value=None, details=None):
        self.scenario = scenario
        self.value = value
        self.details = dict(details or {})

    def _result(self, default_value=None) -> AdapterResult:
        if self.scenario == "success":
            return AdapterResult.success(self.value if self.value is not None else default_value, self.details)
        status, error_class, message = self.SCENARIOS.get(
            self.scenario,
            ("failure", "fake_error", f"unknown fake scenario: {self.scenario}"),
        )
        if status == "skipped":
            return AdapterResult.skipped(error_class, message, self.details)
        return AdapterResult.failure(error_class, message, self.details)


class FakeMinerUAdapter(FakeScenarioMixin, MinerUAdapter):
    def preflight(self) -> AdapterResult:
        return self._result({"capability": "mineru"})

    def extract(self, file_path: Path, language="ch", output_dir=None) -> AdapterResult:
        return self._result({"text": "fake mineru text", "meta": {"source": "fake_mineru"}})


class FakeTextLLMAdapter(FakeScenarioMixin, TextLLMAdapter):
    def preflight(self) -> AdapterResult:
        return self._result({"capability": "text_llm"})

    def review(self, text: str, chunk_info=None) -> AdapterResult:
        return self._result('{"summary":"fake","risk_level":"低","checks":[],"conclusion":"fake"}')


class FakeReferenceLookupAdapter(FakeScenarioMixin, ReferenceLookupAdapter):
    def audit(self, references_text: str, online=False, online_limit=50, timeout=10, cache=None) -> AdapterResult:
        return self._result({"status": "ok", "reference_count": 0, "references": []})


class FakeImageSemanticAdapter(FakeScenarioMixin, ImageSemanticAdapter):
    def analyze(self, image_path: str, timeout=45) -> AdapterResult:
        return self._result({"status": "ok", "summary": "fake image semantics"})


class FakeImageDetectorAdapter(FakeScenarioMixin, ImageDetectorAdapter):
    def detect(self, image_path: str, timeout=60) -> AdapterResult:
        return self._result({"status": "ok", "score": 0, "label": "fake"})


def fake_audit_adapters(scenario="success", values: Dict[str, Any] = None) -> AuditAdapters:
    values = values or {}
    return AuditAdapters(
        mineru=FakeMinerUAdapter(scenario=scenario, value=values.get("mineru")),
        text_llm=FakeTextLLMAdapter(scenario=scenario, value=values.get("text_llm")),
        reference_lookup=FakeReferenceLookupAdapter(scenario=scenario, value=values.get("reference_lookup")),
        image_semantic=FakeImageSemanticAdapter(scenario=scenario, value=values.get("image_semantic")),
        image_detector=FakeImageDetectorAdapter(scenario=scenario, value=values.get("image_detector")),
    )


__all__ = [
    "FakeScenarioMixin",
    "FakeMinerUAdapter",
    "FakeTextLLMAdapter",
    "FakeReferenceLookupAdapter",
    "FakeImageSemanticAdapter",
    "FakeImageDetectorAdapter",
    "fake_audit_adapters",
]
