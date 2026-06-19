# Productize Web Runner UI report flow

## Goal

Turn the existing Veritas command-line audit flow into a local UI product that can select an input, start the audit, stream progress, and expose generated report outputs directly from the browser. Use the existing `--serve-web`, CLI subprocess, artifact naming, follow-up action service, and report rendering code instead of introducing a separate frontend stack.

## What I Already Know

- The user wants an end product, not a proposal: UI, direct report generation/output, autonomous design, 3-5 rounds of design/reasoning, and loophole closure.
- The repo already has `python paper_audit.py --serve-web [--web-port PORT] [--no-open]`.
- `veritas/legacy.py` contains `WebRunnerState`, `render_web_runner_page`, `serve_web_runner`, path picker support, run history, log polling, cancel/retry, and artifact allowlist serving.
- The audit subprocess already uses the existing CLI: `python paper_audit.py <input_path> --json --no-open [-o output] [--fresh]`.
- Existing tests cover Web Runner controls, config secrecy, path picking, drag/drop path extraction, basename fallback, run spawning, cancel, busy guard, artifact allowlisting, and CLI help.
- Current dirty worktree contains unrelated `Test_paper2` deletions and `.veritas_web/`; this task must not include or revert them.

## Assumptions

- Local-only UI is the intended product shape for now. The server remains bound to `127.0.0.1`.
- The current Python stdlib HTTP server is acceptable; no React/Vite/Electron dependency is required for this iteration.
- “直接生成报告输出” means the UI should make the report output path and generated artifacts obvious and actionable after the run completes.
- If third-party service credentials are missing, the UI should surface readiness clearly but must not expose secrets.

## Five Design Passes

### Pass 1: Product Shell

Decision: keep the existing local Web Runner and make it feel like the primary product surface.

Why: it already owns the real subprocess path, local file selection, run history, logs, artifact allowlisting, and report actions. A new frontend stack would duplicate plumbing without improving the audit pipeline.

Gap to close: make the first screen self-contained enough that a user can understand selected input, output destination, configuration readiness, run state, and final report actions without reading terminal output.

### Pass 2: Run Lifecycle

Decision: treat an audit as a single active job with explicit states: ready, running, succeeded, failed, canceled.

Why: the backend already has a single-active-run guard and live log polling. The UI should make that guard visible and prevent ambiguous starts.

Gap to close: improve disabled/enabled actions, status copy, and current-run summary so the UI never appears idle while a process is active or after a process produced artifacts.

### Pass 3: Report Output

Decision: the output stem is first-class UI data. Default output remains `<input-parent>/<project>_<timestamp>/audit_report`; generated artifact links are the direct completion path.

Why: artifact path rules are already shared with CLI artifact helpers. The UI should not invent a separate output convention.

Gap to close: show report type, risk level, summary preview, output folder, and artifact actions in the completion panel.

### Pass 4: Failure and Recovery

Decision: failures stay useful. Path problems, config gaps, active-run conflicts, missing artifacts, canceled runs, and failed diagnostic reports should all be represented as recoverable UI states.

Why: this project distinguishes complete, limited, and failed artifacts. The UI must not hide failed diagnostics or imply a complete report exists when only failed artifacts were generated.

Gap to close: surface backend error messages in the right panel, keep retry anchored to recorded run metadata, and make failed artifact links available when present.

### Pass 5: Local Security Boundary

Decision: keep local-only security strict: no uploaded file bytes, no arbitrary filesystem browser, no arbitrary artifact path serving, no API keys in JSON or HTML.

Why: the workbench runs on localhost but still exposes filesystem-adjacent actions. Existing allowlist behavior is the right boundary.

Gap to close: tests should verify that any new UI state still uses the existing allowlisted artifact routes and secret-safe config payload.

## Requirements

- The app must start with `python paper_audit.py --serve-web --web-port <port> --no-open`.
- The browser UI must be the primary flow for choosing input, choosing/deriving output, starting, canceling, retrying, and opening reports.
- The UI must expose generated report artifacts directly after completion: HTML, Markdown, JSON, and containing folder when available.
- The completion panel must show report type and summary/risk metadata when the JSON artifact contains it.
- The UI must clearly show config readiness without serializing raw API keys.
- The backend must continue to use the existing CLI subprocess and artifact path helpers.
- The app must remain local-only on `127.0.0.1` by default.
- Existing Web Runner path behavior, including explicit path preservation and basename fallback, must remain intact.
- Tests must cover any new UI markers and backend payload behavior.

## Acceptance Criteria

- [ ] `python paper_audit.py --serve-web --web-port <free-port> --no-open` serves a usable browser UI.
- [ ] `GET /` includes controls for input selection, output selection, start, cancel, config status, live logs, current run, report summary, and recent runs.
- [ ] A successful run record exposes artifact actions for available HTML/Markdown/JSON/folder outputs.
- [ ] A failed diagnostic run can expose failed artifact actions instead of hiding outputs.
- [ ] Current run rendering includes output path, report type, risk level, and summary preview when available.
- [ ] Config status remains secret-safe.
- [ ] The UI does not introduce arbitrary file reads outside recorded artifact allowlists.
- [ ] Focused Web Runner tests and full `tests/test_core.py` pass.

## Definition of Done

- Tests added/updated for UI and backend contract changes.
- `python3 -m py_compile paper_audit.py veritas/*.py tests/test_core.py` passes.
- `python3 paper_audit.py --help` passes.
- `python3 -m pytest tests/test_core.py -q` passes when pytest is available.
- The Web Runner is launched locally and the URL is provided to the user.

## Out of Scope

- Cloud deployment or public hosting.
- Multi-user auth, accounts, or remote uploads.
- Replacing the Python stdlib server with a separate frontend build system.
- Changing the core audit algorithms or third-party service contracts except where needed to expose current state safely.

## Technical Notes

- Primary code path: `veritas/legacy.py`.
- Primary tests: `tests/test_core.py`.
- Applicable spec: `.trellis/spec/backend/quality-guidelines.md`, especially the Local Web Runner Service Contract.
- Research artifact: `research/current-web-runner-state.md`.
