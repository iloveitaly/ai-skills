# Python template conventions

Read this reference for projects whose template source is [python-starter-template](https://github.com/iloveitaly/python-starter-template/) or [python-package-template](https://github.com/iloveitaly/python-package-template/). These are template-specific examples. Verify the local recipe and old/applied template revisions before acting; conventions can differ between generated projects.

## Recipe selection

Both templates provide `update_from_upstream_template`. Inspect and prefer the generated project's local recipe, including its dependencies and flags:

```bash
just --show update_from_upstream_template
just update_from_upstream_template
```

The upstream sources are [starter Justfile](https://github.com/iloveitaly/python-starter-template/blob/master/Justfile) and [package Justfile.jinja](https://github.com/iloveitaly/python-package-template/blob/master/Justfile.jinja). Use them to understand changes to the local recipe; do not substitute the upstream recipe wholesale.

These recipes use uv, the `jinja2_shell_extension` extension, `HEAD`, trust, skipped tasks, and recorded answers. Preserve the local choices. Diagnose malformed tool invocations or an incorrect answers-file path with a focused correction when it is within the update's scope, retaining the intended exclusions and other flags.

## python-starter-template

The starter recipe adds CLI exclusions beyond those in [copier.yml](https://github.com/iloveitaly/python-starter-template/blob/master/copier.yml). Examples include `web`, `migrations/versions/`, `infra/`, `pyproject.toml`, `uv.lock`, `.service-versions`, and `.config/mise.toml`. Read the actual local list and audit relevant upstream changes in those areas manually.

- Preserve application dependencies, database migration history, deployment choices, and frontend behavior while reconciling applicable configuration changes.
- Check both the template's tool configuration and excluded project configuration when tool pins or dependency inputs changed.
- Inspect the bootstrap script and tasks for file transformations that explain destination differences. Initialization commits, host setup, trust commands, and environment activation are not a checklist to replay during updates.
- Linting may span Python, frontend, database, and development configuration. When the update affects one of those surfaces, include it in the lint and test run from the main procedure.

## python-package-template

### Answers and CLI behavior

Recent revisions of [copier.yml](https://github.com/iloveitaly/python-package-template/blob/master/copier.yml) configure `.copier/.copier-answers.yml`. Older projects can have a root `.copier-answers.yml`. Identify the existing file and how the local recipe selects it before running an update; use the appropriate `--answers-file` option if a manual invocation requires it. Do not move or recreate the file solely to match a newer default.

Keep recorded `is_cli_tool`, `build_workflow`, `publish_docker_image`, `include_postgres`, and `add_llm_rules` choices unless a change is requested. If `is_cli_tool` is newly introduced, inspect entry points, module execution, documentation, and tests. Absence of `[project.scripts]` alone does not establish that the project has no CLI.

### Workflow mapping

Post-generation tasks select a workflow and rename it to `.github/workflows/build_and_publish.yml`:

| `build_workflow` answer | Template workflow before the move |
| --- | --- |
| `release_please` | `.github/workflows/build_and_publish_release_please.yml` |
| `release_please_matrix` | `.github/workflows/build_and_publish_release_please_test_matrix.yml` |
| `manual_matrix` | `.github/workflows/build_and_publish_test_matrix.yml` |

Verify this mapping at the old and applied revisions. Compare the selected rendered workflow with the project's canonical workflow. With tasks skipped, reconcile newly generated variant files according to the recorded choice and pre-update baseline; preserve intentionally added project workflows.

Review relevant upstream changes to checkout depth, mise setup and bootstrap options, CI environment variables, interpreter/matrix isolation, publish permissions, branch selection, and post-release lockfile synchronization. Preserve project-specific steps such as browser installation, integration services, and CLI checks. Adopt settings only when the selected workflow's changes and project requirements justify them.

### Package and tool reconciliation

- In `pyproject.toml`, preserve project name, version policy, application dependencies, entry points, and custom tool configuration. Reconcile upstream build requirements, classifiers, and development dependencies from the actual diff rather than hardcoded versions.
- When upstream changes version imports or exports, adapt the project's package layout and public API. Preserve existing import tests and add or adapt version checks only when the change warrants them. Remove a `main()` placeholder only after confirming it is unused boilerplate.
- Inspect effective exclusions for project-owned files such as `uv.lock`, `mise.lock`, metadata, licenses, and changelogs. Use the project's sync/lock commands when inputs changed.
- Inspect skipped workflow selection, conditional Docker/database files, tool setup, and rule-generation tasks. Respect their conditions and existing project choices. Do not regenerate a secret-scanning baseline or change GitHub settings as an automatic part of template reconciliation.
- Local recipe names vary. `uv sync`, `just lint-fix`, `just lint`, and `just test` are common. Add packaging or CLI checks when the update affects them.
