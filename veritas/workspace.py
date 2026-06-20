"""Per-run workspace boundary."""

import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List

from .file_utils import _json_save, _safe_name


def create_run_workspace(input_path: Path, output_dir: Path, output_stem: str) -> Dict[str, Any]:
    """Create a unique per-run workspace while root-level reports remain latest shortcuts."""
    output_dir = Path(output_dir)
    run_token = hashlib.sha1(f"{time.time_ns()}|{os.getpid()}|{input_path}".encode("utf-8")).hexdigest()[:8]
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{_safe_name(output_stem)}-{run_token}"
    run_dir = output_dir / ".paper_audit_runs" / run_id
    artifacts_dir = run_dir / "artifacts"
    raw_dir = run_dir / "raw"
    intermediate_dir = run_dir / "intermediate"
    for path in (artifacts_dir, raw_dir, intermediate_dir):
        path.mkdir(parents=True, exist_ok=True)
    workspace = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "artifacts_dir": str(artifacts_dir),
        "raw_dir": str(raw_dir),
        "intermediate_dir": str(intermediate_dir),
        "created_at": time.strftime("%F %T"),
    }
    _json_save(run_dir / "workspace.json", workspace)
    return workspace


def run_workspace_path(workspace: Dict[str, Any], name: str) -> Path:
    return Path(workspace["run_dir"]) / name


def record_run_workspace_json(workspace: Dict[str, Any], name: str, payload: Dict[str, Any]):
    if not workspace:
        return None
    path = run_workspace_path(workspace, name)
    _json_save(path, payload)
    return path


def record_run_workspace_artifacts(
    workspace: Dict[str, Any],
    outcome: str,
    root_paths: List[Path],
    meta: Dict[str, Any] = None,
):
    """Copy latest root-level artifacts into the immutable run workspace and record pointers."""
    if not workspace:
        return None

    artifacts_dir = Path(workspace["artifacts_dir"])
    copied = []
    shortcuts = []
    for root_path in root_paths:
        if not root_path:
            continue
        root_path = Path(root_path)
        if not root_path.exists():
            continue
        target = artifacts_dir / root_path.name
        shutil.copy2(root_path, target)
        copied.append(str(target))
        shortcuts.append(str(root_path))
    payload = {
        "run_id": workspace["run_id"],
        "outcome": outcome,
        "root_shortcuts": shortcuts,
        "workspace_artifacts": copied,
        "meta": dict(meta or {}),
        "recorded_at": time.strftime("%F %T"),
    }
    return record_run_workspace_json(workspace, "report_outcome.json", payload)

__all__ = [
    "create_run_workspace",
    "run_workspace_path",
    "record_run_workspace_json",
    "record_run_workspace_artifacts",
]
