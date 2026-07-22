# EasyStart live BLE monitor

`easystart_monitor.py` connects to the soft-starter over your computer's Bluetooth, polls
`{"Cmd": ReadLive}`, and prints the decoded live frame in real time - for validating the
protocol (see [../PROTOCOL.md](../PROTOCOL.md)) without flashing ESPHome firmware.

## Run with uv (recommended)

The script declares its dependency inline (PEP 723), so [uv](https://docs.astral.sh/uv/)
installs `bleak` and runs it in one step - no venv, no pip:

```shell
uv run easystart_monitor.py
```

Install uv if needed: `winget install astral-sh.uv` (Windows) or
`brew install uv` / `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS).

### Options

```shell
uv run easystart_monitor.py --discover             # discovery: list EasyStart_* units, then exit
uv run easystart_monitor.py --name EasyStart_A1B2  # pick a unit by name (macOS)
uv run easystart_monitor.py --address <mac|uuid>   # pick by MAC (Win) / UUID (macOS)
uv run easystart_monitor.py --interval 0.5         # poll faster
uv run easystart_monitor.py --raw                  # raw bytes only, no decode
```

Start with **`--discover`** to find your own units - it scans for `EasyStart_*` devices and
prints each one's name and MAC/UUID (the script hard-codes none). `EasyStart_A1B2` above is a
made-up placeholder. With two modules, pass `--name` (or `--address`) so you connect to the one
you mean; a bare run connects to the first one seen.

## Usage notes

- The **compressor must be running** - the module powers its BLE radio only while on. The
  script scans until the module appears and reconnects automatically after each cycle.
- **Close the phone app first** - only one BLE central can connect at a time.

Each sample prints the raw bytes, a per-index breakdown (`[4]=137/0x89 ...`), and the decoded
values. Compare the decoded current/state against the official app to confirm the byte
offsets and the /10 scaling.

## macOS notes (MacBook Air)

- First run prompts for Bluetooth permission - grant your terminal app Bluetooth access under
  **System Settings -> Privacy & Security -> Bluetooth**, then restart the terminal.
- macOS hides the hardware MAC; devices are identified by a CoreBluetooth **UUID**. Use the
  default scan (no `--address`); if you pass `--address`, use the UUID the scan prints.

## What to capture for validation

Grab a few samples at steady run, and if convenient one right after a compressor start (the
current changes). Paste the raw hex lines back for confirmation of the decode.

## Without uv

`requirements.txt` is provided for a classic `pip install -r requirements.txt` in a venv if
you prefer, but uv is simpler on Windows.
