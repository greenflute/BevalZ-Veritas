"""Image audit cache key helpers."""

import hashlib
from pathlib import Path

from .preflight import _chat_completions_endpoint

__all__ = [
    "_image_file_fingerprint",
    "_image_file_fingerprint_from_namespace",
    "_image_semantic_cache_key",
    "_image_semantic_cache_key_from_namespace",
]


def _default_text_fingerprint(text: str, extra: str = ""):
    h = hashlib.sha256()
    h.update((extra or "").encode("utf-8", errors="ignore"))
    h.update(b"\n---TEXT---\n")
    h.update((text or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _namespace_value(namespace, name, default=None):
    if isinstance(namespace, dict):
        return namespace.get(name, default)
    return getattr(namespace, name, default)


def _image_file_fingerprint(image_path: str, cache_version, text_fingerprint_func=None):
    text_fingerprint = text_fingerprint_func or _default_text_fingerprint
    try:
        path = Path(image_path)
        stat = path.stat()
        return text_fingerprint(str(path.resolve()), f"{stat.st_size}|{int(stat.st_mtime)}|semantic_v{cache_version}")
    except Exception:
        return text_fingerprint(str(image_path), f"semantic_v{cache_version}")


def _image_file_fingerprint_from_namespace(namespace, image_path: str, cache_version=None):
    version = _namespace_value(namespace, "IMAGE_SEMANTIC_CACHE_VERSION", 1) if cache_version is None else cache_version
    text_fingerprint = _namespace_value(namespace, "_text_fingerprint", _default_text_fingerprint)
    return _image_file_fingerprint(image_path, version, text_fingerprint_func=text_fingerprint)


def _image_semantic_cache_key(
    image_path: str,
    api_url,
    model,
    cache_version,
    text_fingerprint_func=None,
    endpoint_builder=_chat_completions_endpoint,
):
    text_fingerprint = text_fingerprint_func or _default_text_fingerprint
    endpoint = endpoint_builder(api_url)
    service_fingerprint = text_fingerprint(endpoint, f"{model}|image_semantic_v{cache_version}")
    image_fingerprint = _image_file_fingerprint(image_path, cache_version, text_fingerprint_func=text_fingerprint)
    return f"{image_fingerprint}:image_semantic:{service_fingerprint}"


def _image_semantic_cache_key_from_namespace(namespace, image_path: str, api_url=None, model=None, cache_version=None):
    version = _namespace_value(namespace, "IMAGE_SEMANTIC_CACHE_VERSION", 1) if cache_version is None else cache_version
    selected_api_url = api_url or _namespace_value(namespace, "GLM_API_URL", "")
    selected_model = model or _namespace_value(namespace, "GLM_VISION_MODEL", "")
    text_fingerprint = _namespace_value(namespace, "_text_fingerprint", _default_text_fingerprint)
    endpoint_builder = _namespace_value(namespace, "_chat_completions_endpoint", _chat_completions_endpoint)
    return _image_semantic_cache_key(
        image_path,
        selected_api_url,
        selected_model,
        version,
        text_fingerprint_func=text_fingerprint,
        endpoint_builder=endpoint_builder,
    )
