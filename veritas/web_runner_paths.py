"""Path resolution helpers for the local Web Runner."""

from pathlib import Path


def _web_runner_common_search_roots(cwd=None, home=None):
    cwd = Path(cwd or Path.cwd()).expanduser()
    home = Path(home or Path.home()).expanduser()
    roots = [(cwd, True), (home, False)]
    for name in ("Desktop", "Documents", "Downloads", "Videos", "Pictures"):
        roots.append((home / name, True))
    unique = []
    seen = set()
    for root, recursive in roots:
        try:
            resolved = root.resolve()
        except Exception:
            resolved = root
        key = str(resolved)
        if key not in seen and root.exists():
            unique.append((root, recursive))
            seen.add(key)
    return unique


def _web_runner_is_basename_only_input(raw):
    if not raw or raw in (".", ".."):
        return False
    return "/" not in raw and "\\" not in raw


def resolve_web_runner_input_path(input_path, search_roots=None, max_matches=8):
    """Resolve basename-only Web Runner inputs when browser drag/drop omits directories."""
    raw = str(input_path or "").strip()
    if not raw:
        return {"ok": False, "error": "input_path_required", "message": "请输入文件或目录路径。"}
    expanded = Path(raw).expanduser()
    if expanded.exists() or expanded.is_absolute() or not _web_runner_is_basename_only_input(raw):
        return {"ok": True, "path": str(expanded)}

    matches = []
    roots = search_roots if search_roots is not None else _web_runner_common_search_roots()
    for root_entry in roots:
        if isinstance(root_entry, (tuple, list)) and len(root_entry) == 2:
            root, recursive = root_entry
        else:
            root, recursive = root_entry, True
        root = Path(root).expanduser()
        if not root.exists():
            continue
        candidate = root / raw
        if candidate.exists():
            matches.append(candidate)
        if not recursive:
            continue
        try:
            for found in root.rglob("*"):
                if found.name != raw:
                    continue
                if found.exists():
                    matches.append(found)
                    if len(matches) >= max_matches:
                        break
        except Exception:
            pass
        if len(matches) >= max_matches:
            break

    unique = []
    seen = set()
    for match in matches:
        try:
            resolved = match.resolve()
        except Exception:
            resolved = match
        key = str(resolved)
        if key not in seen:
            unique.append(resolved)
            seen.add(key)

    if len(unique) == 1:
        return {"ok": True, "path": str(unique[0]), "resolved_from": raw}
    if len(unique) > 1:
        return {
            "ok": False,
            "error": "ambiguous_input_path",
            "message": "拖拽只提供了文件名，找到多个同名文件；请使用“文件”或“目录”按钮选择完整路径。",
            "candidates": [str(item) for item in unique[:max_matches]],
        }
    return {
        "ok": False,
        "error": "input_path_not_found",
        "message": f"路径不存在: {raw}；拖拽只提供了文件名，请使用“文件”或“目录”按钮选择完整路径。",
    }


__all__ = [
    "_web_runner_common_search_roots",
    "_web_runner_is_basename_only_input",
    "resolve_web_runner_input_path",
]
