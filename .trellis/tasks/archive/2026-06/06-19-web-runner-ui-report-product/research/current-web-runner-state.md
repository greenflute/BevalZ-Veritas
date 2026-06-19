# Current Web Runner State

## Existing Implementation

- `WebRunnerState.start_run` resolves input paths, derives default output, creates output directories, starts the existing CLI subprocess, stores logs, and persists history.
- `WebRunnerState.discover_artifacts` checks complete, limited, and failed artifact path conventions and records existing Markdown, HTML, JSON, and folder outputs.
- `artifact_target` serves only recorded artifact kinds: `html`, `markdown`, `json`, and `folder`.
- `render_web_runner_page` currently renders a single-page local workbench with input/output selectors, config status, current run, logs, recent runs, retry, and artifact links.
- `serve_web_runner` exposes local HTTP routes for health, config, runs, logs, artifacts, path picking, cancel, and shared follow-up generation endpoints.

## Existing Test Coverage

- CLI exposes `--serve-web` / `--web-port`.
- Service mode loads runtime config and respects `--no-open`.
- Workbench HTML contains input, output, fresh, start, cancel, log, config, recent-runs, picker, drag/drop, current actions, and retry markers.
- Path picker avoids a browsable HTTP filesystem API.
- Drag/drop prefers full `file://` local paths and has basename fallback protections.
- Runs spawn the existing CLI with `--json --no-open`.
- Busy, cancel, and artifact allowlist behavior are tested.
- Config payload does not expose raw API keys.

## Product Gaps

- The UI has the core mechanics but still reads more like an internal control panel than a finished report-generation product.
- The current run panel can show input/output/actions but does not present a strong report completion card with report type, risk level, summary, and next actions.
- Errors are placed into the input card; they should be separated from selected input and shown as run feedback.
- Recent runs expose artifact links but not enough summary metadata for quickly choosing the correct report.
- The page has no explicit “ready to run / running / report ready” product rhythm.

## Recommended Direction

Build on the existing no-dependency local Web Runner:

- Keep the backend contract and artifact allowlist unchanged.
- Improve the HTML/CSS/JS in `render_web_runner_page` so the UI clearly communicates readiness, current run state, output destination, and report availability.
- Add tests that assert new stable DOM markers and summary rendering functions exist.
- Avoid a new framework until the existing stdlib UI cannot support a needed workflow.
