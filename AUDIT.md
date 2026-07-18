# AUDIT.md

How this repository audits itself against its committed baseline and reports drift. This is the repo-scoped adaptation of the fleet-wide AUDIT.md kept at the fleet hub (carried per the [repo-config downstream carry][repo-config-readme]); the hub's fleet-wide audit remains authoritative. The ground truth here is the committed [`repo-config/`][repo-config] payloads and [`spec/secrets.json`][secrets]; the prose authorities are [`AGENTS.md`][agents], [`CODESTYLE.md`][codestyle], and [`WORKFLOW.md`][workflow].

The audit is read-only: it diffs live state against the committed baseline and reports findings; it never applies changes. The verdict vocabulary is [`WORKFLOW.md`][workflow]'s: **operational / not operational**, **N/A**, **defect**, and the applicable/absent rule.

## Scope

This is an operational (live-config) repo: `main` and `develop` rulesets, general repository settings, and secret names. Code-project dimensions (analyzers, publish mechanisms, coverage) are N/A - see [AGENTS.md "Branching Model"][agents-branching-model] for the model this baseline encodes.

## General Settings

Diff the live repository settings against [`repo-config/settings.json`][repo-config-settings]. The two state-dependent settings are not in the file: `has_discussions` follows visibility (public on / private off) and `default_branch` is `main`.

```sh
repo="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
live=$(gh api "repos/$repo" --jq '{has_wiki,has_projects,allow_merge_commit,allow_squash_merge,allow_rebase_merge,allow_auto_merge,allow_update_branch,delete_branch_on_merge}')
diff <(jq -S . repo-config/settings.json) <(jq -S . <<<"$live") \
  && echo "settings: in sync" || echo "settings: DRIFT"
```

## Rulesets

Diff each live ruleset against the committed expected payload with a normalized comparison (sort the order-insensitive `rules[]` and `bypass_actors[]` before diffing so a reordered but equivalent ruleset does not read as drift). This operational carry keeps its `develop` payload at [`repo-config/operational/develop.json`][repo-config-develop].

```sh
repo="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
norm='{name,target,enforcement,bypass_actors,conditions,rules} | .rules|=sort_by(.type) | .bypass_actors|=sort_by(.actor_id)'
# Paginate so later-page rulesets count: --paginate with --jq '.[]' emits one JSON object per ruleset
# across all pages; jq -s re-assembles them into the single array the selections below expect.
rulesets=$(gh api --paginate "repos/$repo/rulesets" --jq '.[]' | jq -s '.')
for b in develop main; do
  file="repo-config/$b.json"
  [ "$b" = "develop" ] && file="repo-config/operational/develop.json"
  # Exactly one ruleset per name: zero or duplicates is itself a finding - report it, never diff a guess.
  count=$(jq --arg n "$b" '[.[] | select(.name==$n)] | length' <<<"$rulesets")
  [ "$count" -eq 1 ] || { echo "$b: expected exactly 1 ruleset, found $count (defect/drift)"; continue; }
  id=$(jq --arg n "$b" '.[] | select(.name==$n) | .id' <<<"$rulesets")
  diff <(jq -S "$norm" "$file") \
       <(gh api "repos/$repo/rulesets/$id" --jq '{name,target,enforcement,bypass_actors,conditions,rules}' | jq -S "$norm") \
    && echo "$b: in sync" || echo "$b: DRIFT"
done
```

The result must be exactly two rulesets named `develop` and `main` - a missing ruleset or a divergent payload is a **defect**; a duplicate or stray ruleset is a **drift finding**.

## Secrets

Confirm each name [`spec/secrets.json`][secrets] requires exists in the stores its mechanism claims - the name lists derive from the spec itself, so this check and the spec cannot drift apart - and no forbidden name is present in any store (names only; values are not readable).

```sh
repo="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
# Name lists derive from spec/secrets.json (baseline plus any mechanisms, per store claim; forbidden names
# checked in every store), so this check and the spec cannot drift apart. --paginate so names beyond the
# first page still count.
for store in actions dependabot; do
  names=$(gh api --paginate "repos/$repo/$store/secrets" --jq '.secrets[].name')
  for s in $(jq -r --arg store "$store" '[.baseline, ((.mechanisms // {}) | .[])] | map(select(.stores | index($store)) | .requires[]) | .[]' spec/secrets.json); do
    grep -qx "$s" <<<"$names" && echo "$store/$s: present" || echo "$store/$s: MISSING (defect)"
  done
  for s in $(jq -r '[.baseline, ((.mechanisms // {}) | .[])] | map(.forbids[]) | .[]' spec/secrets.json); do
    grep -qx "$s" <<<"$names" && echo "$store/$s: forbidden name present (defect)" || true
  done
done
```

## Verdict and Follow-Up

A missing required item or a divergent payload is a **defect** (not operational); an equivalent outcome in a non-standard form is a **drift finding**. N/A items are excluded, never counted as failures. Surface findings as repository issues; fixes land as direct signed commits to `develop` per [AGENTS.md "Branching Model"][agents-branching-model]. To re-apply the whole baseline, run `repo-config/configure.sh` (see [repo-config/README.md][repo-config-readme]).

<!-- Repo -->

[agents]: ./AGENTS.md
[agents-branching-model]: ./AGENTS.md#branching-model
[codestyle]: ./CODESTYLE.md
[repo-config]: ./repo-config/
[repo-config-develop]: ./repo-config/operational/develop.json
[repo-config-readme]: ./repo-config/README.md
[repo-config-settings]: ./repo-config/settings.json
[secrets]: ./spec/secrets.json
[workflow]: ./WORKFLOW.md
