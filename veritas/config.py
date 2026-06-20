"""Runtime configuration boundary."""

import importlib
import os
from typing import Any, Dict

from .runtime_config import (
    CapabilityConfig,
    DEFAULT_IMAGE_SEMANTIC_API_URL,
    DEFAULT_IMAGE_SEMANTIC_MODEL,
    DEFAULT_LLM_API_URL,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_RETRIES,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_MINERU_BASE,
    RuntimeConfig,
    default_runtime_config as _build_default_runtime_config,
    load_runtime_config as _build_runtime_config,
)

LLM_API_KEY = ""
LLM_API_URL = DEFAULT_LLM_API_URL
LLM_MODEL = DEFAULT_LLM_MODEL
MINERU_TOKEN = ""
MINERU_BASE = DEFAULT_MINERU_BASE
GLM_API_KEY = ""
GLM_API_URL = DEFAULT_IMAGE_SEMANTIC_API_URL
GLM_VISION_MODEL = DEFAULT_IMAGE_SEMANTIC_MODEL
LLM_TIMEOUT = DEFAULT_LLM_TIMEOUT
LLM_RETRIES = DEFAULT_LLM_RETRIES


def runtime_config_defaults(namespace: Dict[str, Any] = None) -> Dict[str, Any]:
    """Return runtime config defaults from a globals-like namespace."""
    values = namespace if namespace is not None else globals()
    return {
        "LLM_API_KEY": values.get("LLM_API_KEY", ""),
        "LLM_API_URL": values.get("LLM_API_URL", DEFAULT_LLM_API_URL),
        "LLM_MODEL": values.get("LLM_MODEL", DEFAULT_LLM_MODEL),
        "MINERU_TOKEN": values.get("MINERU_TOKEN", ""),
        "MINERU_BASE": values.get("MINERU_BASE", DEFAULT_MINERU_BASE),
        "IMAGE_SEMANTIC_API_KEY": values.get("IMAGE_SEMANTIC_API_KEY", values.get("GLM_API_KEY", "")),
        "IMAGE_SEMANTIC_API_URL": values.get("IMAGE_SEMANTIC_API_URL", values.get("GLM_API_URL", DEFAULT_IMAGE_SEMANTIC_API_URL)),
        "IMAGE_SEMANTIC_MODEL": values.get("IMAGE_SEMANTIC_MODEL", values.get("GLM_VISION_MODEL", DEFAULT_IMAGE_SEMANTIC_MODEL)),
        "LLM_TIMEOUT": values.get("LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT),
        "LLM_RETRIES": values.get("LLM_RETRIES", DEFAULT_LLM_RETRIES),
    }


def default_runtime_config_from_namespace(namespace: Dict[str, Any] = None) -> RuntimeConfig:
    return _build_default_runtime_config(defaults=runtime_config_defaults(namespace))


def load_runtime_config_from_namespace(
    namespace: Dict[str, Any] = None,
    config_module_name: str = "config",
    env=os.environ,
    verbose: bool = True,
) -> RuntimeConfig:
    helpers = (namespace or {}).get("importlib", importlib)
    return _build_runtime_config(
        config_module_name=config_module_name,
        env=env,
        verbose=verbose,
        defaults=runtime_config_defaults(namespace),
        import_module=helpers.import_module,
        reload_module=helpers.reload,
        invalidate_caches=helpers.invalidate_caches,
        printer=(namespace or {}).get("print", print),
    )


def apply_runtime_config_to_namespace(runtime_config: RuntimeConfig, namespace: Dict[str, Any] = None):
    """Apply explicit runtime config to a globals-like namespace."""
    values = namespace if namespace is not None else globals()
    values["LLM_API_KEY"] = runtime_config.text_llm.api_key
    values["LLM_API_URL"] = runtime_config.text_llm.api_url or values.get("LLM_API_URL", DEFAULT_LLM_API_URL)
    values["LLM_MODEL"] = runtime_config.text_llm.model or values.get("LLM_MODEL", DEFAULT_LLM_MODEL)
    values["MINERU_TOKEN"] = runtime_config.mineru.api_key
    values["MINERU_BASE"] = runtime_config.mineru.base_url or values.get("MINERU_BASE", DEFAULT_MINERU_BASE)
    values["GLM_API_KEY"] = runtime_config.image_semantic.api_key
    values["GLM_API_URL"] = runtime_config.image_semantic.api_url or values.get("GLM_API_URL", DEFAULT_IMAGE_SEMANTIC_API_URL)
    values["GLM_VISION_MODEL"] = runtime_config.image_semantic.model or values.get("GLM_VISION_MODEL", DEFAULT_IMAGE_SEMANTIC_MODEL)
    values["LLM_TIMEOUT"] = int(runtime_config.llm_timeout)
    values["LLM_RETRIES"] = int(runtime_config.llm_retries)
    return runtime_config


def default_runtime_config() -> RuntimeConfig:
    return default_runtime_config_from_namespace(globals())


def load_runtime_config(config_module_name: str = "config", env=os.environ, verbose: bool = True) -> RuntimeConfig:
    return load_runtime_config_from_namespace(globals(), config_module_name=config_module_name, env=env, verbose=verbose)


def apply_runtime_config(runtime_config: RuntimeConfig):
    return apply_runtime_config_to_namespace(runtime_config, globals())


__all__ = [
    "CapabilityConfig",
    "RuntimeConfig",
    "runtime_config_defaults",
    "default_runtime_config_from_namespace",
    "load_runtime_config_from_namespace",
    "apply_runtime_config_to_namespace",
    "default_runtime_config",
    "load_runtime_config",
    "apply_runtime_config",
]
