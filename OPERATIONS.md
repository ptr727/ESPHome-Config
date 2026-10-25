# ESPHome Operations

How to work in this repository: reaching the ESPHome CLI, validating and flashing a change, the template and vendor-firmware patterns, the tooling hazards, and the traps that have cost time before. [`GOVERNANCE.md`][governance] carries the cross-cutting rules every repository in the fleet shares, and [`AGENTS.md`][agents] is the entry point that maps a task to the section governing it. Read this file before editing any YAML under this tree, and read [Repository Tooling Hazards][repository-tooling-hazards] before driving `gh` or the repo-config script.

[`GOVERNANCE.md`][governance] is carried fleet law and byte-locked, so a durable rule specific to this repository cannot live there. It goes in whichever local doc owns the subject: ESPHome operations and repository tooling here, code and documentation style in [`CODESTYLE.md`][codestyle], the CI/CD workflow contract in [`WORKFLOW.md`][workflow].

## Keeping This File Current

An operational discovery is written down as part of the change that surfaced it, never left in a session note or an agent's memory. This is the local routing for the self-improvement rule in [`GOVERNANCE.md`][governance], which owns the principle.

- **A mechanism that stopped working, and whatever replaced it**, goes in the section that owns the subject. Record the replacement and the reason the old route failed, so the next agent does not retry it.
- **A procedure carried out for the first time** gets a section describing how, not that it happened. Write the recipe someone would follow, and name the command or the file rather than narrating the session.
- **A fact established by running something** is recorded with what proved it, since a claim nobody can re-derive gets doubted and re-tested. Prefer the observed output over an assertion.
- **A defect in the carried fleet content** (`AGENTS.md`, `GOVERNANCE.md`, `CODESTYLE.md`, `WORKFLOW.md`, `.github/copilot-instructions.md`, and `AUDIT.md`, plus the hub-hosted `repo-config/` and `spec/secrets.json` this repository reaches rather than carries) is reported upstream rather than patched here, because a local edit registers as drift and fails the audit. Filing that report is a **cross-repository write and needs the maintainer's explicit permission for that specific repository in the current session**, per [Repository Boundaries and Write Safety][governance-write-safety]. Ask, do not assume.
- **Nothing here is a changelog.** State the current mechanism in the present tense, per the documentation rules in `GOVERNANCE.md`. The before-and-after belongs in the commit message.
- **`git blame` does not establish who wrote a line.** Agent commits carry the maintainer's `noreply` identity by policy, so blame attributes agent-authored prose to the maintainer just as it does their own. The `AGENTS.md` carve-out for Unicode the developer deliberately typed cannot be claimed from blame output, and a review flagging non-ASCII is answered by removing it rather than by defending it with an authorship claim the repository cannot support.

## External Package Usage

Templates are consumed two ways. Inside this repository a device config composes them with a local `!include`, which is what [`test/`][test] exercises. Outside it, an adopter composes them as a remote `github://` package, and every template opens with an `External usage:` comment block carrying that form plus whatever it needs from the including config.

The mechanics below were confirmed against ESPHome 2026.7.3 by validating a scratch config that pulled [`templates/common.yaml`][common-template] from `@main`.

- **The package is cloned, not read from the working tree.** `esphome config` logs `INFO Cloning https://github.com/ptr727/ESPHome-Config.git@main` and resolves the files under `packages/<hash>/` in ESPHome's data directory, per [Running the ESPHome CLI][running-the-esphome-cli]. A relative `!include` inside a template therefore resolves against that cache, so sibling includes such as `common.yaml` pulling `wifi.yaml` work unchanged.
- **`!secret` falls back to the consuming config's own directory.** Resolution tries the package's `templates/secrets.yaml` first, whose `<<: !include ../secrets.yaml` fails because the repository root `secrets.yaml` is git-ignored, then tries a `secrets.yaml` beside the including config. An adopter supplies their own under the names in [`secrets._yaml`][secrets-example], and both paths appear in the error when neither exists.
- **`test/` cannot use the remote form**, and the reason is the clone above. A `github://` package fetches the named ref rather than the working tree, so a compile test written that way would build `@main`'s copy of a template and pass while the change under test is broken. It also cannot work for a template that does not exist on the ref yet. Local `!include` is the only form that gates a diff.

Some templates deviate from the plain shorthand, and each says so in its own block:

- [`easystart.yaml`][easystart-template] is parameterized, so it takes the `url` / `ref` / `files` form with `vars` rather than the one-line shorthand.
- The overlays are composed on their board template as a second package entry. The `esp32-s3-wroom-*` board definitions compose on [`esp32-s3-devkitc.yaml`][devkitc-template], and [`heltec-l76k-gnss.yaml`][heltec-gnss-template], [`waveshare-esp32-s3-eth-camera.yaml`][waveshare-camera-template] and [`m5stack-cores3-camera.yaml`][m5stack-cores3-camera-template] on their own boards.
- [`templates/secrets.yaml`][secrets-template] is repository-internal plumbing and is not externally usable, since it re-exports a path that exists only in this tree.

Every substitution a template defines or needs is declared in that template's own header. A template composing others also exposes their knobs, so a consumer reads the composed set rather than one file, and [`common.yaml`][common-template] is the usual composer. [`README.md`][readme] catalogs knobs for an adopter choosing a template, and where it names one, the header is what it has to agree with.

- **`Required substitutions:` lists what the template interpolates but does not define**, including what a template it includes locally needs. A name that nothing in the template or its includes reads is a stale claim rather than a contract.
- **`Optional substitutions:` lists what the template defines with a default and a consumer may override**, each with its default and what moving it does. A knob defined here and documented in a consuming template instead is documented where nobody overriding it will look.
- **A substitution that is machinery stays out of both lists and says so in the header**, per [Dollar Signs in Config Values][dollar-signs]. A value the template bridges to a vendor package, such as the `name` a vendor entry point reads, is the other common case. Leaving it out entirely is what a later reader has to reverse engineer.

Renaming or moving a template breaks every one of these blocks and the [`README.md`][readme] paths, and nothing in CI notices, because the local test config is renamed alongside it and stays green. Re-check the block whenever a template's filename changes.

## Documenting a Device

This is a public repository whose primary audience is people reusing the templates, and it is also the live config directory of one specific home. Two human-facing docs keep those apart, and a change that adds prose picks between them before it picks a section.

- **[`README.md`][readme] documents the reusable surface**: what each template in [`templates/`][templates] is for, the hardware it targets, its substitutions, its flashing route, and the gotchas that follow the template to whoever adopts it. It is written for a reader who owns none of these devices.
- **[`DEVICES.md`][devices] documents the deployed fleet**: one section per device or device family, naming the template it composes and carrying the siting, status, and maintenance state of the physical unit. A reader who is not the maintainer has no use for it.
- **The test is whether a stranger reusing the template needs it.** Knowledge that generalizes to any instance of the hardware belongs in `README.md`. Anything true only of this installation, such as where a unit is mounted, what signal it sees there, why one is powered off, or which ones await a reflash, belongs in `DEVICES.md`. A device-specific fact does not migrate to `README.md` by being interesting.
- **Agent-facing depth stays here** in [Template Notes][template-notes]. `README.md` and `DEVICES.md` are both written for humans, so a mechanism an agent needs in order to change a config safely is documented in this file and linked from there rather than expanded inline.
- **A root config named `test-<name>.yaml` is bench hardware, not the deployed fleet.** The prefix groups every bench device together when the tree is sorted by name. `.gitignore` excludes `test-*.yaml` at the repository root, so it needs no commit history and never appears in `DEVICES.md`. This is distinct from [`test/`][test], which holds the tracked, CI-compiled example devices that between them compose every template.

## Container and CLI

A copy of this repository is either the `/config` mount of a running ESPHome dashboard or a checkout on a development box. What matters is whether the dashboard runs on this copy. On the dashboard's copy, `docker inspect esphome` shows this directory mounted at `/config`.

- Top-level `*.yaml` files are the per-device configs. [`templates/`][templates] holds the shared device and utility templates they include via `packages:`.
- On the dashboard's copy, the tree is deployed state, and an edit applies at the next install from the dashboard.
- On a development box, an edit reaches the dashboard only once it reaches the dashboard's copy. Validate and compile per [Config and Compile Validation][config-and-compile-validation], on a route from [Running the ESPHome CLI][running-the-esphome-cli].
- Network flashing works from either copy, with the ESPHome CLI's `upload --device <ip>`.
- Serial flashing needs a USB port on the host running the flasher. The dashboard host may have none, so its USB install goes through the browser's Web Serial instead. That needs a Chromium-based browser on a secure page, meaning HTTPS or `localhost`. Otherwise, download the image from the install dialog and flash it with ESPHome Web.
- A development box with USB ports flashes over serial with `esphome run --device <port>`, per [Debugging][debugging], or with `esptool` for a built image. It also serves for debugging.

### Running the ESPHome CLI

The rest of this file writes a command as `esphome <command> <device>.yaml`, run from the root of the copy. Each route below runs that same command. Only how it is invoked and the path differ.

- **The dashboard's container**, on the dashboard's copy only. ESPHome runs in Docker as the container `esphome`, from the [`ptr727/esphome-nonroot`][esphome-nonroot-link] image, with the copy at `/config`. Prefix the command with `docker exec esphome`, and give the path as `/config/<device>.yaml`.
- **A throwaway container**, on any checkout. It runs the same image, with the checkout at `/config` and a kept cache directory at `/cache`. [Compiling the Way CI Does][compiling-the-way-ci-does] has the full invocation, which is also how CI compiles.
- **`uvx`**, on any checkout, with no container at all. `uvx --from esphome==<version> esphome <command> <device>.yaml` fetches that release into uv's cache and runs it. `uvx --from esphome==<version> esptool <command>` runs the `esptool` that release pins. This is the usual route for a board on a development box's USB port, since a container needs the serial device passed through.

A venv holding a pinned `esphome`, per [VSCode Setup][vscode-setup], behaves like the `uvx` route.

**Pin the version before anything ships.** The dashboard's ESPHome builds the deployed firmware, so check a change against that version. Read it with `docker exec esphome esphome version` on the dashboard's host. A throwaway container pins it as the image tag, and `uvx` pins it as `esphome==<version>`. The CI-parity compile in [Compiling the Way CI Does][compiling-the-way-ci-does] runs `latest` on purpose, and is the one exception. An `esphome` already on a host's `PATH` is whatever version was installed last, so never trust it unpinned.

**Every route needs a `secrets.yaml` at the root of the copy.** [Compiling the Way CI Does][compiling-the-way-ci-does] explains why. Its guard block generates one from [`secrets._yaml`][secrets-example]. Set `config_dir` to a checkout's absolute path, and the block runs on its own for either checkout route. The dashboard's copy already holds the real `secrets.yaml`, so it needs no guard.

**ESPHome keeps the state of each config in its data directory.** That is `.esphome/` beside the config by default, which `.gitignore` excludes, or `$ESPHOME_DATA_DIR` when set. It holds the cloned `github://` packages under `packages/` and the fetched external components under `external_components/`. The build tree goes under `build/` there, unless `$ESPHOME_BUILD_PATH` moves it. The image sets the two variables to `/cache/data` and `/cache/build`. In a container route, the paths this file gives under `.esphome/` therefore live under `/cache` instead.

**The toolchain lives outside the copy.** ESPHome installs ESP-IDF in the user's cache directory, `~/.cache/esphome/idf` on Linux, unless `$ESPHOME_ESP_IDF_PREFIX` moves it. Its ccache store sits there too, whenever a `ccache` binary is on `PATH`. On the `uvx` route that is the host user's own cache, several hundred megabytes after a first ESP32 compile. The image installs `ccache` and points `HOME` at `/cache/home`, so a container route keeps both in its kept cache directory. `esphome clean-all` deletes this toolchain cache wherever it lives, the PlatformIO core directory, and the data directory of each config it reaches. Run it only when a rebuild from scratch is the goal.

## Config and Compile Validation

Whenever a device YAML, or a template included by one, changes, run config validation for every affected device. When the change is in a template, validate at least one device that uses it, and prefer all of them when it is not obvious which ones consume it.

