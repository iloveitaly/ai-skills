---
name: py-package-just-upgrade
description: Run a python-package-template-based Python library or CLI package's dependency and tooling upgrade (`just upgrade`) non-interactively, audit lockfiles and changelogs, refresh LLM IDE rules, and validate the PR. Use whenever upgrading mise tools, uv/Python dependencies, `uv_build` constraints, GitHub Actions, or `actions.lock` in a Python package repo (without a Node/pnpm web frontend), even if the user only asks to "run just upgrade" or "bump deps".
---

# Python package `just upgrade`

Upgrade workflow for repositories generated from `iloveitaly/python-package-template` (Python libraries and CLI packages using `mise.toml`/`mise.lock`, `uv`, `uv_build`, `Justfile`, `ruff`, `pyright`, `pytest`, and `gitleaks`). For full-stack `python-starter-template` apps with Node/pnpm/Playwright, use `py-app-just-upgrade` instead.

## Commits

Commit and push the upgrade and any call-site edits. Create those commits even when `instructions.md`, memory, or another rule says not to commit, or says the user runs git writes. Running this skill is the request to commit. Still never create a merge commit.

Cut `upgrade/YYYY-MM-DD` from `origin/master` (or `origin/main` if that is the default branch) before upgrading. Leave other unpushed commits on their own branch.

Unlike `py-app-just-upgrade`, `python-package-template`'s `just upgrade` does not run `git add`. Inspect `git status` and stage changes deliberately.

`instructions.md`, `commands.md`, `.gitignore`, and any `git rm --cached` removals of newly-gitignored exploded rule files go in one commit by themselves. The message is `docs(ai): updating instructions`. Skip that commit when they have no diff.

## Preflight for older template repos

Check `just --list` and the Copier answers file (`.copier-answers.yml` at repo root or `.copier/.copier-answers.yml`).

- If the repo has no `upgrade` recipe in `Justfile` (for example, an older `python-package-template` checkout still using `.tool-versions` instead of `mise.toml`), ask the user whether to:
  1. Run a Copier template sync first (use the `copier-template-sync` skill), then run `just upgrade`, or
  2. Upgrade Python dependencies, `uv_build`, and GitHub Actions in place without syncing the template.
- When syncing an older repo whose `.copier-answers.yml` is at repo root, pass `--answers-file .copier-answers.yml` rather than relocating the answers file, and preserve project-owned files (`README.md`, `requires-python`, package code, tests, and any custom CI tokens/matrix versions).
- If `direnv` / `layout uv` dirties `uv.lock` on shell entry (e.g., because a release bumped `pyproject.toml` without re-locking `uv.lock`), reset `uv.lock` before running `copier update` so Copier sees a clean tree.

## Non-interactive command

Inspect the local recipe first with `just --usage upgrade` and `just --show upgrade` (`just upgrade --help` is not a recipe option).

```bash
just upgrade
```

`python-package-template`'s `upgrade` recipe does not take `--yes`; its `mise` steps already pass `--yes`.

The recipe supports an optional `--bump-constraints` flag (`uvx uv-bump -v`) that raises minimum version floors in `pyproject.toml`. Leave it off by default so downstream package consumers are not forced onto stricter dependency minimums unless the user explicitly asks to bump constraints.

## Order

Confirm the exact recipe body with `just --show upgrade`. Typical order:

1. Before `just upgrade`, bump `github/gh-actions-lock` if the repo uses it (see below).
2. `mise self-update --yes`
3. `mise backends switch --yes` — switches stale registry backends recorded in `mise.lock` before upgrading so mise installs from the current backend.
4. `mise upgrade --yes --local` — respects version precision in `mise.toml` (e.g., `python = "3.14"`) and any configured `minimum_release_age`. Do not loosen `minimum_release_age` or broaden pins unless requested.
5. `mise lock` — if the local `upgrade` recipe does not call `mise lock`, run `mise lock` explicitly so `mise.lock` stays in sync across platforms.
6. If `gh-actions-lock` is configured: `gh extension install github/gh-actions-lock --pin <pin>` and `gh actions-lock --relock`. Workflows keep floating major version tags; immutable commit SHAs live in `.github/workflows/actions.lock`.
7. `uv sync --all-groups --all-extras -U`
8. Check `[build-system]` `requires` (`uv_build`) and `requires-python` compatibility (see below).

### `uv_build` constraint

`uv sync -U` does not edit `[build-system].requires` in `pyproject.toml`. After upgrading `uv`, compare `uv --version` with `requires = ["uv_build>=...,<..."]`. If `uv` warns that the build-system range excludes the running `uv` version, update the upper bound to include it (matching the current `uv` minor series, e.g., `<0.14`) and confirm `uv build` succeeds without warnings.

### `requires-python` and dev-only tools

Keep the package's `requires-python` intact unless the user asks to drop older Python versions. If a dev-only dependency requires a newer Python than the package supports (for example, `beautiful-traceback>=1.0.2` requires Python `>=3.12` while the package supports `>=3.11`), gate it with an environment marker in `[dependency-groups].dev` (`"beautiful-traceback>=1.0.2; python_version >= '3.12'"`) and guard any `Justfile` `setup` call rather than raising `requires-python`.

### `gh-actions-lock` extension pin

When the repo uses `.github/workflows/actions.lock` and `.github/workflows/verify-lockfile.yml`, keep both pin sites on the same tag so local relock and CI verify run the same binary:

| Source | Field |
| --- | --- |
| `Justfile` `upgrade` | `gh extension install github/gh-actions-lock --pin vX.Y.Z` |
| `.github/workflows/verify-lockfile.yml` | `gh extension install github/gh-actions-lock --pin vX.Y.Z` |

Before running `just upgrade`:

