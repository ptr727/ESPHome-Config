# Code Style and Formatting Rules

This is the single code-style guide for the fleet. The **General** section applies to every language. Each **language section** (.NET, Python, Shell, and the `C++` section this repository adds below) is self-contained: a repo follows only the section(s) for the languages it ships and ignores the rest. A repo keeps the whole file rather than trimming it. An unused-language section costs nothing, the same whole-file model as [`.editorconfig`][root], whose inert `[*.cs]` block a non-.NET repo keeps.

Cross-cutting *process* rules (PR titles, branching, US English, Markdown style, comments philosophy, workflow YAML, PR review etiquette, and the verification discipline that defines the pre-push lint gate) live in [GOVERNANCE.md][governance] and are not repeated here.

## General

These rules apply to every language in the repo.

### Tooling Names and Casing

Use each tool's official casing in task labels, docs, and prose, per the `comment-and-doc-style` Skill at `.agents/skills/comment-and-doc-style/SKILL.md` in the hub (not a repo-relative link, that path is hub-local and not carried into every fleet repo).

### Clean-Compile Verification

Each language defines a **clean-compile** verification: the combination of build, formatter, linter, and code-analysis tools that must report clean before a commit. It is exposed as one or more **named** VS Code tasks (or, where a language ships no tasks, documented commands), and those definitions are the same across the fleet. The concrete names live in each language section below.

- **Run it after every code change, and it is not the whole gate.** The relevant language's clean-compile must pass before you commit. CI runs those same language checks as a backstop **plus everything else its validation workflow runs**, and all of it reports into the one required status, so a green clean-compile does not predict a green CI. That remainder is at least the doc-lint set (markdownlint, cspell, actionlint, `editorconfig-checker`) and whatever spec, config, and script gates the repo carries, so read the workflow for the full list rather than assuming this sentence enumerates it. What has to pass before a push is the repo's **whole** lint gate, per [GOVERNANCE.md "Verification Discipline"][governance-verification-discipline]. Each linter's known-working invocation is in [GOVERNANCE.md "Running the Linters Locally"][governance-running-the-linters-locally].
- **The named task definition is the canonical spec** - its exact command sequence, arguments, and strictness. You may run it through the VS Code task **or** by invoking the equivalent native commands directly, and either is fine **only if the sequence, arguments, and strictness match exactly**. No shortcuts and no more-lenient options (for example, never drop `--verify-no-changes` or loosen a `--severity`).
- **A local commit/pre-commit gate is the repo's choice.** No single hook runner fits every language (a `dotnet`-tool runner like Husky.Net suits .NET but not Python), so none is mandated, but that is **not** a recommendation against commit gates. CI is the authoritative backstop regardless, and a local gate is an additive convenience a repo may wire and keep: Husky.Net (and `dotnet husky run` as a style step) for .NET, `pre-commit` for Python. Keeping a working gate is not drift.

### Analyzer Diagnostics and Suppressions

- **A new port is not a license to silence diagnostics.** Brownfield / just-ported status never justifies relaxing analyzer or linter severities or muting newly surfaced warnings. Fix them. (The only brownfield allowance is the one-time git-signing / line-ending migration described in [GOVERNANCE.md][governance] and [README.md][readme], which has nothing to do with code analysis.)
- **Suppress only genuine false-positives or deliberate, documented exceptions**, always at the **narrowest scope that fits**, in this order of preference:
  1. An **in-code annotation on the specific symbol**, with a justification, in the language's attribute/comment form, never a blanket pragma spanning a region.
  2. The **owning project's local config** when the exception is project-wide for one project (e.g. a test project's own `.editorconfig` / `pyproject.toml`).
  3. The **root / shared config** only when the suppression is genuinely applicable to **every** project in the repo.
- **Never blanket-relax a batch of rules project-wide** to get a port to build. The per-language mechanics (which attribute, which config key) are in each language section.

### Markdown and Spelling

These apply repo-wide, in every directory: Markdown lints clean via `markdownlint-cli2` against the shared config, spelling is US English via CSpell against the shared `cspell.json`, the CI spelling gate covers `README.md` and `HISTORY.md` by fleet default, `HISTORY.md` mirrors the README's opening, and "Markdown" is a proper noun in prose. The full rules are in the `comment-and-doc-style` Skill referenced above.

**This repository widens that spelling gate**, exercising the owner's option to widen rather than diverging from the rule, so the default named above is not what runs here. The enforced file list is `**/README.md`, [`DEVICES.md`][devices], and [`HISTORY.md`][history], carried identically by the CI workflow and the `Lint: Spelling` VS Code task so the two cannot drift. The templates, the easystart project, and its Python subtree each ship a README a reader lands on directly, so all of them must be clean, and `DEVICES.md` is the reader-facing device inventory split out of the root README (see [OPERATIONS.md][operations-documenting-a-device]), so it is gated exactly as it was there. It is deliberately **not** all `**/*.md`: this repository carries many Markdown files full of technical terms, and gating every one of them would mean endlessly padding [`cspell.json`][cspell] just to keep CI green. Broad, live spell-checking across any file is the cspell editor extension's job, so typos still surface to whoever is editing. Markdown *linting* stays repo-wide `**/*.md`, since it does not choke on technical terms. Where the carried fleet default above and the CI workflow disagree, the workflow is authoritative for this repository.

## .NET

*This section applies only to the .NET side. A repo with no .NET projects still carries it (the file is carried whole) and ignores it.*

The style guide for any .NET projects in this repo: the zero-warnings build policy and its three-task clean-compile chain, central `Directory.Build.props`/`Directory.Packages.props` configuration, C# language and naming conventions, XML documentation, analyzer suppression scope, the library-versus-application logging split, async and error-handling patterns, xUnit v3 + AwesomeAssertions testing conventions, and AOT-compatible project configuration.