Run the commands below on any of the routes in [Running the ESPHome CLI][running-the-esphome-cli].

```shell
esphome config <device>.yaml
```

Look for `INFO Configuration is valid!` at the bottom. An earlier `Failed config` block means the change is broken even when the line count looks right.

`esphome config` checks YAML schema and substitution resolution only. It does **not** catch compile errors. When a change touches lambdas, conditional compilation, external components, or framework and platform versions, also compile:

```shell
esphome compile <device>.yaml
```

A compile costs minutes, so reserve it for changes that can plausibly affect generated code. For pure YAML-shape changes, meaning renaming entities, adjusting intervals, or swapping substitution values that map to enum members, `config` is usually enough, but compile when in doubt.

### Compiling the Way CI Does

A checkout compiles without the dashboard. Mount it at `/config` in a throwaway container and run the CLI there. The container, the mounts, and the two CLI calls match the compile job in [`test-pull-request.yml`][test-workflow]. On the same image tag, a compile that fails here fails there. The `uvx` route compiles the same config without Docker. It runs on the host's Python and libraries rather than the image's, so it is the convenient route rather than the parity one.

```shell
config_dir=<absolute path to a checkout, never the deployed tree>
cache=<absolute path to a cache directory you keep>
mkdir -p "$cache"
if [ ! -f "$config_dir/secrets.yaml" ]; then
  key="$(python3 -c 'import base64, os; print(base64.b64encode(os.urandom(32)).decode())')"
  tmp=""
  if [ -n "$key" ] && grep -q REPLACE_WITH_BASE64_32_BYTE_KEY "$config_dir/secrets._yaml" \
    && tmp="$(mktemp "$config_dir/.secrets.XXXXXX")" \
    && sed "s|REPLACE_WITH_BASE64_32_BYTE_KEY|$key|" "$config_dir/secrets._yaml" > "$tmp" \
    && mv "$tmp" "$config_dir/secrets.yaml"; then
    echo "secrets.yaml generated"
  else
    [ -z "$tmp" ] || rm -f "$tmp"
    echo "secrets.yaml not generated" >&2
  fi
fi
[ -f "$config_dir/secrets.yaml" ] && docker run --rm --user "$(id -u):$(id -g)" \
  --volume "$config_dir":/config --volume "$cache":/cache \
  ptr727/esphome-nonroot:latest \
  bash -c '
    set -Eeuo pipefail
    /entrypoint/cache.sh
    esphome config /config/test/<template>.yaml > /dev/null
    esphome compile /config/test/<template>.yaml
  '
```

- **Both paths are absolute.** Docker reads a relative `--volume` source as a named volume. A relative value therefore mounts an empty volume, and the compile fails on a path the caller can see on disk.
- **Point `config_dir` at a checkout rather than at the deployed tree.** The dashboard's container already serves that tree, so compile it there with `docker exec` rather than in a second container.
- **`latest` gives CI parity, not dashboard parity.** CI pulls `latest` fresh on every run, so run `docker pull ptr727/esphome-nonroot:latest` first for parity. That can be newer than the dashboard's last pull. Before an install, rerun with the image tag set to the dashboard's ESPHome version, per [Running the ESPHome CLI][running-the-esphome-cli]. The image's Docker Hub tag list carries each ESPHome release as a tag, such as `2026.9.1`.
- **Compile a [`test/`][test] example device to gate a template change.** A top-level device config works the same way, but the example device is what CI builds.
- **An example device sets `api_reboot_timeout` and `wifi_reboot_timeout` to `0s`.** A flashed one then keeps running on a bench with no Home Assistant and no network, rather than rebooting every 15 minutes. Every template that sets a reboot timeout reads the matching substitution. A template with no `wifi:` block, such as an ethernet-only board's, ignores the WiFi half. CI's change-detection job fails an example device that leaves either one out.
- **`secrets.yaml` belongs at the repository root**, not beside the config being compiled, because [`templates/secrets.yaml`][secrets-template] re-exports the root file and every template resolves `!secret` through it. Generate one from [`secrets._yaml`][secrets-example], and the guard above keeps a real one from being overwritten.
- **`/entrypoint/cache.sh` runs first**, and it prepares the `/cache` mount the image expects.
- **`/cache` holds the toolchain and the build tree, so keep it between runs.** A fresh directory each time makes every local compile a cold ESP-IDF build of several minutes. It also holds ESPHome's ccache store, `home/.cache/esphome/idf/ccache`, so a kept directory turns most repeat compiles into cache hits. CI uses one regardless, since it discards the runner.
- **The container runs as the invoking user**, so what it writes stays owned by that user. The image points its build tree and its data directory at `/cache`. The only thing it leaves in the checkout is `test/.gitignore`, which is ignored. CI pins uid 1000 and chmods the checkout instead, because its runner owns the files differently.
- **A local compile is not the whole gate.** CI runs source lint too. Its change-detection job also fails when no example device in [`test/`][test] includes a device template. An overlay composes into its board's example device rather than getting one of its own. A new utility include joins that job's exemption list instead.

### Compile Lint

A lambda is C++ that only compiles inside the `main.cpp` ESPHome generates, so its warnings show up in a compile log among hundreds from ESPHome and the framework, where they are easy to miss. The compile lint in [`tools/compile-lint`][compile-lint] reruns the compile of `main.cpp` from the build ESPHome left behind. The rerun is syntax-only, uses the build's own flags plus `-Wdouble-promotion`, and keeps only the diagnostics located in this repository's code. It never builds firmware and never changes what gets flashed.

- **Run it with every compile.** The VS Code task "ESPHome: Compile and Lint" compiles the open file in the dashboard's container, then lints that build. Each finding lands in the Problems pane on its YAML line. On a throwaway container, replace the compile call in [Compiling the Way CI Does][compiling-the-way-ci-does] with `PYTHONPATH=/config/tools/compile-lint/src python3 -m compile_lint --config-root /config --compile /config/test/<template>.yaml`.
- **CI runs it on every compile leg** of [`test-pull-request.yml`][test-workflow]. A finding annotates its YAML line, appears in the step summary, and fails the leg.
- **What counts as this repository's code.** A line of a YAML lambda, a lambda ESPHome inlined as a bare expression, and a C++ file in this tree, including the copy of an external component the build holds. Everything else is set aside, and `--verbose` lists it.
- **ESPHome rewrites a lambda before it emits it.** It resolves substitutions, turns `id(x)` into `x` or `x->value()`, and blanks comments. The lint applies the same rewrites before matching each generated line against its YAML line. That match is how it tells a lambda's code from generated code that ESPHome attributes to the same YAML lines.
- **A `text: format:` argument is set aside.** ESPHome passes it to `str_sprintf`, where a float argument is always promoted to double, and no lambda edit changes that.
- **Fixing `-Wdouble-promotion`.** Write a float literal with an `f` suffix, as in `x / 60.0f`, so the arithmetic stays in the single-precision FPU. A float passed to a printf-style call in this repository's own C++ takes an explicit `static_cast<double>()`.
- **Exit status** is `0` when nothing was found, `1` when a finding landed in this repository's code, and `2` when the lint could not run, such as after a failed compile or on a build with no compile database.

## Flashing and sdkconfig

- **`esphome upload` does not compile.** It flashes the last built binary, so after editing YAML run `esphome compile` first, or `esphome run`, which is compile plus upload plus logs. Skipping the compile flashes a stale binary and shows no change. On a cleaned build tree `upload` fails with `FileNotFoundError` on the firmware file. The file takes the node's `esphome:` `name`: `build/<name>.bin` on the native ESP-IDF toolchain, or `.pioenvs/<name>/firmware.bin` on PlatformIO.
- **An sdkconfig change needs no clean build.** An incremental `esphome compile` picks up any option that maps to an esp-idf sdkconfig entry. That includes `esp32_ble` `max_connections`, which maps to `CONFIG_BTDM_CTRL_BLE_MAX_CONN` and `CONFIG_BT_ACL_CONNECTIONS`, and anything under `esp32: framework: sdkconfig_options:`. ESPHome compares the options against what it last wrote, then reconfigures on the native ESP-IDF toolchain, or cleans the build tree itself on PlatformIO. To check, confirm the built value in the build tree's `sdkconfig.<name>`, or in `build/config/sdkconfig.h`, which is what the code compiles against. By default the tree is `.esphome/build/<name>/` beside the YAML, where `<name>` is the node's `esphome:` `name`.
- **A device answers to its FQDN, not to `<name>.local`.** DHCP hands out a default domain that the local DNS serves, and [`templates/wifi.yaml`][wifi-template] passes it to the `wifi` component as the `wifi_domain` secret, so a WiFi device is `<device_name><wifi_domain>`. Read the current value from `secrets.yaml` rather than assuming, and note that an Ethernet device such as the GL-S10 sets no domain of its own and is reachable only by whatever DHCP registered for it.
- **Flash by IP when the name does not resolve** from wherever the CLI runs, a container included: `esphome upload <device>.yaml --device <ip>`. Stream logs the same way with `esphome logs <device>.yaml --device <ip>`. The API port is 6053 and OTA is 3232. Home Assistant carries each device's current address in its `IP Address` text sensor, which is the quickest way to look one up.
- **OTA authenticates with the API encryption key, so the running firmware must offer encryption.** [`templates/ota.yaml`][ota-template] carries `encryption:` and no password. Firmware built on ESPHome 2026.9.0 or later derives the OTA key from the API key, even while a password is configured. Older firmware accepts only the password, so the uploader refuses to send it the encryption-only image, and the device keeps running its old firmware. Upgrade such a device in two steps. First OTA a build from release `2.2.16`, the last one using the password, made on ESPHome 2026.9.1 or later. Then OTA the current build. Treat a password build made on 2026.9.0 as old firmware too, since it crashes on an encrypted upload in safe mode. Keep `ota_password` in `secrets.yaml` until every device has taken the first step.
- **`max_connections` lives on the `esp32_ble` component**, not `esp32_ble_tracker`. The `esp32_ble_tracker` location is deprecated and falls back to the default without warning. The value is one per `ble_client`, plus 3 more when the device also runs a `bluetooth_proxy`, whose active default claims 3.

## Logs and the API Connection Cap

A device's `api:` accepts only `max_connections` clients, defaulting to **5** on ESP32. Home Assistant and the ESPHome dashboard each hold one, which leaves a few spare.

A logs session that outlives its caller keeps retrying and holds a slot. A handful of these saturate the cap, which shows as `[W][api:247]: Max connections (5), rejecting <ip>` and makes every client, including Home Assistant, flap with `EOF received (SocketClosedAPIError)`. So bound every session with `timeout`, and send the output to a file in the git-ignored `logs/` directory rather than to a pipe:

```shell
mkdir -p logs
timeout 45 esphome logs <device>.yaml --device <ip> > logs/<device>.log 2>&1
```

- **On the `uvx` route, the outer `timeout` is enough.** `timeout 25 uvx --from esphome==2026.9.1 esphome logs ...` exits 124 and leaves no `esphome logs` process behind.
- **In the dashboard's container, the timeout goes inside it.** `timeout 45 docker exec esphome esphome logs ...` kills the `docker exec` client but **not** the `esphome logs` process inside the container. That process is orphaned and holds its slot. `docker exec esphome timeout 45 esphome logs /config/<device>.yaml --device <ip> > logs/<device>.log 2>&1` reaps the session on its own and exits 124.
- **In a throwaway container, the timeout goes inside it too.** `docker run --rm ... ptr727/esphome-nonroot:<version> timeout 45 esphome logs ...` exits 124 and leaves no container. With `timeout` outside `docker run`, the container keeps running after the timeout expires. Find a leftover with `docker ps`, and stop it with `docker stop <container>`.
- **A pipe that closes early on `docker exec` orphans the process the same way.** A trailing `| head -N` on `docker exec` leaves the in-container process running until its own timeout expires. Capture to a file and read the file.

To see a device's boot banner and `dump_config`, attach first and then restart it from Home Assistant's `Restart` button. Early boot output predates the API connection and is only ever on the serial console.

