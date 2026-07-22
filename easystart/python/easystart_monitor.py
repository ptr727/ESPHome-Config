#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["bleak>=0.22"]
# ///
"""EasyStart / Micro-Air soft-starter live BLE monitor.

Connects to the module over your computer's Bluetooth, polls {"Cmd": ReadLive}, and prints
the decoded live frame in real time. Doubles as protocol validation before finalizing the
ESPHome component -- it always prints the full raw frame with per-byte offsets so you can
confirm (or correct) the decode against what the official app shows.

Run with uv (auto-installs bleak, no venv needed):
  uv run easystart_monitor.py --discover              # discovery phase: list EasyStart_* units
  uv run easystart_monitor.py                         # scan by service UUID, connect to first
  uv run easystart_monitor.py --name EasyStart_XXXX   # pick a unit by advertised name (macOS)
  uv run easystart_monitor.py --address <uuid-or-mac>  # pick by MAC (Windows) / UUID (macOS)
  uv run easystart_monitor.py --interval 1.0          # poll period seconds (default 1.0)
  uv run easystart_monitor.py --raw                   # only dump raw bytes, skip decode

Discovery: run --discover first to find your own units' names and MAC addresses (this script
hard-codes none). It scans for devices advertising as EasyStart_* (or the Laird VSP service)
and prints each name + address + signal. Then pass one to --name (macOS) or --address (Windows).

Notes:
  - The module powers its BLE radio only while the compressor is running, so the script
    scans/retries until it appears, and resumes automatically after each compressor cycle.
  - Only one BLE central can connect at once: close the phone app before running this.
"""

import argparse
import asyncio
import sys
from datetime import datetime

try:
    # bleak is installed at runtime by uv from the PEP 723 inline metadata, not into the
    # editor's environment, so pyright cannot resolve it standalone.
    from bleak import BleakClient, BleakScanner  # pyright: ignore[reportMissingImports]
except ImportError:
    sys.exit("bleak is required: pip install bleak")

SERVICE_UUID = "d973f2e0-b19e-11e2-9e96-0800200c9a66"
# Confirmed via nRF Connect: e1 = NOTIFY, e2 = WRITE/WRITE-NO-RESPONSE.
NOTIFY_UUID = "d973f2e1-b19e-11e2-9e96-0800200c9a66"  # module -> host (notify)
WRITE_UUID = "d973f2e2-b19e-11e2-9e96-0800200c9a66"  # host -> module (commands)

CMD_READ_LIVE = b'{"Cmd": ReadLive}'

# System-state / fault code table (frame byte [2]); see PROTOCOL.md.
STATE_TEXT = [
    "Normal",  # 0
    "Unexpctd Curr Flt",  # 1
    "Short Cycle Delay",  # 2
    "Pwr Intrrptn Fault",  # 3
    "Stall Fault",  # 4
    "Stuck SR Fault",  # 5
    "Open Ovrld Fault",  # 6
    "Overcurrent Fault",  # 7
    "Bad Wiring Fault",  # 8
    "Wrong Voltage Flt",  # 9
]


def le16(b, i):
    return b[i] | (b[i + 1] << 8)


def le32(b, i):
    return b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24)


def decode_frame(b: bytes) -> str:
    """Decode the 18-byte live frame. Formulas validated against the app decompile and live
    hardware (see PROTOCOL.md section 4)."""
    if len(b) < 18:
        return f"(short frame, {len(b)} bytes)"
    state = b[2]
    state_str = STATE_TEXT[state] if state <= 9 else f"Not Defined({state})"
    learned = b[3]
    current = le16(b, 4) / 10.0
    period = le16(b, 6)
    freq = 500000.0 / period if period else 0.0
    peak = le16(b, 8) / 10.0
    scpt = le16(b, 10)
    faults = le16(b, 12)
    starts = le32(b, 14)
    return (
        f"state={state_str:18s} current={current:5.1f}A freq={freq:5.2f}Hz "
        f"peak={peak:5.1f}A learned={learned:3d} scpt={scpt:5d} "
        f"faults={faults:5d} starts={starts:6d}"
    )


def dump_raw(b: bytes) -> str:
    return " ".join(f"{x:02x}" for x in b)


def dump_indexed(b: bytes) -> str:
    return "  ".join(f"[{i:2d}]={x:3d}/0x{x:02x}" for i, x in enumerate(b))


