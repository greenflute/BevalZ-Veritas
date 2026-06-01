# html-followup-draft-workflow

## Goal

Make the HTML report's PubPeer Comment and journal Letter generation safe and usable as formal follow-up draft production. Users must confirm article identity, choose evidence/language/tone, and receive persisted Markdown/JSON outputs under the report output directory without running a separate script for each draft.

## Confirmed Requirements

* The feature is HTML-first and uses the existing local report action service.
* Clicking "生成 PubPeer Comment" or "生成期刊 Letter" must open a confirmation workflow before LLM generation.
* Article identity must be visible and editable before generation:
  * title
  * journal
  * authors
  * DOI
  * year
  * report source path/context
* The confirmed identity must be saved to `followups/article_identity.json`.
* Users can choose language: `zh` / `en`.
* Users can choose tone: `conservative` / `standard` / `firm`; default is conservative.
* Users can select which report evidence items are included; default selection should favor red-flag/high-risk items.
* Users can add custom concerns, stored as `source: "user_added"` and clearly separated from automated findings.
* Users must confirm a short manual-review disclaimer before generation.
* Generated outputs must be written to the formal output directory:
  * `followups/pubpeer_comment.zh.md`
  * `followups/pubpeer_comment.en.md`
  * `followups/journal_letter.zh.md`
  * `followups/journal_letter.en.md`
  * `followups/followup_generation_log.json`
* Old HTML pages should be able to load existing follow-up files through the local action service and show already generated drafts.
* If the local action service is unavailable, the HTML must show the service URL and a copyable startup command.
* `failed` reports must not generate PubPeer/Letter drafts.
* `limited` reports may generate drafts, but the prompt/output must include a brief scope limitation statement.
* Generated content must state that concerns are based on reading and understanding the article and must match article title, journal, and author information.

## Out of Scope

* No batch CLI generation in the first version.
* No PubPeer auto-posting.
* No journal submission system automation.
* No rich text editor or multi-version diff UI.
* No complex version history UI; overwrite current language/type files while appending generation metadata to the JSON log.

## Acceptance Criteria

* [x] HTML follow-up controls require identity confirmation before draft generation.
* [x] Confirmed identity and generated drafts persist under `followups/`.
* [x] Existing follow-up files can be reloaded by reopening an old HTML report while the action service is running.
* [x] Action-service-unavailable errors include a copyable startup command.
* [x] PubPeer/Letter prompts receive article identity, selected evidence, custom concerns, language, tone, and scope status.
* [x] Failed reports are blocked from follow-up generation.
* [x] Tests cover server-side follow-up persistence, identity handling, failed-report blocking, and prompt payload construction.
* [x] README documents the old-page action service flow and follow-up artifacts.

## Technical Notes

* Likely locations:
  * `veritas/legacy.py` HTML report rendering and report action service.
  * `tests/test_core.py` existing report action service and renderer tests.
  * `README.md` HTML report/follow-up docs.
* Keep user-facing wording in Chinese where the existing report UI is Chinese.
* Persist metadata without storing LLM API keys.
