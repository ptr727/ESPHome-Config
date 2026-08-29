# AUDIT.md

How this repository audits itself against its committed baseline and reports drift. This is the
repo-scoped adaptation of the fleet-wide AUDIT.md kept at the fleet hub, and the hub's fleet-wide
audit remains authoritative. The ground truth is the hub's own committed `repo-config/` payloads
and `spec/secrets.json` (this repo carries no local copy of either), and the prose authorities are
[`AGENTS.md`][agents], [`GOVERNANCE.md`][governance], [`CODESTYLE.md`][codestyle], and
[`WORKFLOW.md`][workflow].

The audit is read-only: it diffs live state against the committed baseline and reports findings,
and it never applies changes. The verdict vocabulary is [`WORKFLOW.md`][workflow]'s: **operational
/ not operational**, **N/A**, **defect**, and the applicable/absent rule.

## Scope

This is an operational (live-config) repo: `main` and `develop` rulesets, general repository
settings, and secret names. Code-project dimensions (analyzers, publish mechanisms, coverage) are
N/A, see [GOVERNANCE.md "Branching Model"][governance-branching-model] for the model this baseline
encodes.

## General Settings and Rulesets

This repo carries no local `repo-config/` directory: the hub hosts the settings and ruleset
payloads it is checked against, so both are validated from a hub checkout rather than diffed
locally. Run, from a checkout of `ptr727/ProjectTemplate` at `main`:

```sh
repo-config/configure.sh check ptr727/ESPHome-Config operational
```

This asserts the live repository settings against the hub's `settings.json`, and each of the
`main` and `develop` rulesets against the hub's `main.json` and `operational/develop.json`,
exiting non-zero on drift. The result must be exactly two rulesets named `develop` and `main`
(a missing ruleset or a divergent payload is a **defect**, and a duplicate or stray ruleset is a
**drift finding**).

## Secrets

This repo carries no local `spec/secrets.json` either, for the same reason: the required and
forbidden name lists resolve centrally from the registry entry (`publish[]` and `types[]`) rather
than from anything repo-specific, so a per-repo copy could only restate the hub's own computation
or drift from it. This repo declares `requiredSecrets: []` and `publish: [{ "target":
"github-release", "mechanism": "none" }]` in the hub's registry, which resolves to no required
secret beyond the fleet baseline. Confirm it from a hub checkout at `main`:

```sh
python3 spec/audit.py ESPHome-Config
```

## Verdict and Follow-Up

A missing required item or a divergent payload is a **defect** (not operational), and an
equivalent outcome in a non-standard form is a **drift finding**. N/A items are excluded, never
counted as failures. Surface findings as repository issues, and fixes land as direct signed
commits to `develop` per [GOVERNANCE.md "Branching Model"][governance-branching-model]. To
re-apply the whole baseline, run the hub-hosted `configure.sh apply` from a hub checkout, naming
this repository and its model.

<!-- Repo -->

[agents]: ./AGENTS.md
[codestyle]: ./CODESTYLE.md
[governance]: ./GOVERNANCE.md
[governance-branching-model]: ./GOVERNANCE.md#branching-model
[workflow]: ./WORKFLOW.md
