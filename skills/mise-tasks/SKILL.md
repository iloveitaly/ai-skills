---
name: mise-tasks
description: "Use when writing mise tasks to understand the latest syntax, features, and best practices"
---

# Writing mise tasks

The below documentation is pulled from: https://mise.jdx.dev/tasks/

It fully documents the mise task syntax and system.

---

# Tasks

Define and run project tasks for building, testing, linting, deploying, and everyday development workflows.

You can define tasks in `mise.toml` files or as standalone shell scripts. Tasks launched with mise include the mise environment — tools and env vars from `mise.toml`.

Favorite features:

- building dependencies in parallel — by default, no configuration required
- last-modified checking to skip rebuilds when nothing changed
- `mise watch` to rebuild on changes
- ability to write tasks as real script files instead of strings inside TOML

Run with `mise run <task>` (or `mise r <task>`). `mise <task>` works only if the name does not conflict with a mise command — never use that form in scripts or docs.

```bash
mise tasks                 # list tasks
mise run build
mise run --force build     # ignore sources/outputs freshness
mise run lint ::: test     # multiple tasks
mise run --silent build    # mise flags MUST come before the task name
mise watch build           # rerun on source changes (needs watchexec)
```

Default parallelism is 4 (`--jobs` / `MISE_JOBS`). Extra arguments after the task name belong to the task: `mise run build --release`.

Environment variables passed to every task:

- `MISE_ORIGINAL_CWD` — directory the task was invoked from
- `MISE_CONFIG_ROOT` — directory containing the `mise.toml` (or the project root if the config is at `.config/mise.toml`)
- `MISE_PROJECT_ROOT` — project that defines the task
- `MISE_TASK_NAME` — name of the task being run
- `MISE_TASK_DIR` — directory containing a file-task script
- `MISE_TASK_FILE` — full path to a file-task script

## TOML-based Tasks

Trivial tasks can be a one-liner in `[tasks]`. Detailed tasks each get their own section.

```toml
[tasks]
build = "cargo build"
test = "cargo test"
lint = "cargo clippy"
```

```toml
[tasks.build]
description = "Build the CLI"
run = "cargo build"
alias = "b"                          # mise run b

[tasks.test]
description = "Run automated tests"
run = [
    "cargo test",
    "./scripts/test-e2e.sh",         # extra args go to the last entry
]
dir = "{{cwd}}"                      # default is the project/config root

[tasks.lint]
description = "Lint with clippy"
env = { RUST_BACKTRACE = "1" }
run = "cargo clippy"

[tasks.ci]
description = "Run CI tasks"
depends = ["build", "lint", "test"]  # no run: just an orchestrator

[tasks.release]
confirm = "Are you sure you want to cut a new release?"
file = "scripts/release.sh"
```

Add tasks with `mise tasks add`:

```bash
mise tasks add pre-commit --depends "test" --depends "render" -- echo pre-commit
```

### `run`

The only required property. A string, an array of strings (series; stop on first failure), or a mix of scripts and nested task steps:

```toml
[tasks.grouped]
run = [
  { task = "t1" },
  { task = "build", args = ["--release"], env = { RUSTFLAGS = "-C opt-level=3" } },
  { tasks = ["t2", "t3"] },   # these two in parallel
  "echo end",
]
```

`{ task }` / `{ tasks }` are this task's own `run` steps, not `depends`. They still run with their own dependencies. `mise tasks deps` does not show them as graph edges.

Use `run_windows` for a Windows-specific command. Use `file = "scripts/release.sh"` to execute an external script instead of inline `run`.

### Shell / shebang

Set the default shell to zsh. Do not put a shebang on ordinary shell tasks.

```toml
[task_config]
shell = "zsh -c"
```

Inline `run` then uses that shell (`set -e` for zsh). A per-task `shell = "zsh -c"` overrides the default.