class Monitor:
    def __init__(self, args):
        self.args = args
        self.last = None

    def on_notify(self, _char, data: bytearray):
        b = bytes(data)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # The module replies with two notifications per ReadLive: the binary live frame and an
        # ASCII status marker like {"Sts": Success}. Show both; only decode the binary one.
        if b[:1] == b"{" or all(32 <= x < 127 for x in b):
            print(f"\n[{ts}] TEXT ({len(b)}): {b.decode('ascii', 'replace')}")
            return
        marker = "" if b == self.last else "  <-- changed"
        self.last = b
        print(f"\n[{ts}] FRAME raw({len(b)}): {dump_raw(b)}{marker}")
        print(f"          {dump_indexed(b)}")
        if not self.args.raw:
            print(f"          {decode_frame(b)}")

    def _matches(self, dev, ad):
        has_service = SERVICE_UUID.lower() in [u.lower() for u in (ad.service_uuids or [])]
        name = ad.local_name or dev.name or ""
        if self.args.name:
            return self.args.name.lower() in name.lower()
        # No name filter: match by service UUID, or by an "EasyStart" name as a fallback
        # (some adapters don't surface service UUIDs in the advertisement).
        return has_service or "easystart" in name.lower()

    async def discover(self):
        """Device-discovery phase: scan for EasyStart_* units (or the Laird VSP service) and
        print each one's advertised name, MAC/UUID, and signal strength. Nothing is hard-coded;
        this is how you find your own units before connecting."""
        print("scanning 8s for EasyStart_* units (compressors must be running)...\n")
        found = {}

        def cb(dev, ad):
            name = ad.local_name or dev.name or ""
            if name.lower().startswith("easystart") or SERVICE_UUID.lower() in [
                u.lower() for u in (ad.service_uuids or [])
            ]:
                found[dev.address] = (name or "(no name)", ad.rssi)

        scanner = BleakScanner(detection_callback=cb)
        await scanner.start()
        await asyncio.sleep(8.0)
        await scanner.stop()
        if not found:
            print(
                "no EasyStart units found (are the compressors running? is the phone app closed?)"
            )
            return
        for addr, (name, rssi) in sorted(found.items(), key=lambda x: -(x[1][1] or -999)):
            print(f"  {name:20s} {addr}  {rssi} dBm")
        print("\nconnect with:  --name <name>   (macOS)   or   --address <mac>   (Windows/ESP)")

    async def find_address(self):
        if self.args.address:
            return self.args.address
        target = self.args.name or f"service {SERVICE_UUID}"
        print(f"scanning for {target} (compressor must be running)...")
        while True:
            dev = await BleakScanner.find_device_by_filter(self._matches, timeout=15.0)
            if dev:
                print(f"found {dev.address} ({dev.name})")
                return dev.address
            print("  not found, retrying...")

    async def run_once(self, address):
        async with BleakClient(address) as client:
            print(f"connected to {address}")
            await client.start_notify(NOTIFY_UUID, self.on_notify)
            print(
                f"subscribed; polling {CMD_READ_LIVE!r} every {self.args.interval}s "
                f"(Ctrl+C to stop)\n"
            )
            while client.is_connected:
                try:
                    await client.write_gatt_char(WRITE_UUID, CMD_READ_LIVE, response=False)
                except Exception as e:
                    print(f"write failed: {e}")
                    break
                await asyncio.sleep(self.args.interval)
            print("disconnected (compressor off?)")

    async def run(self):
        if self.args.discover:
            await self.discover()
            return
        while True:
            try:
                address = await self.find_address()
                await self.run_once(address)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"connection error: {e}; retrying in 5s")
            if self.args.once:
                return
            await asyncio.sleep(5.0)


def main():
    ap = argparse.ArgumentParser(description="EasyStart live BLE monitor")
    ap.add_argument("--address", help="BLE MAC (Windows) / CoreBluetooth UUID (macOS); skip scan")
    ap.add_argument("--name", help="select unit by advertised name substring, e.g. EasyStart_A1B2")
    ap.add_argument(
        "--discover",
        "--list",
        dest="discover",
        action="store_true",
        help="discovery phase: scan for EasyStart_* units, print name+MAC, then exit",
    )
    ap.add_argument("--interval", type=float, default=1.0, help="poll period seconds")
    ap.add_argument("--raw", action="store_true", help="raw bytes only, no decode")
    ap.add_argument("--once", action="store_true", help="exit after one disconnect")
    args = ap.parse_args()
    try:
        asyncio.run(Monitor(args).run())
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