Run at most one short logs session at a time and clean up leftovers. In the dashboard's container, which has no `kill` or `pkill` binary, use the `sh` builtin over `/proc`:

```shell
docker exec esphome sh -c 'self=$$; for d in /proc/[0-9]*; do
  p=${d#/proc/}; [ "$p" = "$self" ] && continue
  c=$(tr "\0" " " <"$d/cmdline" 2>/dev/null)
  case "$c" in *"esphome logs"*) [ "${c#*sh -c}" = "$c" ] && kill -9 "$p" ;; esac
done'
```

**The reaper must exclude itself.** Its own `sh -c` argument contains the string it scans for, so a naive `grep -q "esphome logs"` over every `/proc/*/cmdline` matches the scanning shell. That inflates the session count, which reads as a cap problem that is not there, and it is actively destructive in a keep-the-newest variant: the scanning shell is always the newest process, so "keep the highest PID" keeps the reaper and kills the live capture. Skipping the current PID and any `sh -c` wrapper is what makes the count and the kill correct.

Do not raise `api: max_connections` to paper over leaked sessions. Five is plenty for Home Assistant, the dashboard, and one agent, with spares.

## Bluetooth Proxies and BLE Clients

- **Scan parameters stay at the ESPHome defaults.** `interval` 320ms, `window` 30ms, and `active: true` are what upstream's own proxy configs ship. The [`bluetooth_proxy` docs][bluetooth-proxy-link] name a full duty cycle, `interval` and `window` both 1100ms, as an anti-pattern that adds CPU load and heat for no gain, and on a WiFi-connected board it also fights the shared radio. It competes with the connection events of any `ble_client` on the same device, so the cost lands where it hurts most.
- **Passive scanning is enough to reach a known MAC.** A device whose only BLE job is connecting to `ble_client` targets parses no advertisement payloads, so `active: false` drops the scan-request transmissions with nothing lost.
- **`ble_client` depends on `esp32_ble_tracker`, and needs it scanning.** The tracker is a hard dependency, and a client only connects once a scan discovers its address. Continuous scanning is the sole path back after a disconnect, so `continuous: false` strands a dropped module until something else starts a scan.
- **A `ble_client` automation action registers itself as a BLE node, and most never report `ESTABLISHED`.** `ble_client.disconnect`, `ble_client.connect`, and the other actions in ESPHome's `ble_client/automation.h` call `register_ble_node(this)` from their constructors, and their handlers return early while `num_running_ == 0`. `BLEClientDisconnectAction` never assigns `node_state` at all. Since `BLEClient` releases its cached services only once *every* node reports `ESTABLISHED`, a single such action anywhere in a config suppresses that release for the whole client, so the service memory is never reclaimed. Use a `lambda` calling `id(client)->disconnect()` when the action's own completion semantics are not needed. This also masks the underlying ble_client GATT-cache race, which is why it took a component without any such action to surface it.
- **A flashing status LED on a device with a `ble_client` is usually not a fault.** The `ble_client` RSSI sensor calls `status_set_warning()` on `ESP_GATTC_CLOSE_EVT`, and `status_led` blinks on any component warning. An EasyStart module holds its BLE link only while its compressor runs, so the LED flashes for as long as a compressor is idle, which is most of the time. Judge link quality by the RSSI value and its history, never by the LED.

## Strapping Pin Warnings

A pin ESPHome considers a strapping pin warns at every validation. Where the wiring is fixed by the board and known good, silence it at the pin rather than letting the noise train you to ignore validation output.

- **`ignore_strapping_warning: true` belongs inside the pin schema**, so the shorthand `pin: GPIO15` has to expand to a `pin:` mapping with `number:` first. Placing the key beside `pin:` is accepted by no schema and silences nothing, which is the usual reason it "does not work".
- **A component that takes a bare pin number still accepts the pin mapping.** `ethernet` validates `mdc_pin`, `mdio_pin`, `power_pin`, and `clk.pin` with `pins.internal_gpio_pin_number`, and `esp32_camera` validates `data_pins` and `external_clock.pin` the same way. That validator rejects only `mode` and `inverted`, then runs the full pin schema and returns just the number, so expanding the pin to a `number:` mapping carrying `ignore_strapping_warning: true` validates and silences the warning.
- **A pin owned by an upstream package** warns from that package's own schema, so silencing it means overriding the upstream pin rather than editing this repo's YAML.

## Dollar Signs in Config Values

ESPHome runs its substitution pass over every parsed config value. A `$` before word characters is a substitution reference wherever it sits. A value carrying a literal one resolves as an undefined substitution, an NMEA sentence such as `$PCAS03,...` being the case that surfaced it.

- **It validates, and it warns on every run.** Nothing sets strict mode, so the text survives and the bytes reach the device. `esphome config` prints a warning that the string looks like an expression each time. That is the noise [Strapping Pin Warnings][strapping-pin-warnings] exists to keep out of validation output.
- **Quoting does not help, and there is no escape.** YAML parses first, and the substitution pass runs on the parsed string. Both `'$PCAS03'` and `"\x24PCAS03"` arrive as `$PCAS03`. The substitutions component implements no `$$` form.
- **Route the `$` through a substitution of its own.** A lone `"$"` value is inert, since the reference pattern needs a following name character. The expansion advances its search position past the text it just inserted. The `$` it wrote is never rescanned, so `${prefix}PCAS03,...` emits exactly `$PCAS03,...`. Confirm it by decoding the base64 `!!binary` value `esphome config` dumps for a `uart.write` action.
- **Such a substitution is machinery rather than a knob.** Overriding it corrupts every string built on it, while each action still reports success. Document it as internal, and keep it out of the optional-substitutions list. [`heltec-l76k-gnss.yaml`][heltec-gnss-template] is the worked example.

## Verifying Component Knobs

Some substitutions map to an ESPHome component field with a constrained value set, meaning an enum or an allowed-values list. Before wiring one up, verify the valid values from the component source. Grep the installed package of the **pinned version**, the one that validates and compiles, per [Running the ESPHome CLI][running-the-esphome-cli]. Through `uvx`:

```shell
D=$(uvx --from esphome==<version> python -c "import esphome,os;print(os.path.dirname(esphome.__file__))")
grep -nE "<option>" "$D/components/<component>/__init__.py"
```

In the dashboard's container, run the same two lines inside `docker exec esphome sh -c '...'` with plain `python`. Never grep the working tree of an ESPHome source checkout, which can be **stale** relative to the pinned version. One lagged a `max_connections` relocation. Reading a checkout at the pinned release tag with `git show <version>:<path>` is equivalent to the installed package. The schema with the canonical enum lives in `sensor.py`, `__init__.py`, or another `*.py` under the component directory. Enum membership in the installed ESPHome version is the only authority, so do not rely on memory or external docs alone.

For a concrete failure this prevents: `variant: AHT21` looks like a valid value for the `aht10` platform, but the component's `AHT10_VARIANTS` dict contains only `AHT10` and `AHT20`. `esphome config` catches it, and grepping the component first catches it sooner.

## Vendor Firmware Conversion Pattern

Apollo PLT-1B, Konnected blaQ, and CeilSense all follow one pattern for converting a vendor's cloud and project firmware to a local configuration. To convert a new vendor device:

- **Import** the vendor's assembled *variant entry file* as a `github://...@<ref>` package, then add the house `time.yaml` include, plus `api.yaml`, `ota.yaml`, and `logger.yaml` when the vendor does not already define those.
- **Whole-key `!remove`** each stock provisioning, cloud, and web surface that is its own top-level key: `dashboard_import`, `captive_portal`, `esp32_improv`, `improv_serial`, `web_server`, `update`, `http_request`.
- **Remove by id** with `- id: !remove <id>` when the unwanted thing is one item in a list shared with entities you keep, such as a cloud `select` item, a firmware-update `button`, the glue `script`, or the `http_request` OTA platform. ESPHome's `merge_config` in `esphome/config_helpers.py` matches on the id. A dangling reference left behind fails at `compile` rather than `config`, so compile once after this kind of change.
- **Project identity and Update Manager:** prefer `esphome: project: !remove`, as Apollo and CeilSense do. Fall back to overriding `project_version: "0.0.0"` only when upstream lambdas reference the `ESPHOME_PROJECT_NAME` or `ESPHOME_PROJECT_VERSION` macros, as Konnected's do. Grep the upstream package before removing the block.
- **Read the vendor's value before wiring a substitution into a vendor block.** The including side wins the scalar merge. A template default therefore overrides the vendor's value. This holds even when the template default equals ESPHome's own default. Apollo sets `api: reboot_timeout: 0s` on purpose. A `15min` template default would put every PLT-1B that Prevent Sleep holds awake into a reboot cycle whenever Home Assistant is unreachable. Default the substitution to the vendor's value, as [Apollo PLT-1B][apollo-plt-1b] does, unless the point is to change it.
- **Override local environment:** `wifi: ap: !remove` plus `!secret` ssid, password, and domain, then `api.encryption.key`, and OTA `encryption:` via `- id: !extend <ota_id>`. A bare `encryption:` inherits the API key, and ESPHome rejects a `password` beside it.
- **Keep templates minimal, covering identity, secrets, and cloud-stripping only.** Nuanced per-device tuning such as I2C frequency or a sensor `variant` was tried on the Apollo PLT-1B and made no observable difference. The AHT humidity still tracks ambient and outdoor humidity, and it is not tunable away. Add such knobs only when a concrete problem demands one.

## Template Notes

### Minimum ESPHome Version

[`templates/min-version.yaml`][min-version-template] carries the only `esphome:` `min_version` in the tree, set to the last release the templates were compiled and tested against. Bump that one file when they are re-tested on a newer release, and every template that reaches it follows.

- **Every board template reaches it**, through [`common.yaml`][common-template] or through its own `packages:` entry, so a board template that cannot use `common.yaml` adds `minversion: !include min-version.yaml` itself. One that omits it validates and compiles exactly the same and nothing in CI notices, so check the include when adding a board template.
- **Everything else inherits it.** An overlay, a parameterized package such as [`easystart.yaml`][easystart-template], and every utility include are only ever composed onto a board template, so none of them carries a copy of its own.
- **A duplicate include is harmless.** Packages merge and every path resolves to the same scalar, so a board template composed alongside `common.yaml` needs no deduplication.

### Apollo PLT-1B

[`templates/apollo-plt-1b.yaml`][apollo-template] imports the full upstream `github://ApolloAutomation/PLT-1/Integrations/ESPHome/PLT-1B.yaml@main` package and surgically strips stock provisioning. After any `esphome config` of a device using it, the upstream package is cached in ESPHome's data directory, under `packages/<hash>/Integrations/ESPHome/`. Read those files to answer "where does Apollo set X" questions.

Four substitutions are exposed for per-plant override:

- `sleep_duration_hours` defaults to `12` and is the first-boot value of the Home Assistant "Sleep Duration" number. After first boot Home Assistant owns the value via NVS with `restore_value: true`, so changing the substitution does not move an already-deployed device.
- `prevent_sleep_default` defaults to `ON`, with `OFF` the only other value. It is the first-boot state of the Home Assistant "Prevent Sleep" switch, with the same NVS-wins semantics.
- `api_reboot_timeout` defaults to `0s`, which is Apollo's own value. Raising it puts a unit that Prevent Sleep holds awake into a reboot cycle while Home Assistant is unreachable. A sleeping unit loops only when the timeout is below Apollo's own `run_duration`, 90 seconds in the cached package.
- `wifi_reboot_timeout` defaults to `15min`, ESPHome's own `DEFAULT_REBOOT_TIMEOUT`, since Apollo sets no WiFi reboot timeout of its own.

The NVS-versus-substitution semantics matter for the two first-boot values above. For either to change behavior on a deployed unit, wipe NVS with a USB `esptool erase-flash` plus a reflash. An OTA reflash preserves NVS. The two reboot timeouts are compile-time instead, so they take effect on the next flash.

Do not `!remove` blocks from Apollo's package without checking what depends on the ids inside. Apollo's lambdas reference ids across files, and a missing id surfaces as a compile error rather than a config error.

### GL-S10 Bluetooth Proxy