Shebang is a last resort: only when the interpreter is **not** that shell (Python, Node, uv, Deno, Ruby, …). Extra args that are not in a `usage` spec become `$1` / `$@` for shebang tasks.

```toml
[tasks.lint]
run = "ruff check ."

[tasks.python_task]
run = '''
#!/usr/bin/env python
for i in range(10):
    print(i)
'''
```

Quote colon names: `[tasks."test:unit"]`.

## File Tasks

Standalone executable scripts in one of:

- `mise-tasks/:task_name`
- `.mise-tasks/:task_name`
- `mise/tasks/:task_name`
- `.mise/tasks/:task_name`
- `.config/mise/tasks/:task_name`

The file **must be executable** (`chmod +x`). On Windows it also needs a shebang or an executable extension (`.ps1`, `.cmd`, `.bat`, …) so mise can detect it — that is a detection requirement, not a reason to shebang zsh tasks on Unix.

```zsh
#MISE description="Build the CLI"
#MISE alias="b"
#MISE sources=["Cargo.toml", "src/**/*.rs"]
#MISE outputs=["target/debug/mycli"]
#MISE env={RUST_BACKTRACE = "1"}
#MISE depends=["lint"]
#MISE timeout="5m"
cargo build
```

`#MISE` lines are TOML. Formatters that turn `#MISE` into `# MISE` silently drop the config — use `# [MISE]` if that happens. Arrays can span lines as long as every line keeps the prefix:

```bash
#MISE depends=[
#MISE   "lint",
#MISE   "test",
#MISE ]
#MISE tools.node="20"
```

Subdirectories become colon groups: `mise-tasks/test/unit` → `test:unit`. A `_default` file in a folder is the unprefixed group name (`mise-tasks/test/_default` → `test`).

Edit or create with `mise tasks edit build`. Run an arbitrary script with `mise run ./path/to/script.sh` (path must start with `/` or `./`).

Pair `build` + `build.ps1` in the same directory for native Windows; mise picks the right one per OS.

## Task Arguments

Define arguments with the `usage` field (TOML) or `#USAGE` comments (file tasks). Do **not** use Tera `{{arg()}}` / `{{option()}}` / `{{flag()}}` — deprecated, removal targeted at 2026.11.0.

Values are available as `$usage_*` env vars and as `{{ usage.* }}` in Tera. Hyphens become underscores: `--dry-run` → `$usage_dry_run` / `{{ usage.dry_run }}`.

```toml
[tasks.deploy]
description = "Deploy application"
usage = '''
arg "<environment>" help="Target environment" {
  choices "dev" "staging" "prod"
}
flag "-v --verbose" help="Enable verbose output"
flag "--region <region>" help="AWS region" default="us-east-1" env="AWS_REGION"
'''
run = '''
echo "Deploying to ${usage_environment?} in ${usage_region?}"
[[ "${usage_verbose:-false}" == "true" ]] && set -x
./deploy.sh "${usage_environment?}" "${usage_region?}"
'''
```

```bash
mise run deploy staging --verbose --region us-west-2
mise run deploy --help
```

Precedence: CLI argument > `env="VAR"` > usage `default=`.

File-task form:

```zsh
#MISE description="Deploy application"
#USAGE arg "<environment>" help="Deployment environment" {
#USAGE   choices "dev" "staging" "prod"
#USAGE }
#USAGE flag "--dry-run" help="Preview changes without deploying"
#USAGE flag "--region <region>" help="AWS region" default="us-east-1" env="AWS_REGION"

ENVIRONMENT="${usage_environment?}"
REGION="${usage_region?}"
DRY_RUN="${usage_dry_run:-false}"
```

Without a `usage` spec, extra args go to the last `run` entry (or `$1`/`$@` for a shebang). With a spec, unknown flags error. Proxy a real CLI with `raw_args = true` so `--help` is forwarded:

```toml
[tasks.manage]
raw_args = true
run = "python manage.py"
```

### Usage spec

