"""Image audit selection and cache-flush helpers."""

__all__ = [
    "_image_audit_sort_key",
    "_image_semantic_priority_key",
    "_image_detector_priority_key",
    "_flush_image_cache",
]


def _image_audit_sort_key(item):
    rank = {"local_warning": 0, "needs_online_check": 1, "local_ok": 2}
    return (rank.get(item.get("risk"), 3), -len(item.get("issues") or []), item.get("file", ""))


def _image_semantic_priority_key(item):
    width = int(item.get("width") or 0)
    height = int(item.get("height") or 0)
    min_side = min(width, height)
    max_side = max(width, height)
    area = width * height
    ratio = max_side / max(1, min_side)
    issues = set(item.get("issues") or [])

    # Use semantic model calls on images with enough visible information first.
    low_information = (
        min_side < 80
        or area < 30_000
        or ratio > 10
        or "near_blank_or_flat" in issues
        or "image_parse_error:UnidentifiedImageError" in issues
    )
    risk_rank = {"local_warning": 0, "needs_online_check": 1, "local_ok": 2}
    return (
        1 if low_information else 0,
        risk_rank.get(item.get("risk"), 3),
        -area,
        item.get("file", ""),
    )


def _image_detector_priority_key(item):
    width = int(item.get("width") or 0)
    height = int(item.get("height") or 0)
    area = width * height
    issues = set(item.get("issues") or [])
    local_warning = item.get("risk") == "local_warning"
    semantic = item.get("semantic") or {}
    semantic_attention = (semantic.get("reasonability") in {"需人工核对", "可疑"}) or bool(semantic.get("risks"))
    low_information = "near_blank_or_flat" in issues or area < 10_000
    return (
        1 if low_information else 0,
        0 if (local_warning or semantic_attention) else 1,
        -area,
        item.get("file", ""),
    )


def _flush_image_cache(cache_save, label):
    if not callable(cache_save):
        return
    try:
        cache_save()
    except Exception as e:
        print(f"⚠️ {label}断点缓存即时保存失败: {e}")
