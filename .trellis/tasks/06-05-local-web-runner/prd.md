# Build local web runner for non-technical audit workflow

## Goal

Create a local browser-based runner for Veritas so non-technical users can start an audit, watch progress, recover from failures, and open generated reports without learning CLI commands. The web runner should wrap the existing CLI behavior rather than replacing the audit engine.

## What I Already Know

- The current product is a CLI-first academic paper audit tool.
- Existing reports already provide Markdown, HTML, and JSON artifacts, including complete/limited/failed outcome types.
- Existing HTML reports already include review overview, internal evidence navigation, failed recovery guidance, and follow-up draft actions.
- Existing local report action service is implemented with Python standard library `ThreadingHTTPServer` under `serve_report_actions()`.
- The current audit orchestration lives mostly in `veritas/legacy.py`; `veritas/run.py`, `veritas/renderers.py`, `veritas/config.py`, and related modules are thin compatibility boundaries.
- `run_audit()` and the CLI path use global runtime state, print teeing, resume caches, and long-running third-party service calls.
- The user wants the next product direction to target non-technical users through a local app/web tool.

## Confirmed Decisions

- Build a local Web Runner, not a cloud service.
- First screen is an audit workbench, not a marketing/landing page.
- Start with a path input box plus recent-run history; do not build a native file picker in MVP.
- Use a new `--serve-web` CLI entry point.
- Keep `--serve-report-actions` for existing generated-report follow-up actions.
- `--serve-web` defaults to port `8765` and includes the existing report action endpoints.
- `--serve-report-actions` remains action-service-only for backward compatibility with existing HTML reports.
- The Web Runner launches actual audits.
- Use a single-task serial queue in MVP.
- Run audits through a subprocess that invokes the existing CLI.
- Do not call `run_audit()` in the web server process for MVP.
- Support canceling the current subprocess.
- Do not implement true pause/resume; rely on existing resume caches when users rerun.
- Keep audit artifacts in the existing CLI output locations.
- Maintain a local web history index, for example `.veritas_web/runs.json`.
- Config page checks configuration status only; it must not edit or save API keys.
- After completion, show summary and artifact navigation; do not rebuild the report reader.
- Existing `*.audit.html`, `*.limited.html`, and `*.failed.html` remain the detailed report reading surface.

## Requirements

### 1. Web Runner Entry Point

- Add a new local web entry point:
  - `python paper_audit.py --serve-web`
  - optionally exposed through installed `paper-audit --serve-web`
- Bind only to `127.0.0.1`.
- Default port is `8765`.
- Port conflicts should produce clear guidance and allow users to pick another port.
- `--serve-web` must serve the workbench plus the existing report action endpoints:
  - `/health`
  - `/generate`
  - `/followups`
- `--serve-report-actions` remains available for old reports and only needs to guarantee report action endpoints.
- The command should open the browser by default unless a server/CI-friendly flag disables auto-open.

### 2. Audit Workbench UI

- The first screen should be the actual tool surface.
- Provide:
  - input path field for file or directory
  - optional output stem/path field
  - from-scratch rerun checkbox mapped to `--fresh`
  - configuration status panel
  - start button
  - current run status
  - live log output
  - cancel button
  - recent run list
- The UI should be quiet, utilitarian, and optimized for repeated review work.
- Do not add a marketing hero page.

### 3. Running Audits

- Starting a run spawns a subprocess equivalent to:

```bash
python paper_audit.py <input_path> [-o <output_stem>] --json --no-open [--fresh]
```

- The web form should not expose advanced CLI switches in MVP.
- `--json` and `--no-open` are fixed by the Web Runner.
- Advanced flags such as `--no-mineru`, reference/image limits, `--llm-cache-only`, and provider disabling flags are out of scope for the first form.
- The server must capture stdout/stderr and expose it to the browser.
- Live log display should use simple polling in MVP, not SSE or WebSocket.
- Log polling endpoint should support an offset/cursor so the browser can fetch only new output.
- Only one run may be active at a time in MVP.
- Starting another run while one is active should return a clear busy state.
- Cancel should terminate the subprocess and explain that rerunning the same input will use resume caches where available.