```kdl
arg "<name>" help="Required positional"
arg "[name]" help="Optional positional" default="all"
arg "<file>"                                  // filename completion
arg "<files>" var=#true                       // 1 or more
arg "[files]" var=#true var_min=0 var_max=5
arg "<token>" env="API_TOKEN"

flag "-f --force"
flag "-v --verbose" count=#true               // -vvv → $usage_verbose = 3
flag "--dry-run" help="Preview only"
flag "-o --output <file>" default="out.txt"
flag "--color <when>" {
  choices "auto" "always" "never"
  default "auto"
}
flag "--color" negate="--no-color" default=#true

complete "plugin" run="mise plugins ls"
```

Variadic args are a shell-escaped string. Expand with `eval "files=($usage_files)"`.

zsh expansions (same `${…}` forms as bash):

| Syntax | When |
|---|---|
| `${usage_var?}` | Required, or has a usage `default=` |
| `${usage_var:?}` | Required and non-empty |
| `${usage_var:-false}` | Boolean flags with no default |
| `${usage_var:+--flag}` | Pass a flag through only when set |

Forward parent usage into a dependency — both tasks need a spec:

```toml
[tasks.build]
usage = 'arg "<app>"'
run = 'echo "building {{usage.app}}"'

[tasks.deploy]
usage = 'arg "<app>"'
depends = [{ task = "build", args = ["{{usage.app}}"] }]
run = 'echo "deploying {{usage.app}}"'
```

## Timeout

```toml
[tasks.integration-test]
run = "./scripts/integration-test.sh"
timeout = "10m"
```

Accepts `30s`, `5m`, `1h`, and Tera templates. The task fails if it overruns.

This is per-task. `mise run --timeout 5m` / the `task.timeout` setting limit the whole run. When both are set, the **shorter** wins — a per-task timeout cannot extend past the global one.

## Other properties that matter

### `depends` / `depends_post` / `wait_for`

```toml
[tasks.test]
depends = ["lint", "build"]          # must succeed first (parallel, deduped)
depends_post = ["cleanup"]           # after this task; runs even if this task failed (if it started)
wait_for = ["render"]                # wait only if render is already in this run
```

`confirm` only gates this task's own `run`. `depends` still run first. Confirm before work by putting `confirm` on the dependency, or use `run = [{ task = "…" }]` instead of `depends`.

Task-local `env` and `tools` are **not** inherited by `depends`.

### `sources` / `outputs`

Skip the task when outputs are newer than sources (mtime). The task definition is always a source. `outputs = { auto = true }` is the default when `sources` is set.

```toml
[tasks.build]
run = "cargo build"
sources = ["Cargo.toml", "src/**/*.rs", "!src/**/*.test.rs"]
outputs = ["target/debug/mycli"]
```

`!` exclusions are gitignore-style; later entries win. `mise run --force` ignores freshness. `mise watch build` uses `sources` as the watch set.

### `dir`, `env`, `vars`, `tools`

```toml
[tasks.test]
dir = "{{cwd}}"                      # follow the caller; default is config root
env = { RUST_BACKTRACE = "1" }
vars = { mode = "headed" }           # template-only, not exported
tools = { rust = "1.80" }            # this task only
run = "./scripts/test-e2e.sh --{{ vars.mode }}"
timeout = "10m"
```

Install task-only tools with `mise install --include-task-tools`.

### `raw` / `interactive` / `quiet` / `silent`

- `raw = true` — connect stdin/stdout/stderr; exclusive lock while that command runs
- `interactive = true` — same I/O, exclusive lock for the whole task (better for prompts)
- `quiet = true` — hide mise's `[task] $ cmd` lines; still shows task output
- `silent = true` — hide task stdout/stderr too (`"stdout"` / `"stderr"` for one stream)

### `hide`

`hide = true` omits the task from `mise tasks` and completions. Show with `mise tasks --hidden`.