- **The board has no PSRAM.** GL-iNet's datasheet and the community pages claim 8MB, and the hardware does not have it. Treat the 8MB figure as wrong for this board revision and do not add `psram:` back.
- **The status LED convention is deliberate.** The `status_led` pin is intentionally not inverted, so a lit globe LED means healthy and a flashing one means a warning or error, which is the reverse of what upstream's own `gl-s10.yaml` produces. A sync with upstream must not "fix" it.
- **Its GPIO0 and GPIO5 strapping warnings are silenced at the pin**, since the `ethernet` clock and power wiring is fixed by the board, see [Strapping Pin Warnings][strapping-pin-warnings].

### Waveshare ESP32-S3-ETH

[`templates/waveshare-esp32-s3-eth.yaml`][waveshare-template] is a board template, so a device config composing it supplies its own job, the way [`office-bluetooth-proxy.yaml`][office-bluetooth-proxy] adds `esp32_ble_tracker` and `bluetooth_proxy` on top.

- **It cannot include `common.yaml`.** The `ethernet` component declares `CONFLICTS_WITH = ["wifi"]`, and `common.yaml` carries [`wifi.yaml`][wifi-template], so the template composes the individual includes instead. Anything else added to the tree that pulls in a `wifi:` key breaks it, which is the reason [`rgb-led-status.yaml`][rgb-led-status-template] carries its own status logic rather than the upstream package, see [RGB LED Status][rgb-led-status].
- **The W5500 pins carry no strapping warnings.** None of GPIO9 through GPIO14 is an ESP32-S3 strapping pin, so validation output for this board should be clean and a new warning means something actually changed.
- **The `ethernet` component owns its SPI bus outright.** An SPI based PHY does not go through the `spi` component, so those four pins cannot be shared, and the TF card slot on GPIO4 through GPIO7 is a separate bus.
- **The antenna is a solder change, not a config one.** Moving the resistor from the ceramic antenna to the IPEX Gen 1 connector has no GPIO behind it, so there is no equivalent of the ProS3D's `external_antenna` switch to flip.
- **PSRAM is octal.** The ESP32-S3R8 part carries 8MB in package. Waveshare's own `IO_Test` demo contradicts this by listing GPIO33 through GPIO37 as free GPIO, and those pins are the octal PSRAM bus. Trust the part number and the boot banner over the demo.

### Waveshare ESP32-S3-ETH Camera

[`templates/waveshare-esp32-s3-eth-camera.yaml`][waveshare-camera-template] is an overlay on the board template above, composed as a second `packages:` entry the way the WROOM module templates compose onto [`esp32-s3-devkitc.yaml`][devkitc-template].

- **The power down pin is GPIO8, and Waveshare's pin table omits it.** Without `power_down_pin: GPIO8` the sensor never leaves power down, `esp_camera_init` returns `ESP_ERR_NOT_FOUND`, and `esp32_camera` marks itself failed. This is the first thing to check on any camera failure on this board. The board exposes no camera reset pin.
- **The sensor's register bus is a dedicated `i2c:` list entry**, `id: camera_i2c` on GPIO48 and GPIO47, referenced by `i2c_id`. The `i2c_pins:` shorthand is deprecated and is rejected outright once any `i2c:` block exists anywhere in the merged config, so it is a trap that fires when a device later adds a sensor. It is a list entry rather than the mapping shorthand because `i2c` sets `MULTI_CONF`, and a list merges with a device's own bus where a mapping collides with it.
- **GPIO3, GPIO45, and GPIO46 are strapping pins on the camera bus**, silenced at the pin, see [Strapping Pin Warnings][strapping-pin-warnings].
- **The OV2640 tops out at UXGA.** The larger entries in ESPHome's `FRAME_SIZES` need a larger sensor such as the OV5640, and the widely copied community config for this board sets `QHD`, a size the OV2640 cannot produce. That same config uses `i2c_pins:` and puts a `switch:` on GPIO8 beside `power_down_pin: GPIO8`, which fails the pin reuse check. Do not re-derive from it.
- **Exposure is left at the ESPHome defaults.** The overlay is a board template and exposure is a property of the room, so a dark image is tuned at the device. Community reports for this board blame `agc_gain_ceiling` defaulting to `2X` rather than the auto exposure, and nothing here has measured that, so treat it as a starting point rather than as a finding.
- **Take the protective film off the lens before judging an image.** The bench frame that prompted the exposure note above was dark for that reason and for no other, which is worth eliminating first since every other explanation costs a reflash.

### Heltec WiFi LoRa 32 V4-R8 and the L76K GNSS Module

[`templates/heltec-wifi-lora32-v4-r8.yaml`][heltec-template] is a board template. [`templates/heltec-l76k-gnss.yaml`][heltec-gnss-template] is an overlay for the GNSS module that plugs into its header. It composes as a second `packages:` entry, the way the camera overlay above composes onto its board template.

- **What is confirmed on hardware is USB and OTA flashing, WiFi, the OLED, both rails, the GNSS UART and the battery ADC.** The user button is untested. The radio and front-end pins are documented rather than claimed, so nothing exercises them.
- **The board bus is an `i2c:` list entry, and a mapping there loses the bus in silence.** `merge_config` keeps only the consuming config's value when one side is a mapping and the other a list. A consumer's list entry therefore drops a template's mapping bus, and nothing reports it. Two list entries concatenate instead, which is why [Waveshare ESP32-S3-ETH Camera][waveshare-camera] takes that form. A device on the merged bus then needs an explicit `i2c_id`, and says so with `Too many candidates found`. Every template that declares a bus uses the list form, and each board bus uses the id `board_i2c`.
- **`Vext` gates the I2C bus and its pull-ups, so the rail has to come up before the bus.** The bus sets up at `BUS` priority and the `switch` raising the rail at `HARDWARE`, which is the wrong order. An `on_boot` handler at priority 1100 raises the rail first, through the IDF GPIO API. Without it the bus recovery reads SCL low and errors on every boot.
- **The GNSS UART direction is the trap on this board, and the vendor macro names cause it.** MeshCore calls `Serial1.setPins(PIN_GPS_TX, PIN_GPS_RX)` into a signature that takes rx first. Its `PIN_GPS_RX=38` and `PIN_GPS_TX=39` therefore name the module's pins rather than the MCU's. The MCU side is tx on GPIO38 and rx on GPIO39.
- **ESPHome writes the module nothing, which is what makes the overlay a test.** The `gps` component only reads NMEA, so a silent link is the module's own state. The `$PCAS` buttons are the only writes. They separate a dead link from a module whose saved configuration disabled NMEA output, since a version query answers in both cases.
- **The L76K streams the full NMEA set unprompted, so no PCAS write is needed to make it talk.** It also reports `ANTENNA OPEN` once per second with a passive antenna fitted. That is the active-antenna current detector, not a fault, and satellites appear in GSV while it is asserted.
- **Time sync and a position fix have very different signal requirements.** Decoding the navigation message from one satellite carries date and time, and ESPHome's `gps` time platform needs both before it syncs. A 3D position fix needs four satellites, and a 2D one needs three, with altitude held rather than solved.
- **Rule sky view out before the wiring.** A satellite in GSV is not a decoded one, and only a decoded navigation message carries the date, so an indoor unit can list satellites and still never produce a valid RMC or ZDA or sync its time source. Confirm outdoors before treating a silent time source as a module, antenna, direction, baud or protocol fault.
- **Opening the `USB_SERIAL_JTAG` tty resets the MCU, and the host is what does it.** Linux `cdc_acm` sends CDC `SET_CONTROL_LINE_STATE` on open, which this part wires to reset. Reading the bulk IN endpoint through usbfs sends no such request and does not reset. A tool that opens the tty is therefore a reset rather than a read.
- **A board that looks silent may only be resetting under the tool reading it**, per the bullet above, so rule the reader out before suspecting the hardware. Keep `uart_debug` at `WARN` regardless, since a raw NMEA tap costs console bandwidth for nothing when nobody is reading.
- **The 0db range on an S3 is nearer 950mV than the often quoted 1100mV, which is the classic ESP32's reference.** A cell reading 4.18V to 4.19V on a meter gave raw 3657 of 4095 and a calibrated 868mV at the pin. Treat 950mV as the working figure and 1100mV as wrong for this part by roughly 15%.
- **That residual cannot yet be split between the reference and the divider, so neither number is settled.** Back-solving full scale from the raw count and the meter gives 955mV to 958mV only if the divider is exactly the nominal 4.9. Attribute the same residual to the resistors instead and the effective ratio is about 4.82 and full scale about 972mV. One measurement cannot distinguish the two, and the template's `attenuation: 0db` headroom argument rests on whichever it is.
- **Separate them with a raw sensor beside the calibrated one on the same pin.** Both need `allow_other_uses: true`, or two `adc` platforms on one pin fail with `Pin 1 is used in multiple places`. Until that runs, the template keeps the nominal 4.9 ratio.
- **The 15% figure applies to a raw count read against the hardware scale.** A framework that normalizes a calibrated reading onto a fixed 1100mV scale is a separate case, and its constant is correct there. Check which scale a count is on before applying either number.
- **The status LED is dark when healthy, deliberately.** ESPHome drives the pin low when healthy, which lights an active low LED. This board's LED is active high and bright white on a unit that runs from a cell. It blinks through a PWM output capped at `status_led_brightness`, 50% by default, since full drive glares.
- **The SX1262 cannot be driven through ESPHome on this board.** The `sx126x` component reaches an RF switch only through the radio's own DIO2. The KCT8103L front-end is wired to three ESP32 pins instead, one selecting the transmit or receive path per packet. Those pins are documented and left unclaimed.
- **A bench unit needs both reboot timeouts disabled**, as every example device does per [Compiling the Way CI Does][compiling-the-way-ci-does]. On this board a unit on a desk with no Home Assistant otherwise restarts part way through a cold GNSS acquisition.

### M5Stack CoreS3

[`templates/m5stack-cores3.yaml`][m5stack-cores3-template] is a board template. [`templates/m5stack-cores3-camera.yaml`][m5stack-cores3-camera-template] is an overlay for its camera, composed as a second `packages:` entry.

- **The display, touch and backlight drivers sit in the board template, unlike the OLED boards.** The LCD reset is AW9523B pin 9, the touch reset is pin 0, and the backlight is the AXP2101's DLDO1 rail. A device writing its own display block would rebuild that plumbing. The display carries no lambda and `update_interval: never`, which is what LVGL needs. A lambda device extends `board_display` with its lambda, an update interval and `auto_clear_enabled: true`.
- **The AXP2101, AW9523B and AW88298 drivers are M5Stack's external components, pinned to a commit.** ESPHome core closed the pull requests for the first two and pointed at M5Stack's repository instead. That repository changes without releases, so moving the ref needs a bench re-test.
- **An AXP2101 rail output does nothing until something turns it on.** The output platform enables a rail only in `write_state`, so a declared rail keeps whatever the previous firmware or the PMU default left. An `on_boot` at priority 800 turns on every rail but the backlight's, which the backlight light turns on at priority 600. M5Stack's own YAML declares the rails without turning them on, which works only because its factory firmware already did.
- **The vendor AXP2101 component enables the PMU watchdog and never feeds it.** Its default mode raises an interrupt that does not reach the ESP32, and a bench unit ran for hours without a PMU reset. Do not switch the watchdog to a reset mode without adding a feed.
- **GPIO35 is both the display DC pin and the microSD MISO.** M5GFX switches the pin's function on every chip select and `mipi_spi` does not, which is one more reason the slot stays unclaimed.
- **The GC0308 has no JPEG encoder.** With the default `pixel_format: JPEG` the driver returns `ESP_ERR_NOT_SUPPORTED` and `esp32_camera` marks itself failed. `RGB565` with a `jpeg_quality` converts in software, which needs PSRAM.
- **VGA with auto exposure returned one byte-identical flat frame on the bench, every time.** QVGA with the manual exposure and gain from M5Stack's Stack-chan firmware returns a real image. Both changed together, so which one mattered is not established.
- **The camera's pixel clock is GPIO45, and GPIO45 picks the flash voltage at every reset.** The PMU keeps the camera powered across an ESP32 reset, so a streaming camera can hold the strap high. The flash then runs from the 1.8V LDO and the bootloader loops on misreads. Every reset taken with the camera streaming outside the shutdown hook looped on the bench, and every cold power on booted. The evidence, in order:
  - The loop printed `rst:0x3 (RTC_SW_SYS_RST),boot:0x3c` and `partition 0 invalid magic number 0x10aa`, where the magic is `0x50aa`.
  - The partition table read back from flash was byte-identical to the built one, so the bootloader misread intact flash.
  - esptool's ESP32-S3 target defines `GPIO_STRAP_VDDSPI_MASK = 1 << 4`, and `0x3c` has bit 4 set, so GPIO45 read high.
  - `espefuse summary` showed `VDD_SPI_FORCE` unburned, so the strap alone decides the flash voltage.