This is packaged as the `dotnet-codestyle` Skill at `.agents/skills/dotnet-codestyle/SKILL.md` in the hub, not a repo-relative link since that path is hub-local and not carried into every fleet repo. The summary above sketches the scope. Read the skill for the full rules, code examples, and mechanics.

## Python

*This section applies only to the Python side. A repo with no Python projects still carries it (the file is carried whole) and ignores it.*

The style guide for any Python project(s) in this repo: the build-versus-lint-only profile split, the uv/ruff/pyright/mypy/pytest toolchain, `src` layout, formatting and linting, comment and docstring conventions, type hints, naming, imports, patterns to avoid, test conventions, and versioning.

This is packaged as the `python-codestyle` Skill at `.agents/skills/python-codestyle/SKILL.md` in the hub, not a repo-relative link since that path is hub-local and not carried into every fleet repo. The summary above sketches the scope. Read the skill for the full rules and the profile-adaptation guidance.

### This Repository's Python

One Python subtree, [`easystart/python`][easystart-python], the standalone EasyStart BLE monitor. It takes the `lint-only` profile: a single script that declares its own runtime dependency through PEP 723 inline metadata and runs with `uv run easystart_monitor.py`, and a `pyproject.toml` carrying **only** tool config, no `[project]`, no `[build-system]`, and no `uv.lock`, because that metadata would misrepresent it as a shippable package.

- **ruff is the only CI gate**, run as `uvx ruff check .` and `uvx ruff format --check .` from the subtree. A `[tool.pyright]` block in **standard** mode keeps Pylance quiet in the editor. There is no mypy gate: the subtree is one script importing an untyped BLE library, so a second type checker adds nothing over Pylance.
- **The ruff version is pinned**, `uvx ruff@0.15.22`, in the CI step and in the VS Code tasks alike so the two cannot drift. This is a deliberate divergence from the fleet default of running `uvx <tool>@latest` unpinned. The fleet reasons that a manual pin Dependabot does not track goes stale silently, and this repository reasons that an unpinned linter turns an upstream release into a surprise CI failure on an unrelated change. The divergence is raised with the fleet rather than settled locally, so expect this bullet to move once that is decided.
- **There is no pytest suite**, so the coverage expectation is N/A. `.py` files follow this repository's LF line-ending default, per [GOVERNANCE.md "Line Endings"][line-endings].

## Shell

Bash, and only where a program cannot be Python: a bootstrap that installs the interpreter cannot be written in it, and a host tool that must run before a development toolchain exists cannot depend on one. Everything else is Python, with a test under the scripts tree's `tests/` directory. The mandatory `set -Eeuo pipefail` header, the pipefail-versus-early-reader pitfall, self-locating scripts, `shellcheck` cleanliness, and the why-not-what comment rule are packaged as the `shell-codestyle` Skill at `.agents/skills/shell-codestyle/SKILL.md` in the hub, not a repo-relative link since that path is hub-local and not carried into every fleet repo. Read the skill for the full rules.

## C++

The C++ here is a small amount of hand-written code that an ESPHome build compiles: the EasyStart external component and the lambda helpers the templates include. It is never built by this repository, so the scope of these rules is **style only**.

### Formatting Toolchain

[`.clang-format`][clang-format] at the repository root is the single source of truth for C/C++ formatting, shared by three surfaces so they cannot disagree:

- **The editor** - the `xaver.clang-format` extension, set as the C/C++ default formatter in the workspace, formats on save from this file.
- **The CLI** - `clang-format --dry-run --Werror <files>` reproduces the check locally.
- **CI** - the lint job runs the same check, feeding the operational lint gate.

The style derives from ESPHome upstream (LLVM-based, 2-space indent, 120-column limit) so the committed sources format clean and do not churn against upstream conventions. A repository's `.h` is read as C++ by context, which is what ESPHome and Arduino headers are.

Semantic and static analysis is deliberately out of scope. The downstream ESPHome build compiles this code and does the compile-time checking, and it holds the compile database that a `clang-tidy` pass would need. Adding a second, weaker analysis here would duplicate that without the context to be correct.

### Conventions

- **Comments follow the repo-wide [comment rules][governance]** in `GOVERNANCE.md`: structured rather than prose, one sentence per line, no file- or class-header summary blocks.
- **Keep header helpers safe to include more than once.** `templates/Utils.h` is textually included into generated lambdas, so it must not introduce a namespace-scope definition that is neither `inline` nor `constexpr` - that is an ODR violation waiting for a second include. Class-scope static member functions, `static constexpr` data members, and function-local `static` caches are fine and are the pattern already in use (`GetMultiButtonState` builds its table once into a function-local static). Prefer computing into a function-local static over a namespace-scope global.
- **Match ESPHome's own naming** in an external component - `snake_case` members and methods, a trailing underscore on private members - so the component reads like the framework it plugs into.

<!-- Repo -->

[clang-format]: ./.clang-format
[cspell]: ./cspell.json
[devices]: ./DEVICES.md
[easystart-python]: ./easystart/python/
[governance]: ./GOVERNANCE.md
[governance-running-the-linters-locally]: ./GOVERNANCE.md#running-the-linters-locally-known-working-invocations
[governance-verification-discipline]: ./GOVERNANCE.md#verification-discipline
[history]: ./HISTORY.md
[line-endings]: ./GOVERNANCE.md#line-endings
[operations-documenting-a-device]: ./OPERATIONS.md#documenting-a-device
[readme]: ./README.md
[root]: ./.editorconfig
