# BLE reverse-engineering playbook (agent-driven)

A repeatable process for reverse-engineering a Bluetooth LE device's app protocol with a Claude
agent, optimized so the **human does as little as possible** - no typing into phone apps, no
screenshots, no file shuffling. The agent drives every CLI and analysis step; the human only
does the few things that need a physical body or a one-time credential.

This is generalized from the EasyStart project (see `PROTOCOL.md`); the concrete artifacts there
(`python/easystart_monitor.py`, `components/easystart`) are good copy-paste starting points.

## Division of labor

**Agent does (all of it, autonomously via the shell):** driving `adb` to find and pull the APK,
running `apktool`/`jadx`, grepping, decoding byte layouts, writing and iterating the BLE
scripts, decoding captures, and writing the docs and the final firmware/component. `adb`,
`apktool`, `jadx` are just CLI tools - the agent runs them directly.

**Human does (the only real friction):**

1. **Plug the phone into the computer** and enable USB debugging. First connection only: tap
   "Allow USB debugging" (the RSA prompt) on the phone and unlock it - after that one tap `adb`
   works unattended.
2. For the **live BLE** phase: run the one-line `uv run` monitor command the agent gives you and
   **paste the text output** back (the agent can't reach the computer's BLE radio itself).
3. Physical actions: be in BLE range, and trigger the device (power on, cycle a load, press a
   button) so there's live traffic; optionally read a value off the vendor app once to
   ground-truth.

Everything else - extracting the APK, decompiling, analysis - is the agent's, no screenshots or
manual dumps needed. Guiding rule: **prefer tools that emit copy-pasteable text on the computer
over any phone app.** Use phone apps only for a one-time GATT eyeball, never for data capture.

## Phase 1 - Static analysis (agent drives everything; human only plugs in the phone)

Once the phone is plugged in and authorized (see human step 1), the agent runs all of this
itself via the shell. Pull the APK with the `tools/pull-apk.sh` helper - it resolves the
package, reads the version, and writes a self-describing `<package>-<versionName>-<versionCode>.apk`
(and handles split APKs), so you never juggle a generic `base.apk`:

```shell
adb devices                                          # confirm phone shows "device"
bash tools/pull-apk.sh <keyword>                     # -> <package>-<versionName>-<versionCode>.apk
```

For EasyStart this yields e.g. `net.microair.easystart-4.2-19.apk`. Point the decompilers at
that file (substitute the actual name the helper prints - shown here as `$APK`):

```shell
APK=net.microair.easystart-4.2-19.apk                # the file pull-apk.sh just wrote
apktool d "$APK" -o app-apktool                      # smali + resources
jadx "$APK" -d app-jadx                              # readable Java (nicer than smali)
```

Then the agent greps the decompiled source for: service/characteristic **UUIDs**,
`writeCharacteristic` / `setValue` / `onCharacteristicChanged`, and the command/response
strings and byte-offset parsing. This alone usually yields the UUIDs, the command(s), and the
frame layout - before touching any hardware. No screenshots or manual file transfers involved.

<details><summary>What <code>pull-apk.sh</code> does under the hood (manual fallback)</summary>

```shell
adb shell pm list packages | grep -i <keyword>     # find the package name
adb shell pm path <package.name>                   # get APK path(s) - may be split APKs
adb pull <path>/base.apk <package>-<ver>.apk       # pull each path returned, name by version
```

The helper adds the version naming, `package:`-prefix / `\r` stripping, and split-APK handling
described in the gotchas below.
</details>

**Tool sourcing:** look for each tool (PATH -> winget package dirs -> local repo copies); if
missing, self-source the official GitHub release / zip locally - but **don't auto-run
`winget install`** or mutate system packages. Ask the user only if it can't be found or sourced.

**Tooling gotchas (Windows / Git Bash), learned running this e2e:**

- `adb` on PATH (winget `Google.PlatformTools`) works directly.
- `adb shell pm path` / `cmd package path` output has a **`package:` prefix and a Windows `\r`**;
  strip both: `... | tr -d '\r' | sed 's/^package://'`.
