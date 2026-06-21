"""Failed run artifact/result helpers."""

from pathlib import Path

from .run_types import RunResult

__all__ = ["save_failed_run_result"]


def save_failed_run_result(
    failure,
    input_path,
    run_workspace,
    save_failed_audit_diagnostics,
    record_run_workspace_artifacts,
    completed_stages=None,
    failed_artifact_kwargs=None,
    diagnostics_meta=None,
    workspace_meta=None,
    result_meta=None,
):
    """Save failed diagnostics, record workspace artifacts, and return RunResult."""
    diagnostics_kwargs = dict(failed_artifact_kwargs or {})
    if diagnostics_meta is not None:
        diagnostics_kwargs["meta"] = diagnostics_meta
    md_path, json_path = save_failed_audit_diagnostics(
        failure,
        input_path,
        **diagnostics_kwargs,
    )
    artifact_meta = {"completed_stages": list(completed_stages or [])}
    artifact_meta.update(workspace_meta or {})
    record_run_workspace_artifacts(
        run_workspace,
        "failed",
        [md_path, json_path],
        meta=artifact_meta,
    )
    meta = {"input_path": str(Path(input_path))}
    meta.update(result_meta or {})
    return RunResult.failed(
        failure,
        {"markdown": str(md_path), "json": str(json_path)},
        workspace=run_workspace,
        meta=meta,
    )
