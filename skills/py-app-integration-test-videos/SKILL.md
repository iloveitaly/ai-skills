---
name: py-app-integration-test-videos
description: Run branch-relevant browser integration tests with video recording (and slow-motion), investigate and fix failures, watch the recorded videos against the PR description and codebase, and report improvements (UX issues, PR alignment gaps, and missing visual snapshots). Use whenever asked to validate branch changes with recorded integration tests, inspect Playwright test videos, review recordings for UX or PR alignment problems, or identify missing screenshot coverage.
---

# Integration test videos

Deliver passing branch-relevant integration tests, a complete set of preserved recordings, and an actionable improvement report grounded in watching those recordings. Automated assertions only check explicit expectations; watching the rendered flow in slow motion catches loading flashes, clipped modals, PR mismatches, and untested states that passing tests miss.

If the user points directly to existing recordings for review without requesting a test run, verify those files exist and start at **Inspect videos**.

## Select the scope

1. Read the repository instructions and test workflow. Use its prescribed runner and prerequisites; do not introduce a broad prerequisite suite unless the repository requires it.
2. Identify the branch's merge base with its intended target branch. Include staged, unstaged, and untracked changes when assessing the current work.
3. Select tests added on this branch and existing tests whose behavior should materially change because of the branch's implementation changes. Trace affected routes, shared components, and workflows; changed test files alone are not sufficient evidence of coverage. Exclude deleted tests and unrelated integration coverage.
4. State the selected scope and why it is relevant. Use test node IDs to narrow mixed files when appropriate. Do not default to the entire integration suite.

## Record videos and fix failures

1. Inspect pytest configuration, `conftest.py` hooks, and the installed browser plugin to identify recording flags, the effective artifact directory, and how browser launch options reach Playwright.
2. Enable full-suite recording and slow motion:
   - Use `--video=on` in pytest-playwright so successful runs retain recordings alongside failures.
   - Add a slow-motion delay (such as `--slowmo=150` for ~150 ms between actions) when recording for UX review. At full speed, loading skeletons, validation tooltips, modal transitions, and scroll jumps happen in a single frame or between keyframes; a short delay keeps transitions clearly observable without inflating runtime excessively.
   - If tests connect to a remote or containerized browser via WebSocket instead of launching locally, verify that the test harness forwards slow-motion into remote launch headers (e.g., mapping `slow_mo` to camelCase `slowMo` in `x-playwright-launch-options`) so `--slowmo` actually takes effect.
3. Preserve existing recordings before starting a run. Pytest-playwright's autouse `delete_output_dir` fixture clears the configured output directory at session startup. Prefer a unique directory per run using `--output` when respected; otherwise archive existing artifacts before every retry. Do not alter project configuration solely to preserve videos.
4. Run the selected tests and keep progress updates concise during long runs.
5. Investigate each failure using the traceback, server logs, captured DOM, screenshot, and browser console. Distinguish application defects, stale test expectations or fixtures, and transient browser failures. A model refreshed in the test process may still leave a separately loaded record stale after another server process updates it; verify persisted state before changing application behavior.
6. Fix demonstrated causes within the affected workflow while preserving unrelated working-tree changes. Do not weaken assertions, skip tests, blindly increase timeouts, or rubber-stamp snapshots just to obtain a pass. For a suspected transient failure, inspect artifacts and rerun the test before editing it; report uncertainty if the cause remains unproven.
7. Rerun failed tests with video and slow-mo enabled after fixes, repeating while evidence supports progress. Stop and report a concrete blocker when resolving it requires unavailable configuration, services, migrations, or permissions under repository rules. Do not fabricate required environment values or retry an unchanged deterministic failure indefinitely.
8. Retain recordings for every selected test, including tests that passed before retries. Merge preserved successful recordings with successful rerun artifacts, or rerun the selected set when needed to verify interactions between tests. Avoid rerunning unrelated tests or rerunning solely because artifacts were accidentally overwritten.

## Inspect videos

1. Verify each selected test has a non-empty recording corresponding to the final tested code. Do not rely on file counts alone when tests create multiple browser pages or contexts.
2. Watch every retained video from start to finish using native video reading (`read_file` on `.webm`/`.mp4` when supported, or extracting transition frames via `ffmpeg` if needed).
3. Read context on what the branch is trying to accomplish: inspect the PR description (e.g., `gh pr view`), recent branch commits, affected UI components, backend commands/routes, and existing visual snapshot calls (`assert_snapshot`).
4. Cross-check what renders on screen against the PR goals and source code, logging approximate timestamps (`MM:SS` or `MM:SS–MM:SS`) and code locations for every observation:
   - **UX issues:** Watch for theme/background discontinuities (unstyled `HydrateFallback` flashes, wrong-theme skeletons), clipped or awkwardly scrolling modals (headers, close buttons, or error alerts pushed out of view), form validation friction (duplicate browser + JS tooltips, raw placeholder text), typography or layout jumps, and third-party widget branding/mandate mismatches (payment forms, auth widgets, embeds).
   - **PR alignment gaps:** Check for stale campaign/product names, domains, or legacy components lingering in active flows; static/hardcoded tier numbers or metrics contradicting live backend data; incomplete flows; or tests whose assertions pass superficially without exercising key changed UI.
   - **Missing visual snapshots:** Identify key screens, states, error alerts, auth variants, or below-the-fold sections (especially where `reset_scroll` or viewport height clips rendered content) that lack snapshot coverage, naming the specific test function(s) and files where snapshots belong.

## Report results and improvements

Present a concise test run summary followed by the numbered improvement report and clickable absolute `file://` paths to recordings and relevant artifacts. Use stable dotted item numbers (`1.1`, `1.2`, ..., `2.1`, ..., `3.1`, ...) so the user can reference specific findings directly in follow-up prompts.

1. **Test run summary** (when tests ran): exact command, passed/failed/skipped counts and duration, selected scope and why it is relevant, whether results reflect targeted reruns or a full selected-suite pass, fixes made or unresolved blockers, and environment caveats (for example, disabled local visual snapshots).
2. **Improvement report** — organize findings under these headings (note if any section has no findings, plus briefly note verified fixes if inspecting after an edit pass):

```markdown
## 1. UX issues

**1.1. Short descriptive title**
- Video: [test-name (`MM:SS`–`MM:SS`)](file:///abs/path/to/video.webm)
- Code: [Component.tsx](file:///abs/path/to/Component.tsx#L10-L25)
- Observed behavior and root cause.

## 2. PR Alignment Issues

**2.1. Short descriptive title**
- Video / PR / Code links with approximate `MM:SS` timestamps where observable.
- Specific mismatch between PR description or goals and what was implemented or tested.

## 3. Missing Screenshots

**3.1. State or screen name** in `test_function_name` ([test_file.py](file:///abs/path/to/test_file.py#L100)) — uncaptured state or below-the-fold area missing snapshot coverage.
```

3. **All retained recordings & failure artifacts:** link every final `video.webm` (collapsing long lists in a `<details>` block) and any screenshots or `failure.html` traces for unresolved failures.

Repository-specific discovery example: `movie-tickets` assigns `config.option.output` from `PLAYWRIGHT_RESULT_DIRECTORY` in `tests/conftest.py` (overriding CLI `--output`), maps `slow_mo` to `slowMo` inside `x-playwright-launch-options` when connecting to `PLAYWRIGHT_CHROME_WS_ENDPOINT`, disables `assert_snapshot` locally on macOS (`is_local_testing()`), and typically writes videos to `tmp/test-results/playwright/<test-name>/video.webm`. Verify current configuration rather than assuming these details apply elsewhere.