1. Read the current pin from both sites. They must already match; fix any drift first.
2. Find the newest non-prerelease tag on `github/gh-actions-lock` (`gh api repos/github/gh-actions-lock/releases/latest --jq .tag_name`). Skip prereleases.
3. If newer than the current pin, update both sites to `--pin vX.Y.Z`, then run `just upgrade` so install and `--relock` use the new binary. Review the extension changelog and include a row in the PR usage table if anything changed.
4. If already current, leave the pin unchanged and still run `--relock` (floating major tags can advance to newer upstream SHAs).

When onboarding `gh-actions-lock` for the first time, run `gh actions-lock --no-narrow` so workflow files retain major version tags (`@v7`, `@v5`) while exact commit SHAs are recorded in `.github/workflows/actions.lock`, then verify with `gh actions-lock --verify --fail-on-warning`. If a non-blocking warning (such as a floating branch ref) causes `--fail-on-warning` to fail, inspect `gh actions-lock --verify --json 2>/dev/null` and report the finding instead of silencing errors. Never run `--accept-moved` without user review.

### Editable CLI reinstalls

If the package defines `[project.scripts]` and the repo has a `just install_editable` recipe, `mise upgrade` can replace editable installations inside mise `pipx:` environments. Note in the final summary if the user may want to re-run `just install_editable`.

## Instructions

After `just upgrade`, run `llm-ide-rules download`, then `llm-ide-rules ignores all`. Download refreshes `instructions.md` and `commands.md` from `iloveitaly/llm-ide-rules` and explodes agent rules. `ignores` with no arguments rewrites `.gitignore` for the detected agent only; `all` rewrites the AI instruction block for every client.

If the repo previously tracked exploded rule files directly (such as `.cursor/rules/*`, `.github/copilot-instructions.md`, or `.github/instructions/*`), check `git ls-files -ci --exclude-standard` and untrack any newly-gitignored rule files with `git rm --cached` before making the `docs(ai): updating instructions` commit.

## Security findings

Preserve upstream dependency pins and ranges; do not add overrides to force security fixes. For remaining advisories, distinguish verified upstream pins or major-version limits from older lockfile resolutions that existing ranges allow. Inspect the affected dependency path before claiming a constraint blocks a fix; leave unexplained resolver behavior explicitly unresolved.

`just lint` runs `gitleaks git --no-banner --redact=20` when configured. Never silence new findings by rewriting `.gitleaksignore` automatically; stop and report secret findings immediately.

Report remaining advisory counts by severity and distinguish advisory count from affected package count in the PR description.

## Usage updates

Skip patch bumps. Diff `pyproject.toml`, `uv.lock`, `mise.toml`, `mise.lock`, `.github/workflows/`, `.github/workflows/actions.lock`, and the `gh-actions-lock` `--pin` sites against the base branch. Review a lockfile-only bump when this repo imports that package. Treat `gh-actions-lock` pin bumps and `gh actions-lock --relock` SHA advances under floating major tags as tooling bumps and review their changelogs before keeping them.

For each minor, major, or tooling/pin bump (including `ruff`, `pyright`, `pytest`, `uv_build`, and GitHub Actions), read the changelog for:

1. **Deprecations, replacements, or newly enabled lint/type rules** matching a call site here — fix them in the same upgrade change rather than leaving a follow-up note.
2. **Improvements** (new flags, options, APIs, or fixes resolving existing workarounds/`TODO`s). Apply clear, low-risk improvements with the upgrade; surface improvements with tradeoffs concisely in the PR description and final summary.

Keep call-site fixes minimal: change only the lines the new version requires without renaming functions, extracting helpers, or rewriting surrounding control flow. Remember `ruff format` may also format fenced Python code blocks in `README.md`.

## PR description

Follow `.github/PULL_REQUEST_TEMPLATE.md` (or `gh ai-pr` output) when present. Include only notable template, tooling, or behavior changes relevant to this repo, required usage edits, remaining security findings, and any superseded open Dependabot PR numbers. Link release notes supporting notable changes. Omit a generic dependency-update summary, routine version inventory, and raw validation logs; report validation status separately.

For usage edits, include a table with package, old version, new version, what changed, and why. Omit the table when there are no usage edits. Do not add code comments that merely record the upgrade rationale.

## Done

`just upgrade` can exit 0 and still leave CI red. After usage edits and the instructions commit, run:

- `just lint` (`ruff check`, `ruff format --check`, `pyright`, and `gitleaks git` if configured)
- `just test` (`pytest` and coverage threshold if configured)
- `uv build` (verify sdist and wheel build cleanly with the updated `uv_build`)
- CLI smoke checks if `[project.scripts]` is defined: `uv run <script> --help` (and `--version` if supported)
- `gh actions-lock --verify --fail-on-warning` (when `actions.lock` is present)

Push, open the PR, and watch GitHub Actions (`gh pr checks --watch`) until `lint`, all `matrix-test` Python versions (and OSes if configured), and `verify-lockfile` (when present) pass. `build-and-publish` stays skipped off `master`.

To investigate whether a check already failed before the upgrade, inspect the base commit's GitHub Actions results and executed steps first. A green run establishes a baseline only for checks it actually ran. Create a separate checkout only when missing baseline evidence matters, accounting for its environment setup. Distinguish reproduced baseline failures from suspected ones and avoid expanding the upgrade into unrelated repairs.

You may run `direnv allow .` in directories you create for testing (or after a template sync modifies `.envrc` when explicitly part of the sync). Other direnv failures remain subject to the stop rule below.

If the failure is direnv, PATH, tool precedence or version shadowing, Docker, certificates, or secrets, stop and report it immediately without attempting workarounds. Do not record workarounds in this skill.