### 4. Run History and Artifacts

- Keep existing CLI artifact placement semantics.
- Maintain a lightweight local history index with:
  - run id
  - input path
  - command
  - started/finished timestamps
  - status: running/succeeded/failed/canceled
  - artifact paths when discovered
  - report type when discoverable: complete/limited/failed
  - final summary fields when JSON report exists
- The history view should expose buttons/links for:
  - HTML report
  - Markdown report
  - JSON report
  - output folder when safely available
- Detailed report reading stays in generated HTML reports.
- Artifact serving must be allowlisted by recorded run metadata.
- The server must not expose an arbitrary local-file read or filesystem browser API.
- Artifact kinds should be limited in MVP to `html`, `markdown`, `json`, and `folder`.

### 5. Configuration Status

- Web Runner should check current config using existing runtime config/preflight helpers where safe.
- Display status for:
  - text LLM
  - MinerU
  - image semantic analysis
  - optional format dependencies such as `python-docx` and `openpyxl`
- Do not provide a form that writes API keys.
- Provide repair guidance that points users to `config.example.py`, `config.py`, and environment variables.

### 6. Failure and Recovery UX

- If audit subprocess exits non-zero, show:
  - failed status
  - recent log tail
  - discovered `*.failed.html/md/json` artifacts if present
  - retry guidance
- Failed reports remain the authoritative diagnostic details.
- The workbench should not generate PubPeer or journal-letter drafts directly; those remain in generated report pages.

## Acceptance Criteria

- [ ] `python paper_audit.py --serve-web` starts a localhost-only workbench.
- [ ] The workbench loads in a browser and shows path input, start/cancel controls, config status, live log area, and recent runs.
- [ ] The MVP form exposes only input path, optional output path/stem, and `--fresh`.
- [ ] Starting an audit spawns the existing CLI in a subprocess and writes normal audit artifacts.
- [ ] The browser can poll current-run logs without reloading the page.
- [ ] The server prevents a second concurrent audit in MVP.
- [ ] Cancel terminates the current subprocess and records a canceled run state.
- [ ] Successful runs appear in history with links to HTML/Markdown/JSON artifacts when present.
- [ ] Failed runs appear in history with links to failed diagnostics when present.
- [ ] Artifact endpoints only serve paths attached to recorded runs.
- [ ] The web UI does not store API keys.
- [ ] Existing `--serve-report-actions` behavior remains compatible with old HTML reports.
- [ ] Default tests do not call third-party services.
- [ ] `python3 -m py_compile paper_audit.py veritas/*.py tests/test_core.py` passes.
- [ ] `python3 paper_audit.py --help` passes.
- [ ] `python3 -m pytest tests/test_core.py -q` passes when pytest is available.

## Out of Scope

- Cloud upload or hosted service.
- Electron/native desktop packaging.
- Native OS file/folder picker.
- Concurrent run queue.
- True pause/resume state machine.
- Editing or saving API keys from the browser.
- Rebuilding the generated report reader.
- Replacing the existing audit engine.
- Large-scale `legacy.py` decomposition unless needed for a narrow web runner boundary.
- New detection logic or risk scoring changes.

## Technical Notes

- Likely implementation should add a new web runner boundary rather than expanding `serve_report_actions()` into unrelated responsibilities.
- The existing report action service can be reused or share helpers, but `--serve-web` must remain a distinct user-facing command.
- Subprocess execution avoids leaking global audit runtime state into the long-lived web server.
- `.paper_audit_runs/` remains the authoritative per-run workspace for audit details; `.veritas_web/runs.json` can be a convenience index.
- The UI should be no-build static HTML/CSS/JS unless a stronger need appears during implementation.
- Existing local web code and report action code live in `veritas/legacy.py` today; future refactoring can move web runner code into a dedicated module once the interface is stable.
- Prefer shared handler/helpers so `/generate` and `/followups` behavior does not diverge between `--serve-web` and `--serve-report-actions`.
