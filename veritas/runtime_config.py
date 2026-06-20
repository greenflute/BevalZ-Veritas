"""Runtime configuration schema and loading helpers."""

import importlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


DEFAULT_LLM_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"
DEFAULT_MINERU_BASE = "https://mineru.net"
DEFAULT_IMAGE_SEMANTIC_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_IMAGE_SEMANTIC_MODEL = "glm-4.6v-flash"
DEFAULT_LLM_TIMEOUT = 45
DEFAULT_LLM_RETRIES = 1


@dataclass
class CapabilityConfig:
    """Runtime settings for one externally backed audit capability."""
    name: str
    api_key: str = ""
    api_url: str = ""
    model: str = ""
    base_url: str = ""
    required: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def missing_required_fields(self) -> List[str]:
        missing = []
        if self.required and not self.api_key and self.name in {"text_llm", "mineru", "image_semantic"}:
            missing.append("api_key")
        if self.required and not self.api_url and self.name in {"text_llm", "image_semantic"}:
            missing.append("api_url")
        if self.required and not self.model and self.name in {"text_llm", "image_semantic"}:
            missing.append("model")
        if self.required and not self.base_url and self.name == "mineru":
            missing.append("base_url")
        return missing


@dataclass
class RuntimeConfig:
    """Explicit runtime configuration, loaded by CLI rather than at import time."""
    text_llm: CapabilityConfig
    mineru: CapabilityConfig
    reference_lookup: CapabilityConfig
    image_semantic: CapabilityConfig
    image_detector: CapabilityConfig
    llm_timeout: int = DEFAULT_LLM_TIMEOUT
    llm_retries: int = DEFAULT_LLM_RETRIES

    def validation_errors(self) -> List[Dict[str, str]]:
        errors = []
        for capability in (
            self.text_llm,
            self.mineru,
            self.reference_lookup,
            self.image_semantic,
            self.image_detector,
        ):
            for field_name in capability.missing_required_fields():
                errors.append({"capability": capability.name, "field": field_name, "error": "missing_required_config"})
        return errors


def _default_values(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    values = {
        "LLM_API_KEY": "",
        "LLM_API_URL": DEFAULT_LLM_API_URL,
        "LLM_MODEL": DEFAULT_LLM_MODEL,
        "MINERU_TOKEN": "",
        "MINERU_BASE": DEFAULT_MINERU_BASE,
        "IMAGE_SEMANTIC_API_KEY": "",
        "IMAGE_SEMANTIC_API_URL": DEFAULT_IMAGE_SEMANTIC_API_URL,
        "IMAGE_SEMANTIC_MODEL": DEFAULT_IMAGE_SEMANTIC_MODEL,
        "LLM_TIMEOUT": DEFAULT_LLM_TIMEOUT,
        "LLM_RETRIES": DEFAULT_LLM_RETRIES,
    }
    values.update(overrides or {})
    return values


def default_runtime_config(defaults: Dict[str, Any] = None) -> RuntimeConfig:
    values = _default_values(defaults)
    return RuntimeConfig(
        text_llm=CapabilityConfig(
            "text_llm",
            api_key=values["LLM_API_KEY"],
            api_url=values["LLM_API_URL"],
            model=values["LLM_MODEL"],
        ),
        mineru=CapabilityConfig("mineru", api_key=values["MINERU_TOKEN"], base_url=values["MINERU_BASE"]),
        reference_lookup=CapabilityConfig("reference_lookup", required=False),
        image_semantic=CapabilityConfig(
            "image_semantic",
            api_key=values["IMAGE_SEMANTIC_API_KEY"],
            api_url=values["IMAGE_SEMANTIC_API_URL"],
            model=values["IMAGE_SEMANTIC_MODEL"],
        ),
        image_detector=CapabilityConfig("image_detector", base_url="https://imagedetector.com/", required=False),
        llm_timeout=int(values["LLM_TIMEOUT"]),
        llm_retries=int(values["LLM_RETRIES"]),
    )


def load_runtime_config(
    config_module_name: str = "config",
    env=os.environ,
    verbose: bool = True,
    defaults: Dict[str, Any] = None,
    import_module=None,
    reload_module=None,
    invalidate_caches=None,
    printer=print,
) -> RuntimeConfig:
    """Load config.py and environment variables explicitly for one run."""
    values = _default_values(defaults)
    import_module = import_module or importlib.import_module
    reload_module = reload_module or importlib.reload
    invalidate_caches = invalidate_caches or importlib.invalidate_caches
    cfg = None
    try:
        invalidate_caches()
        cfg = import_module(config_module_name)
        if getattr(cfg, "__spec__", None) is not None:
            cfg = reload_module(cfg)
        if verbose:
            printer(f"✅ 从 {config_module_name}.py 加载配置")
    except ImportError:
        if verbose:
            printer(f"⚠️ 未找到 {config_module_name}.py，将使用环境变量和默认配置")

    def value(name, default=""):
        if cfg is not None and hasattr(cfg, name):
            return getattr(cfg, name)
        return env.get(name, default)

    llm_timeout = values["LLM_TIMEOUT"]
    llm_retries = values["LLM_RETRIES"]
    try:
        llm_timeout = int(value("LLM_TIMEOUT", values["LLM_TIMEOUT"]))
        llm_retries = int(value("LLM_RETRIES", values["LLM_RETRIES"]))
    except (TypeError, ValueError) as e:
        if verbose:
            printer(f"⚠️ LLM_TIMEOUT/LLM_RETRIES配置无效，已使用默认值: {e}")

    return RuntimeConfig(
        text_llm=CapabilityConfig(
            "text_llm",
            api_key=value("LLM_API_KEY", ""),
            api_url=value("LLM_API_URL", values["LLM_API_URL"]),
            model=value("LLM_MODEL", values["LLM_MODEL"]),
        ),
        mineru=CapabilityConfig(
            "mineru",
            api_key=value("MINERU_TOKEN", ""),
            base_url=value("MINERU_BASE", values["MINERU_BASE"]),
        ),
        reference_lookup=CapabilityConfig("reference_lookup", required=False),
        image_semantic=CapabilityConfig(
            "image_semantic",
            api_key=value("IMAGE_SEMANTIC_API_KEY", env.get("IMAGE_SEMANTIC_API_KEY", value("GLM_API_KEY", env.get("GLM_API_KEY", "")))),
            api_url=value("IMAGE_SEMANTIC_API_URL", env.get("IMAGE_SEMANTIC_API_URL", value("GLM_API_URL", env.get("GLM_API_URL", values["IMAGE_SEMANTIC_API_URL"])))),
            model=value("IMAGE_SEMANTIC_MODEL", env.get("IMAGE_SEMANTIC_MODEL", value("GLM_VISION_MODEL", env.get("GLM_VISION_MODEL", values["IMAGE_SEMANTIC_MODEL"])))),
        ),
        image_detector=CapabilityConfig("image_detector", base_url="https://imagedetector.com/", required=False),
        llm_timeout=llm_timeout,
        llm_retries=llm_retries,
    )


__all__ = [
    "CapabilityConfig",
    "RuntimeConfig",
    "default_runtime_config",
    "load_runtime_config",
]