- **A power cycle recovers, and the overlay prevents the orderly cases.** Hold the power button for 6 seconds, since a reset leaves the camera streaming. The overlay's `on_shutdown` holds the camera in reset, and an OTA reboot with the camera streaming came back clean. The reset after an esptool flash bypasses that hook. Turn `Camera Enable` off over the API first, and a USB flash then boots without a power cycle. The switch drives the sensor's reset line rather than its rail, so turning it back on resets the sensor's registers and needs a restart. A crash or a brownout bypasses the shutdown hook as well.
- **Burning `VDD_SPI` to 3.3V removes the hazard, and nothing here does it.** `espefuse set-flash-voltage 3.3V` is permanent, and the flash voltage is inferred from behavior rather than read from a schematic. The template leaves it to the owner.
- **The camera web server asserts on reboot after the camera failed setup.** `esp32_camera_web_server` marks itself failed before it creates its semaphore, and its `on_shutdown` deletes the null semaphore in `vQueueDelete`. It shows as a crash on the reboot after an OTA, and a working camera never reaches it.
- **The microphone and the speaker share one I2S bus, so only one runs at a time.** The example device stops its `sound_level` sensor, waits until the microphone stops capturing, plays the tune, and restarts the sensor when playback finishes. A version without the wait froze the screen on a press, and the version with it has not.
- **The touch mapping matches M5GFX, 0 to 319 and 0 to 239 with no offset.** A raw capture over the API ran from y 0 at the top edge to 239 at the bottom. Fingertip taps read up to about 20 pixels low near the bottom and within 4 pixels near the top. That is finger contact rather than a panel offset, so the template does not correct for it.
- **The FT6336 drops quick taps once it falls into its monitor scan.** It slows its scan a few seconds after the last touch. Waking a dark screen then took several taps, and the touchscreen component logged one of three. ESPHome's `ft63x6` driver sets the active scan rate in register 0x88 and leaves the power mode in register 0x86 at its default. The board template writes 0 to register 0x86 through the touchscreen's own I2C device. It does so in an `on_boot` at priority -100, since the driver's setup resets the controller. A single tap then wakes the screen.
- **The example device swipes between tabs only from the screen edge.** LVGL's tabview swipe is a plain scroll that also starts on the slider and the drawing pad, so the example turns it off. A drag starting within 24 pixels of the left or right edge and moving 60 pixels inward changes tab instead.

### M5Stack Dial

[`templates/m5stack-dial.yaml`][m5stack-dial-template] is a board template, with every part on the StampS3 GPIO pins rather than behind an expander or a PMU.

- **GPIO46 is the power hold, an output.** On battery the front button or the RTC alarm powers the board on, and it stays on only while the firmware drives GPIO46 high. ESPHome's device page configures it as a "Hold Button" input instead, so a board on battery turns off as soon as the button is released. On USB or the DC input the pin does nothing, so the bench unit could not test it.
- **A restart releases the power hold until the switch sets up again.** The reset returns GPIO46 to an input with its pulldown. Whether a board on battery stays powered through an OTA reboot or a restart is untested.
- **GPIO8 resets both the LCD and the WS1850S RFID reader.** The display owns the pin, so the reader takes no `reset_pin`. On the bench the reader set up without an error after the display's reset pulse.
- **The FT3267 touch controller runs on the `ft5x06` driver.** The boot I2C scan lists only 0x28 and 0x51, but the driver then reads vendor ID 0x11 at 0x38, and touch works. Do not chase the missing address.
- **The touch mapping matches the display with no calibration.** Taps on rings 30 pixels in from each edge and at the center landed on them. The reported coordinates sit one pixel below the raw ones.
- **`resolution: 1` gives one encoder step per detent.** M5Stack's example uses 4, which counts four steps per click.
- **The RTC is a BM8563, which the docs also call an RTC8563 and M5Stack's example drives as a PCF8563.** The template uses the `bm8563` platform, as the CoreS3 template does.

### RGB LED Status