- `adb pull` prints its progress to **stderr**.
- `apktool` is **not on PATH** - run `java -jar apktool.jar d ...`.
- `jadx`: winget `Skylot.jadx` installs the **GUI only**; the CLI is in the GitHub zip at
  `jadx-1.5.6/bin/jadx.bat`. `apktool` smali is usually enough; use jadx only for readable Java.
- Split-APK apps return several paths - pull them all (the helper handles this).

## Phase 2 - Live validation from the computer (CLI, text only)

Use the **computer's own Bluetooth as the central** via [`bleak`](https://bleak.readthedocs.io/)
(cross-platform: Windows/macOS/Linux). No phone, no extra hardware. The agent writes a monitor
script; the human runs one command and pastes the output.

```shell
uv run monitor.py --discover             # discover devices (print names + MACs), then exit
uv run monitor.py --name <DeviceName>    # connect, poll, decode in real time
```

Make the script (template: `python/easystart_monitor.py`):

- **`uv`-runnable** with PEP 723 inline deps (`# /// script ... dependencies = ["bleak"] ... ///`)
  so there's no venv setup - just `uv run`.
- Select by **name or service UUID** (macOS hides the MAC behind a CoreBluetooth UUID).
- **Print raw bytes with per-index annotations AND the decoded interpretation**, so the human
  can eyeball which byte is which even if the first decode guess is wrong.
- **Auto-reconnect**, since many devices power their radio only intermittently.

Ground-truth by comparing the decoded values against the vendor app's own on-screen numbers
(the human reads those off once). Exact matches confirm scaling/offsets.

## Phase 3 - Passive sniffing (only if you must RE write/OTA commands)

If you need to see exactly what the app sends (commands you can't infer, OTA, config writes),
passively sniff the real **app <-> device** link. Still CLI/text, not screenshots:

- Hardware: **nRF52840 USB dongle** (~$10, the canonical sniffer target) running Nordic's
  **nRF Sniffer for Bluetooth LE** firmware. (A newer nRF54-series board may not be a supported
  sniffer target yet - check the nRF Sniffer release notes.)
- Capture to a `.pcap`, then pull bytes with `tshark` (Wireshark CLI):

  ```shell
  tshark -r cap.pcapng -Y 'btatt.opcode.method == 0x1b || btatt.opcode.method == 0x52' \
         -T fields -e frame.time_relative -e btatt.handle -e btatt.value
  ```

## Anti-patterns / gotchas (learned the hard way)

- **Don't rely on phone apps for data capture.** nRF Connect *mobile* only shows the *latest*
  notification value (it hid a binary frame behind an ASCII ack in the EasyStart work), and it
  means typing + screenshots. Use it only to eyeball the GATT table once; capture with `bleak`.
- **Android HCI snoop log is useless on stock phones.** Modern Pixel/AOSP runs it in `FILTERED`
  mode (`SnoopLogMode=FILTERED`), which strips ATT payloads - the `bugreport` `btsnooz_hci.log`
  keeps only a few bytes per packet. Full `btsnoop_hci.log` needs root. Skip it; use `bleak`.
- **Don't trust vendor/module UUID conventions** (e.g. "Laird VSP TX/RX") - verify which
  characteristic is write vs notify from the app or a live GATT dump. EasyStart had them
  swapped from the usual convention.
- **Only one central connects at a time** - close the vendor app before running the monitor.
- **Watch framing**: a "response" may be several notifications (e.g. binary frame + an ASCII
  `Success` marker). Print everything; decode the binary, treat text markers as
  completion/status.

## How to direct the agent next time

One opening message is enough to kick off Phase 1 end-to-end:

> "I have `<app>` installed on my Android phone, developer options + USB debugging are on, and
> it's plugged into this computer. Extract the APK, decompile it, and reverse-engineer its
> Bluetooth protocol. Go."

The agent then drives `adb` -> `apktool`/`jadx` -> analysis on its own. From there:

1. (Phase 1 runs autonomously - the human only had to plug in and approve the one-time prompt.)
2. "Write me a `bleak` monitor for it." -> agent produces a `uv run` one-liner.
3. Human runs it near the device, pastes the text. -> agent decodes, iterates, and (optionally)
   ground-truths against the vendor app's on-screen values.
4. "Now write the ESPHome component / integration." -> agent ports it.
