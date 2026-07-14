# AGENTS.md

Operating rules for AI coding agents working in this repository. Read this
before editing ESPHome configs.

## Repo at a glance

- ESPHome configs for this household. Top-level `*.yaml` files are per-device
  configs; `templates/*.yaml` are shared device templates included via
  `packages:`.
- ESPHome runs in Docker. Container name: `esphome` (image
  `ptr727/esphome-nonroot:latest`). The host path
  `/data/appdata/esphome/config` is mounted at `/config` inside the container.
- All ESPHome CLI invocations must run **inside the container** and use
  `/config/<file>.yaml` as the path argument.

## Branching Model

This is an **operational** repo (see the fleet
[`workflowModel`](https://github.com/ptr727/ProjectTemplate/blob/main/registry/repos.json)):
configuration is committed **directly to `develop`** with signed commits - there
is no feature branch, because this tracks the live controller state. A
`develop -> main` pull request occasionally promotes a known-good snapshot to
`main`. `develop` takes direct pushes (advisory CI); the promotion PR runs the
enforced lint check. Both branches are protected; never force-push or delete
either - fix mistakes with follow-up commits.

## Git and Commit Rules

- **Signing.** Every commit on both `develop` and `main` must be
  cryptographically signed (SSH or GPG); branch protection rejects unsigned
  commits. If signing is not configured in the environment, do not commit -
  stop at `git add` and tell the developer/maintainer that signing is
  not configured so they can set it up; do not proceed with the commit.
- **Author identity.** Commit as the repository owner's GitHub `noreply`
  identity (the same identity whose key signs) - never a private, personal, or
  invented/bot address. Verify `git config --get user.email` before committing.
- **Default to staging.** Stage changes with `git add` and leave `git commit`
  to the developer, unless the current task explicitly authorizes committing.
- **No history rewrites.** Never force-push or delete `develop` or `main`; fix
  mistakes with follow-up commits.

## Required validation before declaring a change "done"

Whenever a device YAML or a template that's included by a device YAML is
edited, run config validation for every affected device. If the change is in
a template, validate at least one device that uses it (and prefer all of them
if it's not obvious which ones consume it).

```bash
docker exec esphome esphome config /config/<device>.yaml
```

Look for `INFO Configuration is valid!` at the bottom. Any earlier `Failed
config` block means the change is broken even if the line count looks right.

`esphome config` only checks YAML schema + substitution resolution. It does
**not** catch compile errors. If a change touches lambdas, conditional
compilation, external components, or framework/platform versions, also run:

```bash
docker exec esphome esphome compile /config/<device>.yaml
```

Compile is slow (minutes). Reserve it for changes that could plausibly affect
generated code. For pure YAML-shape changes (renaming entities, adjusting
intervals, swapping substitution values that map to enum members) `config` is
usually enough - but if in doubt, compile.

## Verify component knobs before adding substitutions

When wiring up a substitution that maps to an ESPHome component field with a
constrained value set (an enum, an allowed-values list), verify the valid
values from the component source first. ESPHome components live at
`/data/backup/Profiles/PIETER-DESKTOP/piete/OneDrive/Source/ptr727/esphome-esphome/esphome/components/<component>/`
on this machine - `sensor.py` / `__init__.py` / `*.py` contain the schema
with the canonical enum. Do not rely on memory or external docs alone: enum
membership in the user's installed ESPHome version is the only authority.

Example failure to avoid: `variant: AHT21` was suggested as a valid value for
the `aht10` platform. The component's `AHT10_VARIANTS` dict only contains
`AHT10` and `AHT20`. `esphome config` caught it, but the right move would
have been to grep the component first.

## Apollo PLT-1B template

[templates/apollo-plt-1b.yaml](templates/apollo-plt-1b.yaml) imports the full
upstream `github://ApolloAutomation/PLT-1/Integrations/ESPHome/PLT-1B.yaml@main`
package and surgically strips stock-provisioning. The upstream package is
cached at `/data/appdata/esphome/cache/data/packages/8bc80dd7/Integrations/ESPHome/`

- read those files when answering "where does Apollo set X" questions.

Substitutions exposed for per-plant override:

- `sleep_duration_hours` - first-boot value of HA "Sleep Duration" number.
  After first boot, HA owns the value via NVS (`restore_value: true`). Changing
  the substitution does **not** move an already-deployed device.
- `prevent_sleep_default` (`ON` / `OFF`) - first-boot state of the HA "Prevent
  Sleep" switch. Same NVS-wins semantics.
- `aht_variant` (`AHT10` / `AHT20`) - AHT chip init mode. Compile-time, takes
  effect on next flash.

NVS-vs-substitution semantics matter: for any of these knobs to actually
change behavior on a previously-deployed unit, NVS must be wiped (USB
`esptool.py erase_flash` + reflash). OTA reflash preserves NVS.

## SmartHome CeilSense template

[templates/smarthome-ceilsense.yaml](templates/smarthome-ceilsense.yaml)
assembles the device from SmartHomeShop's firmware **sub-packages**
`github://smarthomeshop/ceilsense/ceilsense-v1/{base.yaml, packages/ld2412.yaml,
packages/scd4x.yaml}@main` rather than the vendor's
`ceilsense-complete-wifi-ld2412.yaml` entry point. That entry point also pulls in
`wifi.yaml`, whose `on_boot` calls the `ble.disable` action (and brings in the
Improv/BLE provisioning stack). Because `on_boot` is an un-id'd list, that single
action can't be `!remove`d, so importing the entry point forces you to keep a
BLE stack alive just to satisfy the action. Importing the sub-packages and
supplying our own `wifi:` + boot phase 1 drops Bluetooth entirely (no
`esp32_ble`, no Improv, no captive portal). `base.yaml` and the two sensor
packages contain no BLE references.

From `base.yaml` it then strips the cloud/project machinery: the `http_request`
`update:` firmware-update entity, the cloud/local "Firmware Variant" `select`
and its glue `script`, the `ble_disable_after_boot` switch (now pointless), plus
`web_server`. `project: !remove` is safe here (unlike Konnected blaQ): nothing in
the sub-packages references the `ESPHOME_PROJECT_NAME/VERSION` compile-time
macros - the Software Version text sensor uses the `${project_version}`
*substitution*, which still resolves after the block is gone.

Consumed by [garage-presence-sensor.yaml](garage-presence-sensor.yaml). Tracks
`@main` on a `0.9.0-beta` upstream, so an upstream id rename surfaces as a
"Source for removal not found" error at `esphome config` - re-check the removed
ids if that appears, or pin a `@<sha>`. Note this trades the vendor's maintained
variant entry point for hand-assembling its parts: if upstream restructures
`base.yaml`/the packages, re-diff against the current
`ceilsense-complete-wifi-ld2412.yaml` to see what changed.

## Converting vendor cloud/project firmware to local (reusable pattern)

Pattern shared by Apollo PLT-1B, Konnected blaQ, and CeilSense. To convert a new
vendor device:

- **Import** the vendor's assembled *variant entry file* as a `github://...@<ref>`
  package; add the house `time.yaml` include (and `api.yaml`/`ota.yaml`/
  `logger.yaml` if the vendor doesn't already define those).
- **Whole-key `!remove`** each stock provisioning/cloud/web surface that is its
  own top-level key: `dashboard_import`, `captive_portal`, `esp32_improv`,
  `improv_serial`, `web_server`, `update`, `http_request`.
- **Remove-by-id** (`- id: !remove <id>`) when the unwanted thing is one item in
  a list shared with entities you keep (e.g. a cloud `select` item, a
  firmware-update `button`, the glue `script`, the `http_request` OTA platform).
  ESPHome's `merge_config` (`esphome/config_helpers.py`) matches the id; a
  dangling reference left behind only fails at `compile`, not `config`, so
  compile once after this kind of change.
- **Project identity / Update Manager:** prefer `esphome: project: !remove`
  (Apollo, CeilSense). Only fall back to overriding `project_version: "0.0.0"`
  when upstream lambdas reference the `ESPHOME_PROJECT_NAME/VERSION` macros
  (Konnected) - grep the upstream package before removing the block.
- **Override local env:** `wifi: ap: !remove` + `!secret` ssid/password/domain;
  `api.encryption.key`; OTA password via `- id: !extend <ota_id>`.
- **Keep templates minimal - identity + secrets + cloud-stripping only.** Nuanced
  per-device tuning (I2C frequency, sensor `variant`, etc.) was tried on the
  Apollo PLT-1B and made *no observable difference* (e.g. the SCD41/AHT humidity
  still tracks ambient/outdoor humidity and isn't tunable away). Don't add such
  knobs preemptively; add them only when a concrete problem demands it.

## Writing style (prose, comments, docs, commits)

Write like the developer who owns this repo, not like an AI assistant.

- **No em-dashes.** Use a hyphen with spaces (` - `), a comma, a colon, or a new
  sentence instead. Em-dashes read as AI-generated.
- **ASCII only in text you author.** Don't introduce non-ASCII characters
  (smart quotes, ellipsis glyphs, arrows, en/em-dashes, etc.) when writing prose,
  comments, or markdown. Use plain `"`, `'`, `...`, `->`.
- **Exception: characters that carry real meaning.** A symbol the value depends
  on is fine and should be preserved - e.g. an Ohm sign for resistance, a degree
  sign for temperature, or any Unicode the user deliberately added. Don't strip
  those.
- This applies to anything you generate: code comments, markdown, commit
  messages, PR text. If the user adds a Unicode symbol on purpose, leave it; just
  don't author em-dashes or decorative non-ASCII yourself.

## Things to avoid

- Don't claim a config change is working until `esphome config` (and, where
  appropriate, `esphome compile`) returns success.
- Don't invent enum values, component fields, or framework option names. Grep
  the component source if uncertain.
- Don't `!remove` blocks from Apollo's package without checking what depends
  on the IDs inside - Apollo's lambdas reference IDs across files, and a
  missing ID surfaces as a compile error, not a config error.