[`templates/rgb-led-status.yaml`][rgb-led-status-template] derives from [Flo-R1der's package][flo-r1der-link] but does not import it, because that version binds its state to `wifi:` `on_connect` triggers and so cannot run on an Ethernet board.

- **The status source is polled, deliberately.** ESPHome has a `wifi:` `on_connect` and an `ethernet:` `on_connect` but no network-level trigger, and YAML has no conditionals, so no single event-driven form covers both interfaces. A 1s `interval` edge-detects instead and runs the script only on a change.
- **`network::is_connected()` is the interface-agnostic helper.** It resolves Ethernet, modem, WiFi, and OpenThread behind their own `USE_*` defines, so the C++ already does the conditional compilation that the YAML cannot. Its header is in the generated `src/esphome.h` for both WiFi and Ethernet builds, so a lambda needs no include. Do not "fix" this back to a `wifi:` trigger.
- **The API state is read live, never latched into a global.** `api:` accepts `max_connections` clients, so a flag set by `on_client_connected` and cleared by `on_client_disconnected` goes false the moment any one of them leaves and stays false while Home Assistant is still connected. That is a white LED on a device Home Assistant reports online, and the earlier version of this template had exactly that bug. The `api.connected` condition reads `APIServer::is_connected()`, the live connection count, and upstream fires the disconnect trigger *after* removing the client so the condition sees the true state from inside it. The two triggers stay, but only to re-run the script.
- **Any second client is enough to trip it**, a leaked `esphome logs` session included, so see [Logs and the API Connection Cap][api-connection-cap] for reaping them.
- **It is remotely consumable**, needing only the `rgb_led_pin` substitution, so it must stay free of repo-local `!include` entries.
- **It contributes its own `api:` block** for the client triggers and the `api.connected` condition, which enables the API server rather than requiring one. A config composing this package alone validates with an unencrypted API, so an encryption key comes from `api.yaml` or from the composing config.

### Bootloader Age and USB Flashing

An ESP32 flashed before ESP-IDF 5.2 keeps that bootloader through every OTA, because OTA writes the app partition and never the bootloader. ESPHome checks it at boot with `esp_ota_get_bootloader_description()` and warns when the call fails:

```text
[W][app:190]: Bootloader too old for OTA rollback and SRAM1 as IRAM (+40KB). Flash via USB once to update the bootloader
```

- **Every ESP32 variant can report it**, only the wording differs, and the classic ESP32 adds the SRAM1 clause. It is not an ESP8266 concern.
- **Never enable `sram1_as_iram` before the USB flash lands.** ESPHome's own source notes that combination hard bricks the device, recovering only by USB reflash. Take the USB flash first, then the option.
- **A device confirms itself fixed on the next boot** by dropping the warning. The absence of the warning is the test, not the `safe_mode` line below it.
- **`Bootloader rollback: support unknown` is the normal state after a serial flash**, and is not a fault. `safe_mode.cpp` reports it whenever the running partition is `ESP_OTA_IMG_NEW`, which is what `esptool` leaves behind, and only an OTA moves the partition to `ESP_OTA_IMG_PENDING_VERIFY` and the line to `supported`. A freshly USB-flashed device therefore reads `support unknown` with a current bootloader, which is a different state from the old-bootloader `not supported`.
- Checking one means attaching to its logs and restarting it, since the banner prints once at boot. A deep-sleeping device cannot be checked outside its wake window.

### MAX17048 Fuel Gauge

[`templates/max17048.yaml`][max17048-template] carries the gauge for every board that has one, and the ProS3D and Adafruit Feather templates include it as a package. It needs nothing from the including board but an `i2c` bus. The [Option-Zero][option-zero-link] `max17048` external component it wraps is read-only: it reads VCELL, SOC, and CRATE and writes nothing.

The gauge is a ModelGauge part, so it infers state of charge by fitting cell voltage to a model of lithium cell behavior rather than counting charge. It runs that fit once, at **its own** power-on, and it is powered from VBAT. An ESP32 reboot, an OTA, or a `restart` button therefore never re-fits it, and a cell attached after boot is measured against whatever model the gauge fit beforehand.

- **With no cell attached the SOC and rate readings are meaningless**, and the numbers do not look obviously broken forever. The charger oscillates between charge and terminate with nothing to hold the rail, which shows as a fast-blinking charge LED and a bouncing voltage that can exceed LiPo float. SOC saturates above 100 percent and then decays for hours, passing through entirely plausible values on the way down.
- **The `Battery Gauge Reset` button forces the re-fit** by writing the QuickStart bit `0x4000` to the MODE register `0x06`, reaching the chip through `id(battery_gauge)->write_byte_16(...)` because `MAX17048Component` inherits `i2c::I2CDevice` publicly. A successful press shows as a single-sample discontinuity in SOC plus the rate register collapsing toward zero.
- **Press it with the cell resting.** QuickStart fits from the instantaneous terminal voltage, which charge current elevates above the true open-circuit voltage, so a press taken while charging reads optimistic.
- **A long state string is a float32 artifact, not a missing rounding**, and a `round` filter makes it worse. The gauge reports state of charge in 1/256 steps, so `4.12890625` is exactly `1057/256` and survives the API's 32-bit float intact. Rounding that to `4.13` lands on a value binary32 cannot represent, and Home Assistant's double-precision expansion then prints `4.13000011444092`.
- **`accuracy_decimals` reaches Home Assistant as `suggested_display_precision`** and the frontend honors it, so the dashboard already shows two decimals. It is an entity-registry option rather than a state attribute, so read it with the entity registry and do not conclude from its absence in the state attributes that it was never sent.
- **A template reading the raw state bypasses all of that.** A `Battery low ... (4.12890625%)` notification is a defect in the notifying template, which rounds with a Jinja `| round(2)`, not in the device config.
- **A mains-powered device drops the gauge by removing both ids**, `- id: !remove battery_gauge` under `sensor:` and `- id: !remove battery_gauge_reset` under `button:`. Removing only the sensor fails validation, because the button's lambda still references the gauge id. The `external_components` entry survives either way and instantiates nothing.

### SmartHome CeilSense

[`templates/smarthome-ceilsense.yaml`][ceilsense-template] assembles the device from SmartHomeShop's firmware **sub-packages** `github://smarthomeshop/ceilsense/ceilsense-v1/{base.yaml, packages/ld2412.yaml, packages/scd4x.yaml}@main` rather than the vendor's `ceilsense-complete-wifi-ld2412.yaml` entry point.

That entry point also pulls in `wifi.yaml`, whose `on_boot` calls the `ble.disable` action and brings in the Improv and BLE provisioning stack. Because `on_boot` is an un-id'd list, that single action cannot be `!remove`d, so importing the entry point forces a live BLE stack just to satisfy the action. Importing the sub-packages and supplying our own `wifi:` plus boot phase 1 drops Bluetooth entirely, leaving no `esp32_ble`, no Improv, and no captive portal. `base.yaml` and the two sensor packages contain no BLE references.

From `base.yaml` the template then strips the cloud and project machinery: the `http_request` `update:` firmware-update entity, the cloud and local "Firmware Variant" `select` with its glue `script`, the now-pointless `ble_disable_after_boot` switch, and `web_server`. `project: !remove` is safe here, unlike Konnected blaQ, because nothing in the sub-packages references the `ESPHOME_PROJECT_NAME` or `ESPHOME_PROJECT_VERSION` compile-time macros. The Software Version text sensor uses the `${project_version}` *substitution*, which still resolves after the block is gone.

[`garage-presence-sensor.yaml`][garage-presence-sensor] consumes it. It tracks `@main` on a `0.9.0-beta` upstream, so an upstream id rename surfaces as a `Source for removal not found` error at `esphome config`. Re-check the removed ids when that appears, or pin a `@<sha>`. This trades the vendor's maintained variant entry point for hand-assembling its parts, so when upstream restructures `base.yaml` or the packages, re-diff against the current `ceilsense-complete-wifi-ld2412.yaml` to see what changed.

### LD2412 Siting and Tuning

The CeilSense carries an LD2412 24 GHz radar, and every control it offers is expressed in **gates** rather than meters. Distance resolution sets the gate width, so changing it silently redefines what every other control means.

- **Fourteen gates, always, and resolution picks the width.** `0.2m` reaches 2.8 m, `0.5m` reaches 7.0 m, `0.75m` reaches 10.5 m. Choose the narrowest width that still covers the room. A wider gate buys range the room does not have and spends spatial resolution to get it.
- **Measure the room before touching a threshold.** Measure slant range, sensor face to object, because that is the path the radar reports, and a floor-plan distance is not it. A reported return beyond the largest dimension of the room is not in the room, and no amount of threshold tuning makes it real.
- **Bound the radar to the room with `Maximum Distance Gate`.** It is the cheapest control, it needs no firmware change, and it applies to the moving and still paths alike. Reach past the walls and the sensor reports what is past them, because drywall and glass are both effectively transparent at 24 GHz. A glass garage door does not stop the sightline at the door.
- **Changing `Distance Resolution` invalidates any background correction.** The learn is stored per gate, so re-binning leaves it describing bands that no longer exist. Run `Start Dynamic Background Correction` **after** a resolution change, never before. A stale background shows up as a strong still target at a range where nothing is, and it clears the moment a valid learn replaces it.
- **Dynamic background correction needs a static scene for the whole learn**, which runs 50 to 90 seconds. It subtracts static clutter, so it never cancels a moving target, and a learn taken while something moved is worse than no learn at all. Attach to the logs and confirm no moving-target events fall inside the window rather than assuming the room was still.
- **Separate a nuisance from a real target by energy, not by distance.** A real target inside the room saturates move energy at 100 percent, while a nuisance sits in a narrow band well below it. A per-gate move threshold placed between the two removes the nuisance with margin, where a distance cut would cost real coverage.
- **The vendor package exposes no gate thresholds at all**, so tuning one costs a firmware change. The template carries the vendor entity set, and a device that needs thresholds declares them in its own config.
- **Declare all fourteen gates or none.** `LD2412Component::set_gate_threshold()` writes the whole array and dereferences every entry, and its early-out tests `.empty()` on a `std::array`, which is never true. A partial declaration leaves null entries and crashes the device on the first threshold write.

## Python Workspace

All Python is one uv workspace rooted at the repository root, laid out in `CODESTYLE.md` "This Repository's Python". The hub validator runs the same commands in CI. Run them from the repository root:

```shell
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

The generic linters (editorconfig-checker, actionlint, markdownlint, and cspell) are the fleet set, invoked as documented in `GOVERNANCE.md` "Running the Linters Locally (Known-Working Invocations)", a hub-only section read in a hub checkout rather than carried here. ESPHome config and compile validation is separate, covered above.

## Device Builder Auto-Commits

ESPHome Device Builder's version history feature is **disabled**, and it needs to stay that way.

On the dashboard's copy, this directory is the `/config` mount of the running `esphome` container. Device Builder's version history polls the tree for changes in `controllers/_device_scanner.py`, stat-based on `(inode, dev, mtime, size)` rather than inotify. It commits every changed YAML as `Edit <file>.yaml`, authored `ESPHome Device Builder <device-builder@esphome.io>` and unsigned. It shells out to `git -c user.email=... -c commit.gpgsign=false commit --no-verify`, and a command-line `-c` outranks the host gitconfig, so neither the host signing policy nor a hook can stop it. It hit this repository twice: on 2026-07-14, amended away, and on 2026-07-18, five commits, reset and re-committed as `08678ad`.

- It is turned off via "Save version history" in the Device Builder UI, persisted in `.device-builder-preferences.json` as `version_history_enabled: false`. That store is RAM-canonical with a debounced write plus a shutdown flush, so patch the file only while the container is stopped, otherwise use the `config/set_preferences` API, which applies live.
- Were it ever re-enabled, a clean `git status` would no longer prove nothing was committed. After editing files here, run `git log --format='%h %G? %an <%ae>' origin/develop..HEAD` and confirm every commit is signed with `G` and authored `ptr727@users.noreply.github.com`.
- Never push commits that fail that check, and never attribute them to yourself or to the maintainer. Check `%an` and `%ae` before claiming or denying authorship. Such commits are unpushed, so correcting them locally is not a history rewrite.

## Reverse Engineering and External Tooling

BLE and device reverse-engineering work, the Micro-Air EasyStart soft-starter for one, follows [`easystart/BLE-RE-PLAYBOOK.md`][ble-re-playbook]: the agent drives adb, apktool, and jadx and decodes the protocol, while the human only plugs in the phone and runs the BLE monitor. Project-specific notes stay in the project folder, in [`easystart/PROTOCOL.md`][easystart-protocol].

When a CLI tool is needed, look for it first on `PATH`, then in package-manager directories, then for a local copy already in the repository. When it is missing, self-source the official GitHub release or vendor zip locally. Do not auto-run `winget install` or another system package manager: sourcing a portable zip or jar is fine, mutating installed system packages is not. Ask the maintainer when a tool cannot be found or sourced.

## Framework and Platform Versions

The notes below were confirmed against the ESPHome 2026.9.1 source and a 2026.9.1 ESP-IDF build. The source files are `esphome/components/esp32/__init__.py`, `esphome/core/config.py`, `esphome/core/__init__.py`, and `esphome/__main__.py`, plus each platform's own `__init__.py`.

- **An ESP32 builds with the native `esp-idf` toolchain by default, not with PlatformIO.** ESPHome downloads ESP-IDF itself and builds with CMake and Ninja. The build tree holds a `CMakeLists.txt` and no `platformio.ini`.
- **`esp32:` `toolchain: platformio` selects the PlatformIO route.** `esphome --toolchain platformio` on the command line does the same and overrides the YAML. ESPHome warns that this route is deprecated and scheduled for removal in 2027.2.0.
- **`framework:` `type:` is either `arduino` or `esp-idf`.** Use [`esp-idf`][esp-idf-framework-link] for ESP32 devices.
- **`version` selects the framework release**, ESP-IDF for `esp-idf` and arduino-esp32 for `arduino`. It defaults to `recommended`. The names `recommended`, `latest`, and `dev` come from a table fixed per ESPHome release. So `latest` means the newest version that release knows, not the newest framework. In 2026.9.1 all three resolve to ESP-IDF 5.5.5 and arduino-esp32 3.3.11. An exact version number also works, and ESPHome warns when it differs from the recommended one.
- **`platform_version` does nothing on the native toolchain.** ESPHome drops it without a warning, since it names a PlatformIO platform package. Under `toolchain: platformio` it selects the `pioarduino/platform-espressif32` release. There it needs an exact `version` beside it, since a named one fails validation.
- **`source` overrides where the framework is downloaded from.** On the native toolchain ESPHome keeps it and warns whenever it is set. Under `toolchain: platformio` it needs an exact `version`, as `platform_version` does.
- **Most `esphome:` `platformio_options` are ignored on the native toolchain.** Each ignored key, such as `board_build.flash_mode`, gets a warning naming it. `build_flags` applies with a deprecation warning, pointing to `esphome:` `build_flags` instead. `lib_deps` and `lib_ignore` apply without a warning. `build_unflags` is ignored, with a warning for each flag. `upload_speed` is read at upload time. `board_upload.flash_size` fails validation on either toolchain.
- **A build setting for an ESP32 belongs in an `esp32:` option**, such as `flash_mode`, or in `framework:` `sdkconfig_options:`.
- **ESP8266, RP2040 and RP2350, LibreTiny, and the host platform build only with PlatformIO.** `platformio_options` and the PlatformIO version apply to them. The ESPHome release sets that PlatformIO version, and it cannot be updated independently.
- **nRF52 builds with its own `sdk-nrf` toolchain by default.** Its PlatformIO toolchain is deprecated and scheduled for removal in 2027.2.0, like the ESP32 one.

## Building Against Patched ESPHome Core Components

Testing a candidate fix to an ESPHome core component does not need a custom image, a venv, or a container change. It works the same on every route in [Running the ESPHome CLI][running-the-esphome-cli]. `external_components` shadows a built-in component of the same name, because `loader.install_meta_finder()` inserts its finder at the front of `sys.meta_path`.

- **Confirm the installed sources match the branch you are patching before trusting the result.** Compare `components/<name>/` in the pinned version's installed package, found as in [Verifying Component Knobs][verifying-component-knobs], against the upstream ref. When they are identical, a build on that version is a valid test of that ref.
- **A git source pulls a fork branch**, and needs `components:` listed explicitly because a full fork exceeds the loader's 100-component limit. Use `refresh: 0s` so an amended branch is re-fetched rather than served from `external_components/` in ESPHome's data directory.

  ```yaml
  external_components:
    - source:
        type: git
        url: https://github.com/<owner>/esphome
        ref: <branch>
      components: [ble_client, esp32_ble_client]
      refresh: 0s
  ```

- **A local source is better for iterating**, since it needs no push per attempt. Copy the components out of the installed package into a git-ignored directory inside the copy, and patch them there. Then point `type: local` at the parent directory. A path inside the copy is what a container route can see through its `/config` mount. `.esphome/` works, but `esphome clean-all` can empty it, per [Running the ESPHome CLI][running-the-esphome-cli]. Copy whole component directories: a stray `.cpp` landing beside the wrong headers fails the build with a confusing missing-header error rather than a path error.
- **Add temporary diagnostics to the core component this way too.** An `ESP_LOGW` inside the code under investigation settles a question that reading the source cannot, and the copy is deleted afterwards.
- **Remember that `esphome upload` does not compile.** After a failed compile it happily flashes the previous binary, so a failed build followed by a successful upload means the device is running the *old* firmware. Check the compile result before reading anything into the device's behavior.

## Contributing Upstream to ESPHome

Core-component fixes are developed in a clone of the fork, whose `origin` is [`ptr727/esphome-esphome`][esphome-fork-link] and whose `upstream` is [`esphome/esphome`][esphome-upstream-link]. An upstream pull request is opened from a branch on the fork. `git push origin <branch>` is what updates it, and nothing is ever pushed to [`esphome/esphome`][esphome-upstream-link] directly. Confirm that with `gh pr view <n> --repo esphome/esphome --json headRepositoryOwner` before assuming a push target.

### Staging on the Fork First

There is **one** fork, renamed from `ptr727/esphome`, so the old name still redirects and `gh` resolves it happily. Do not conclude from that there are two forks. It carries two branch families per change:

- **`fix/<topic>`** is the staging branch, with real working history, opened as a self-PR against the fork's own `dev`. This is where the Copilot round happens.
- **`upstream-<topic>`** is the curated branch that is the actual head of the `esphome/esphome` PR, same tree as its `fix/` counterpart with squashed history.

A change is committed to the `fix/*` branch and reviewed there before it touches the `upstream-*` branch. The fork PR is where Copilot comments without an audience, and it is the only place a bot review can be requested at all. Once the change survives that round, cherry-pick it onto `upstream-*` and push. Prefer adding commits on top of `upstream-*` over a force-push while codeowners are mid-review: ESPHome squash-merges anyway, so tidy history buys nothing and a force-push breaks their review anchors. The two branches carry different histories, so verify the trees agree rather than the commits:

```shell
git diff fix/<topic> upstream-<topic> --stat
```

- **Keep the fork's own `dev` current before branching.** A `fix/*` branch cut from `upstream/dev` while the fork's `dev` lags shows every intervening upstream commit in the fork PR, which drowns the real change and makes a bot review worthless. Fast-forward first: `git fetch upstream dev && git checkout dev && git merge --ff-only upstream/dev && git push origin dev`.
- **Moving the base branch does not always re-diff an open PR.** GitHub recomputes the merge base reliably when the *head* is pushed, not when the *base* moves, so a PR can keep showing the stale diff after the fix. `gh api repos/<o>/<r>/compare/<base>...<head>` reports the true `merge_base_commit` and file list. When that disagrees with `gh pr view --json changedFiles`, close and reopen the PR to force the recompute.

### Fork CI Does Not Run the Real Linters

On a fork's pull requests the lint and build jobs report `Run: skipping`, and `label` and `External component comment` fail outright because they need write tokens a fork does not have. Green-ish checks there mean nothing at all. Run the gates locally from the fork clone, in its venv:

```shell
source venv/bin/activate
script/ci-custom.py
script/build_codeowners.py --check
script/build_language_schema.py --check
script/generate-esp32-boards.py --check
script/generate-rp2-boards.py --check
script/ci_check_duplicate_test_ids.py
script/ci_check_test_fixture_list_form.py
script/clang-format --changed -i
script/clang-tidy --all-headers --changed --environment esp32-idf-tidy
script/clang-tidy --all-headers --changed --environment esp32-arduino-tidy
script/test_build_components.py -c <component>,<component> -t esp32-idf
```

- **`clang-format` reports nothing and rewrites in place**, so confirm it produced no diff rather than reading its exit code as a pass.
- **`clang-tidy-nosplit` is the CI job that covers ESP32**, not the obviously named `clang-tidy-single`, which greps for `USE_ARDUINO` and `USE_ESP8266` and matches zero files in an ESP32 change. The `esp32-idf-tidy` invocation above is what that job runs.
- **The first clang-tidy run builds an ESP-IDF compile database**, about four minutes, and needs clang-tidy 22.1.8 on `PATH`. Later runs reuse the cache.
- **`generate-rp2-boards.py --check` fails with a bare `CalledProcessError` when ruff is missing** from the venv, which reads as a real failure and is not. Install it with `uv pip install ruff`, since plain `pip` hits PEP 668 in a venv without pip.
- **A `tests/components/<x>/test.*.yaml` fixture cannot be compiled directly.** It carries no `esphome:` section because the harness injects one, so go through `test_build_components.py`.
- **`clang-format` does not reflow comments**, but the 120-column limit still applies to them. Check a long comment with `awk 'length > 120'` instead of assuming the formatter would have caught it.

### The `gh` CLI Is Too Old for `gh pr edit`

`gh` is 2.46.0 from the Debian package. `gh pr edit` fetches PR metadata including `projectCards`, a Projects-classic field GitHub has retired, and the API now answers that field with an error rather than null, so the command fails before writing anything:

```text
GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience ... (repository.pullRequest.projectCards)
```

This is a client-version problem and nothing else. It is not the repo-scope rule in [`GOVERNANCE.md`][governance] and not a change in the Copilot or agent instructions: writes aimed at the correct repo succeed, and a read-only probe of `projectCards` by itself reproduces the identical error. Edit a PR body through REST instead, always from a file:

```shell
gh api -X PATCH repos/<owner>/<repo>/pulls/<number> -F body=@body.md
```

The same age accounts for `gh pr checks --json` not existing, so poll CI with `gh pr view <n> --json statusCheckRollup` instead. Upgrading `gh` past the Debian package retires both workarounds. Until then, treat any `gh` subcommand failure whose message names a GraphQL field as a version problem to route around, not as a permissions or policy signal, and **verify whether the write landed before retrying it**. In the failures seen so far the PR body was unchanged, so the error came from the lookup that precedes the write, but that is something to confirm each time rather than assume.

### Bot Reviewers

Upstream runs two automated reviewers, and they differ enough to need handling separately.

- **Copilot** (`copilot-pull-request-reviewer`) posts inline threads. **Its low-confidence notes never become threads.** They are folded into a `<details>` block in the review body, so the comments endpoint returns nothing and a review reporting "generated no new comments" can still carry substantive objections. Read the review body itself, via `gh api repos/<o>/<r>/pulls/<n>/reviews`. In one round those suppressed notes were the only findings, and all of them were correct.
- **Filtering REST reviews by the GraphQL login silently returns nothing.** REST reports `copilot-pull-request-reviewer[bot]`, GraphQL reports it without the suffix, so `select(.user.login=="copilot-pull-request-reviewer")` on a REST payload yields an empty list that reads as "no review yet" rather than as a bad filter. Match the API, and cross-check with `gh pr view --json reviews`, which uses the unsuffixed form.
- **Never hand-complete a commit SHA when filtering.** A poll filtered on a full SHA reconstructed from a short one matched nothing and expired silently while the review had in fact landed. Take it from `git rev-parse`, the same rule the [`GOVERNANCE.md`][governance] id policy applies to writes.
- **esphbot** posts a summary comment plus a formal review, quotes replies back point by point, and concedes with evidence when it is wrong. It re-reviews on push by itself, so there is nothing to trigger and nothing to nudge.
- **A review cannot be requested on an upstream PR.** The `requestReviews` mutation answers `FORBIDDEN: ptr727 does not have the correct permissions to execute RequestReviews` on `esphome/esphome`, because an outside contributor cannot assign reviewers. It works on the fork, which is the only place it is needed.
- **Confirm a review covers the current head by commit oid**, never by timestamp, filtering on author and oid together. A thread reply posts as a review authored by the maintainer at the head SHA, which otherwise reads as coverage.

### The Repo's Own AGENTS.md Is the Style Authority

ESPHome carries contributor rules in its own `AGENTS.md`, and they move. Grep it before arguing a style point, in either direction.

- **Config validators need type hints**, `def validate_x(config: ConfigType) -> ConfigType:`, with `ConfigType` imported from `esphome.types`. Older validators in the same file often lack them, and new code is still expected to have them.
- **Prefer an existing validator from `config_validation.py`** over a hand-rolled one, composed in `cv.All(...)`. `cv.has_at_most_one_key` is the named choice for mutually-exclusive keys, but it tests key *presence*, so it does not fit a key carrying a schema default, which is always present after validation. When the shared one genuinely does not fit, say why in a comment at the validator, because a reviewer following the same rule will ask.
- **A PR title must start with a `[tag]` prefix**, the component name or `[core]`, and the pull request template must be filled out without removing sections.

### Negative Validation Belongs in a Component Test

A schema rejection is testable, and `tests/component_tests/<component>/` is where it goes. `tests/component_tests/bk72xx_ble_tracker/test_scan_parameter_validation.py` is the model: accepted cases and rejected cases in separate blocks, rejections via `pytest.raises(cv.Invalid, match=...)`.

- **Drive the full platform `CONFIG_SCHEMA`, not the validator function.** Testing the function alone still passes when someone unwires it from the `cv.All` chain, which is the regression worth catching. An autouse `reset_core` fixture clears entity state between tests, but names must still be unique within a single test.
- **Confirm the test can fail.** Temporarily remove the validator from the chain and check that exactly the rejection tests fail. A test that passes both with and without the code under test is not coverage.
- **The venv ships without the test dependencies.** `uv pip install pytest pytest-asyncio pytest-cov pytest-mock`, and run with `--no-cov` unless the coverage args in `pyproject.toml` are wanted.

### Answering a Review

Disagreement lands well when it carries evidence, and both bots have accepted well-supported pushback. Cite file and line as they read at the PR's base commit, not as they read in the working tree, since a diff shifts them. Quote the source that settles the point, and state plainly what was applied and what was declined. Check a style objection against the tree before accepting it: an ask for `override` beside `final` died against 54 bare `) final {` and zero `override final` in the codebase. Never build a comment body in a shell string, see [Repository Tooling Hazards][repository-tooling-hazards].

## Debugging

The steps below run ESPHome outside the live instance, on a workstation, which is how a device gets flashed over USB and how a config gets debugged without touching the running controller.

### VSCode Setup

- Install VSCode.
- Clone this repository and open the workspace.
- Upload `secrets.yaml`.
- Install the recommended extensions from the workspace.
- Associate YAML files with ESPHome, from the ESPHome extension.
- Select the default Python interpreter and create a virtual environment, via Ctrl-Shift-P then Python.
- Install the dashboard's ESPHome version in the venv terminal: `pip install --upgrade setuptools wheel esphome==<version>`. ESPHome pins its own PlatformIO. The `uvx` route in [Running the ESPHome CLI][running-the-esphome-cli] runs the same commands without a venv.
- Confirm the [ESPHome CLI][esphome-cli-link] is installed: `esphome version`.
- Compile a project: `esphome compile test/esp32-s3-devkitc.yaml`.
- For a dashboard, install [ESPHome Device Builder][device-builder-link] with `pip install esphome-device-builder` and run `esphome-device-builder .` from the root of the checkout. Without the path argument it serves `./configs`. The `esphome` package carries no dashboard, and `esphome dashboard` only prints a pointer to Device Builder.

### Debugging in the DevContainer

- Complete the [VSCode setup][vscode-setup].
- Open the workspace and clone into the devcontainer volume.
- The image entrypoint serves Device Builder on port 6052. The `ESPHome Device Builder` launch config debugs a second instance beside it, on port 6054.
- That instance keeps its lock and cloned packages in `/cache/debug-data`, because Device Builder allows one instance per data directory.
- The two share the build tree and `/config/.device-builder-preferences.json`, so change settings and compile in one UI at a time.
- TODO: serial port forwarding configuration.

### Debugging on Windows

- Install Python from the Microsoft Store.
- Complete the [VSCode setup][vscode-setup].
- Compile a project: `esphome compile test/adafruit-esp32-s3-feather.yaml`.
- Plug in the device, holding Boot and pressing Reset when required.
- List COM ports from PowerShell:
  - Serial ports: `[System.IO.Ports.SerialPort]::getportnames()`
  - Microsoft drivers: `Get-CimInstance -Class Win32_SerialPort | Select-Object Name, Description, DeviceID`
  - Custom drivers: `Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { $_.Name -match '.*\(COM(\d)\)' } Select-Object Caption`
- Upload firmware: `esphome run --device COM4 test/adafruit-esp32-s3-feather.yaml`.
- Stream logs: `esphome logs [--device COM5] test/adafruit-esp32-s3-feather.yaml`.

### Debugging on Windows WSL

- Install Ubuntu or Debian from the Microsoft Store.
- Install [USBIPD-WIN][usbipd-link] from [GitHub Releases][usbipd-releases-link].
- Bind the serial port. Open PowerShell as Admin in Terminal, referred to as Windows, and open Ubuntu in Terminal, referred to as WSL.
  - Windows: `usbipd list`, for example `7-1    303a:1001  USB Serial Device (COM4), USB JTAG/serial debug unit          Not shared`
  - Windows: `usbipd bind --busid 7-1`
  - Windows: `usbipd attach --wsl --busid 7-1`
  - WSL: `sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y`
  - WSL: `sudo apt install python3 python3-venv usbutils -y`
  - WSL: `lsusb`, for example `Bus 001 Device 002: ID 303a:1001 Espressif USB JTAG/serial debug unit`
  - WSL: `dmesg | grep tty`, for example `cdc_acm 1-1:1.0: ttyACM0: USB ACM device`
  - WSL: `ls /dev/tty*`, for example `/dev/ttyACM0`, `/dev/ttyUSB0`
- Grant the account access to the port.
  - The node class follows the socket the cable is in, not the part on the board. A native USB port enumerates as `/dev/ttyACM*` through `cdc_acm`, and a port behind a bridge chip, a CP210x or a CH340, enumerates as `/dev/ttyUSB*`. A board carrying both, the ESP32-S3-DevKitC among them, presents either depending on which socket is used.
  - Both classes are `root:dialout`, and `dialout` is the only grant flashing and logs need.
  - WSL: `sudo usermod -aG dialout $USER`
  - Group membership is fixed at process start. A VS Code Remote WSL server started before the change keeps its old groups, so every terminal it spawns still fails on the port while a fresh WSL tab works. Restart WSL rather than only opening a new terminal.
    - Windows: `wsl --shutdown`
- Install VSCode and the Remote Explorer extension.
- Open a VSCode Remote WSL Ubuntu session.
  - Complete the [VSCode setup][vscode-setup] in the remote WSL session.
  - List ports: `ls /dev/tty*`, and `ls -l /dev/serial/by-id/` for the stable names.
  - Prefer a by-id name, because `ttyACM` and `ttyUSB` numbering depends on attach order once more than one board is present. A CH340 exposes no USB serial number and so gets no by-id entry at all, and `/dev/serial/by-path/` is the fallback for those.
  - Upload firmware: `esphome run --device /dev/serial/by-id/<by-id-name> test/esp32-s3-devkitc.yaml`
- Unbind the serial port.
  - Windows: `usbipd detach --busid 7-1`
  - Windows: `usbipd unbind --all`

### Debugging in PlatformIO

This applies only to a device that builds with PlatformIO. An ESP32 on the default native toolchain has no PlatformIO project to open, per [Framework and Platform Versions][framework-and-platform-versions].

- Complete the [VSCode setup][vscode-setup] and install the PlatformIO extension.
- Compile the project with `esphome compile [project]`.
- Launch the PlatformIO extension and open the project folder, `.esphome/build/<name>/` beside the YAML, where `<name>` is the node's `esphome:` `name`.
- PlatformIO opens a new instance of VSCode for that project.
- Select the default Python interpreter and create a virtual environment, via Ctrl-Shift-P then Python.
- PlatformIO Core installs into the virtual environment and uses that environment's Python.

## Repository Tooling Hazards

Sharp edges in the tooling around this repository, each one learned by tripping over it.

- **Never build a GitHub comment or reply body inside a double-quoted shell string.** Write it to a file and pass `--body-file`, or `-F body=@file` on a REST call. Backticks in a double-quoted string are command substitution, so a body that mentions a path in code formatting **executes that path**. This is not theoretical: a review reply naming the ruleset apply script in code formatting **executed** it, back when this repository carried its own copy, and that script writes by default, so the posted comment came out with its code spans replaced by command output. Escaping each backtick works and is one missed backslash from repeating the incident. The hazard is the shell's, not that script's, so it survives the copy being retired.
- **The ruleset apply script writes unless told otherwise, and it is hub-hosted rather than carried here.** Run it from a hub checkout and name this repository explicitly, since it otherwise targets whichever repository the shell is sitting in. Its default mode PATCHes repository settings, toggles Dependabot features, and PUTs both branch rulesets. Pass its `check` mode for read-only validation, which is what you almost always want. The payloads it compares against are the hub's own committed `repo-config/` files. This repository carries no local copy, per [AUDIT.md "General Settings and Rulesets"][audit-general-settings-and-rulesets].
- **This file uses reference-style links, and it is the one file in this repository that should not.** The fleet rule allows four agent-instruction files to keep inline links, [`AGENTS.md`][agents], [`GOVERNANCE.md`][governance], this one, and `.github/copilot-instructions.md`, on the grounds that they are read one section at a time so a definition at the foot of the file is never reached. The other three take that allowance and this one does not, which is a divergence to close deliberately rather than incidentally. Every other Markdown file in the repository is reference-style by the rule rather than by exception. Definitions live at the bottom of the file, grouped under `<!-- Repo -->` and `<!-- External -->` and alphabetized within each group. A reference name encodes what it points at, so `analog-max17048-link`, never `analog-en-products-link` after a URL path segment. Removing a link also removes its definition, since an orphan fails the lint.
- **Inline HTML is limited to `<details>` and `<summary>`.** Those two are allowed because a collapsible has no markdown equivalent. Every other element still fails `MD033`, and that includes a `<code>` nested inside a `<summary>`, so use a markdown code span there instead.
- **The spell-check gate CI enforces covers `README.md` and `HISTORY.md`, and nothing else.** That is the fleet rule, applied by the hub's reusable `validate-task.yml`, which exposes no input to widen it. The `Lint: Spelling` task covers `**/README.md` plus [`DEVICES.md`][devices] and `HISTORY.md`, so it reads wider than CI does and gates nothing. A typo in a nested README passes CI, and only that task or the cspell editor extension will show it.
- **Never mount the live checkout into a third-party lint container.** `secrets.yaml` holds the live secrets and is git-ignored. [`secrets._yaml`][secrets-example] is the tracked placeholder. Build a temporary snapshot from tracked and intended untracked files, mount that snapshot read-only, and remove it when done. The Git exclusion rules keep `secrets.yaml` out without maintaining a second exclusion list.

  ```shell
  set -Eeuo pipefail
  repo_root="$(git rev-parse --show-toplevel)"
  lint_root="$(mktemp -d -t esphome-lint.XXXXXX)"
  trap 'rm -rf "$lint_root"' EXIT
  git -C "$repo_root" ls-files --cached --others --exclude-standard -z | tar -C "$repo_root" --null -T - -cf - | tar -xf - -C "$lint_root"
  docker run --rm --network=none --user "$(id -u):$(id -g)" -v "$lint_root":/workdir:ro --workdir /workdir <lint-image> <arguments>
  ```

  `--user "$(id -u):$(id -g)"` runs the container as the invoking host user rather than the image's own default, so it reads `$lint_root` through the same owner permission bits `mktemp -d`'s default `0700` already grants, with no `chmod` opening it to any other local account. This assumes a standard rootful Docker daemon, where the container's user namespace is the host's own. Under **rootless** Docker the daemon runs in its own user namespace, so the host UID passed to `--user` maps to an unrelated subordinate UID inside the container rather than to the owner of the bind mount, and the snapshot becomes unreadable instead. On a rootless daemon, `chmod -R o+rX "$lint_root"` after the tar step is the fallback, accepting the wider local-account readability for the run's duration. The trap removes the snapshot on exit either way.

  **This includes the hub's `scripts/docker_lint.py` wrapper, and it cannot currently take this snapshot as its `--root`.** Its own target discovery runs `git -C "$root" ls-files`, and the snapshot above deliberately holds only the `git ls-files` output, not `.git` itself, so `--root "$lint_root"` fails with "not a git repository" before any linter runs. Passing the live checkout instead would defeat the whole point of the snapshot. Until the wrapper accepts a plain snapshot or file manifest, lint this repository with the direct `docker run` invocations above rather than `docker_lint.py`.

- **The installed `gh` is old enough that `gh pr edit` always fails**, on every repository, and the message names a GraphQL field rather than a permission. See [The `gh` CLI Is Too Old for `gh pr edit`][gh-cli-too-old] for the cause and the REST workaround.
- **A compile job that fails in about 18 seconds is a registry timeout, not a template defect.** The compile jobs pull the [`ptr727/esphome-nonroot`][esphome-nonroot-link] image, and a slow Docker Hub kills the job with `registry-1.docker.io ... context deadline exceeded` before any ESPHome work starts. A real esp-idf compile runs for minutes, so the duration tells the two apart at a glance. Re-run the job rather than reading the template for a fault that is not there.
- **Check an esphome.io link by page title, not HTTP status.** The site answers an unknown path with `200` and a `404 - Page Not Found | ESPHome` title, so a status-code sweep reports a dead link as healthy. The current link form carries no `.html` suffix and no trailing slash, the `guides/configuration-types` anchors have moved to the dedicated [`components/substitutions`][substitutions-link] and [`components/packages`][packages-link] pages, and the per-board pages live on [devices.esphome.io][devices-esphome-link]. An anchor is verified by fetching the page and matching the `id` attribute, since a renamed anchor silently lands the reader at the top of the page.

## Things to Avoid

- Do not claim a config change works until `esphome config`, and where appropriate `esphome compile`, returns success.
- Do not invent enum values, component fields, or framework option names. Grep the component source of the pinned version when uncertain.
- Do not `!remove` blocks from a vendor package without checking what depends on the ids inside. A missing id surfaces as a compile error, not a config error.
- Do not raise `api: max_connections` to work around leaked logs sessions.
- Do not run an ESPHome CLI command on an unpinned install, apart from the CI-parity `latest` compile. Pin it to the dashboard's version, which builds what ships, per [Running the ESPHome CLI][running-the-esphome-cli].

<!-- Repo -->

[agents]: ./AGENTS.md
[api-connection-cap]: #logs-and-the-api-connection-cap
[apollo-plt-1b]: #apollo-plt-1b
[apollo-template]: ./templates/apollo-plt-1b.yaml
[audit-general-settings-and-rulesets]: ./AUDIT.md#general-settings-and-rulesets
[ble-re-playbook]: ./easystart/BLE-RE-PLAYBOOK.md
[ceilsense-template]: ./templates/smarthome-ceilsense.yaml
[codestyle]: ./CODESTYLE.md
[common-template]: ./templates/common.yaml
[compile-lint]: ./tools/compile-lint/
[compiling-the-way-ci-does]: #compiling-the-way-ci-does
[config-and-compile-validation]: #config-and-compile-validation
[debugging]: #debugging
[devices]: ./DEVICES.md
[devkitc-template]: ./templates/esp32-s3-devkitc.yaml
[dollar-signs]: #dollar-signs-in-config-values
[easystart-protocol]: ./easystart/PROTOCOL.md
[easystart-template]: ./templates/easystart.yaml
[framework-and-platform-versions]: #framework-and-platform-versions
[garage-presence-sensor]: ./garage-presence-sensor.yaml
[gh-cli-too-old]: #the-gh-cli-is-too-old-for-gh-pr-edit
[governance]: ./GOVERNANCE.md
[governance-write-safety]: ./GOVERNANCE.md#repository-boundaries-and-write-safety
[heltec-gnss-template]: ./templates/heltec-l76k-gnss.yaml
[heltec-template]: ./templates/heltec-wifi-lora32-v4-r8.yaml
[m5stack-cores3-camera-template]: ./templates/m5stack-cores3-camera.yaml
[m5stack-cores3-template]: ./templates/m5stack-cores3.yaml
[m5stack-dial-template]: ./templates/m5stack-dial.yaml
[max17048-template]: ./templates/max17048.yaml
[min-version-template]: ./templates/min-version.yaml
[office-bluetooth-proxy]: ./office-bluetooth-proxy.yaml
[ota-template]: ./templates/ota.yaml
[readme]: ./README.md
[repository-tooling-hazards]: #repository-tooling-hazards
[rgb-led-status]: #rgb-led-status
[rgb-led-status-template]: ./templates/rgb-led-status.yaml
[running-the-esphome-cli]: #running-the-esphome-cli
[secrets-example]: ./secrets._yaml
[secrets-template]: ./templates/secrets.yaml
[strapping-pin-warnings]: #strapping-pin-warnings
[template-notes]: #template-notes
[templates]: ./templates/
[test]: ./test/
[test-workflow]: ./.github/workflows/test-pull-request.yml
[verifying-component-knobs]: #verifying-component-knobs
[vscode-setup]: #vscode-setup
[waveshare-camera]: #waveshare-esp32-s3-eth-camera
[waveshare-camera-template]: ./templates/waveshare-esp32-s3-eth-camera.yaml
[waveshare-template]: ./templates/waveshare-esp32-s3-eth.yaml
[wifi-template]: ./templates/wifi.yaml
[workflow]: ./WORKFLOW.md

<!-- External -->

[bluetooth-proxy-link]: https://esphome.io/components/bluetooth_proxy
[device-builder-link]: https://github.com/esphome/device-builder
[devices-esphome-link]: https://devices.esphome.io
[esp-idf-framework-link]: https://esphome.io/components/esp32#esp-idf-framework
[esphome-cli-link]: https://esphome.io/guides/cli
[esphome-fork-link]: https://github.com/ptr727/esphome-esphome
[esphome-nonroot-link]: https://github.com/ptr727/ESPHome-NonRoot
[esphome-upstream-link]: https://github.com/esphome/esphome
[flo-r1der-link]: https://github.com/Flo-R1der/ESPHome_RGB-Status-LED_Package
[option-zero-link]: https://github.com/Option-Zero/esphome-components
[packages-link]: https://esphome.io/components/packages
[substitutions-link]: https://esphome.io/components/substitutions
[usbipd-link]: https://learn.microsoft.com/en-us/windows/wsl/connect-usb
[usbipd-releases-link]: https://github.com/dorssel/usbipd-win/releases/latest
