# repo-config

Repository and branch configuration held as committed files, kept out of `.github/` (which holds the GitHub-consumed configuration - workflows, Dependabot). This mirrors the layout the fleet repos use.

- `main.json` plus one `develop` variant - the branch rulesets as the writable API subset (`name`, `target`, `enforcement`, `bypass_actors`, `conditions`, `rules`). The `develop` payload is `develop.json` (`release` repos) or `operational/develop.json` (`operational` repos); this repo is operational, so it carries `operational/develop.json`. These are the canonical expected payloads that the audit (`AUDIT.md`) diffs the live rulesets against.
- `operational/develop.json` - the `develop` ruleset for **operational** repos (registry `workflowModel: operational`): direct signed pushes, no PR gate. Present at the hub and in operational carries only - a carried `release` repo does not have it. See "Rulesets" below.
- `configure.sh` - applies the rulesets to a repository via the GitHub API (create or full-payload update, idempotent). Run `repo-config/configure.sh [owner/repo] [release|operational]`; the model may also be passed as the sole argument (`repo-config/configure.sh operational`). With no registry present it infers the model from which `develop` payload is carried (here, `operational`), and an ambiguous layout (both or neither payload) aborts rather than guesses.

## Rulesets

Two workflow models share `main.json` but differ on `develop` (registry `workflowModel`, default `release`):

- **`release`** (`develop.json`): `develop` requires squash merges with linear history and a PR - the feature-branch pipeline.
- **`operational`** (`operational/develop.json`): `develop` takes **direct signed pushes** - only `deletion`, `non_fast_forward`, and `required_signatures`; no PR, no status-check, no Copilot-on-push. CI runs on the push as advisory feedback. This is for live-service config repos that edit `develop` directly and promote a known-good snapshot to `main` via an occasional PR (see [AGENTS.md "Branching Model"][agents-branching-model]).

`main` (both models) requires merge-commit merges (no linear-history rule), signed commits, a passing `Check pull request workflow status job`, resolved review threads, and Copilot review, and blocks force-pushes and deletion - so a `develop -> main` promotion is always gated even when `develop` takes direct commits. Every ruleset intentionally leaves "Require branches to be up to date before merging" **off** - see [AGENTS.md "Branching Model"][agents-branching-model].

**Configure by importing these JSON files, never by hand-building the rules** (hand reconstruction has gone wrong on past setups). The result must be **exactly two rulesets named `develop` and `main`** - the names are load-bearing (`AGENTS.md` and the workflows reference them); only the `develop` *content* varies by model. First remove all legacy classic branch-protection rules and any stray rulesets, then run `configure.sh` (which picks the `develop` payload from the repo's `workflowModel`), or `gh api -X POST repos/<owner>/<repo>/rulesets --input repo-config/<name>.json` per file (operational repos use `operational/develop.json` for `develop`). `gh ruleset` is read-only; creation goes through `gh api`. The required check binds by name and only turns green after the repo's PR workflow runs once. To edit a ruleset, GET it, change the field, and PUT the whole writable subset back (a partial PUT `422`s).

To change the canonical rulesets, edit the live rulesets (fleet-wide changes happen at the hub), then regenerate the committed files from the current repo:

```sh
repo="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
# Paginate so a name match on a later page is never missed - the same trap configure.sh guards against.
# --paginate with --jq '.[]' emits one JSON object per ruleset across all pages; jq -s re-assembles them
# into the single array the selections below expect.
rulesets=$(gh api --paginate "repos/$repo/rulesets" --jq '.[]' | jq -s '.')
for name in develop main; do
  out="repo-config/$name.json"
  # An operational carry keeps its develop payload at operational/develop.json (develop.json is absent).
  [ "$name" = "develop" ] && [ ! -f "$out" ] && out="repo-config/operational/develop.json"
  # Exactly one ruleset per name: zero or duplicates is declared drift - fail loudly, never regen from a guess.
  count=$(jq --arg n "$name" '[.[] | select(.name==$n)] | length' <<<"$rulesets")
  [ "$count" -eq 1 ] || { echo "expected exactly 1 ruleset named $name, found $count (drift)" >&2; exit 1; }
  id=$(jq --arg n "$name" '.[] | select(.name==$n) | .id' <<<"$rulesets")
  gh api "repos/$repo/rulesets/$id" \
    --jq '{name, target, enforcement, bypass_actors, conditions, rules}' \
    | jq -S --indent 4 '.' > "$out"
done
```

## Secrets

Publish credentials required per mechanism are enumerated in `spec/secrets.json`. A repo needs only the mechanisms its own publish targets use - a source-only repo needs none of the publish credentials below. NuGet and PyPI use keyless OIDC Trusted Publishing (no stored key; the publish job needs `id-token: write`, and PyPI additionally an `environment: pypi` gate). Docker Hub has no OIDC equivalent and uses a stored `DOCKER_HUB_USERNAME` + `DOCKER_HUB_ACCESS_TOKEN` in both the Actions and Dependabot secret stores. Codegen and merge-bot repos add a GitHub App (`CODEGEN_APP_CLIENT_ID` + `CODEGEN_APP_PRIVATE_KEY` in both stores; the app must be installed, not just created). App-token call sites use `client-id`, never the deprecated `app-id`.

## Repo Settings

The fleet-standard general settings live in [`settings.json`][settings-json] and are applied idempotently by `configure.sh` alongside the rulesets (`gh api PATCH /repos/{owner}/{repo}`). The two settings that depend on per-repo state - `has_discussions` (visibility) and `default_branch` (main-must-exist) - are computed by the script, not stored in the file.

- **Default branch `main`** (the script sets it only when a `main` branch exists, never pointing the default at a missing branch).
- **Merge methods**: `Allow merge commits` and `Allow squash merging` on, **rebase off** - each branch ruleset then picks its method (merge on `main`, squash on `develop`).
- **Auto-merge on** (the merge-bot needs it) and **`Always suggest updating pull request branches` on**.
- **`Automatically delete head branches` OFF - deliberately.** With it on, a `develop -> main` promotion (whose PR head is `develop`) would delete `develop`. There is no per-branch exemption, so the repo-wide toggle stays off to protect `develop`. **The CLI has the same trap: never `gh pr merge --delete-branch` a promotion PR whose head is `develop`** - the explicit flag deletes `develop` regardless of this setting (see [AGENTS.md "Branching Model"][agents-branching-model]).
- **Wikis and Projects off. Discussions on public repos only** (off on private). **Sponsorships off** - the button is driven by `.github/FUNDING.yml`, not a REST toggle, and the fleet ships none.
- **Actions / General**: allow GitHub Actions to create and approve pull requests (for the bots).

## Brownfield Migration (Maintainer Only)

`Require signed commits` rejects any pre-existing unsigned commit, so the first `develop -> main` release on a repo with unsigned history is blocked. Re-signing that history is a non-fast-forward that the `Block force pushes` rule rejects, **and the admin bypass does not cover `git push --force`**. Completing it requires temporarily disabling the ruleset and a maintainer force-push. This is a one-time, maintainer-performed migration that deliberately uses the force-push [AGENTS.md "Git and Commit Rules"][agents-git-and-commit-rules] forbids agents from running - **an agent must never execute it; surface it to the maintainer**. Greenfield repos where signing is live before the first commit never hit this.

<!-- Repo -->

[agents-branching-model]: ../AGENTS.md#branching-model
[agents-git-and-commit-rules]: ../AGENTS.md#git-and-commit-rules
[settings-json]: ./settings.json
