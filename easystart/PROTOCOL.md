# EasyStart Bluetooth Protocol

Reverse-engineered from `net.microair.easystart` v4.2 (versionCode 19) by APK static analysis
(apktool smali). Status: **fully decoded and hardware-validated** (live BLE capture;
see section 7).

## 1. Transport - Laird VSP (Virtual Serial Port)

The module uses a Laird BLE module exposing the Laird VSP service. Application data is a
byte/ASCII stream tunnelled over GATT.

| Role | UUID | GATT props |
|------|------|------------|
| Service | `d973f2e0-b19e-11e2-9e96-0800200c9a66` | Primary |
| **Notify** (module -> host, responses) | `d973f2e1-b19e-11e2-9e96-0800200c9a66` | NOTIFY (CCCD 0x2902) |
| **Write** (host -> module, commands) | `d973f2e2-b19e-11e2-9e96-0800200c9a66` | WRITE, WRITE NO RESPONSE |

> Roles confirmed via nRF Connect against one of the installed modules (advertised name
> `EasyStart_XXXX`; identifiers redacted - this is a public repo).
> Note: `e1` is **notify**, `e2` is **write** - the opposite of the usual Laird VSP convention.
> Device advertises name `EASYSTART_<id>` (matches the app's `ESbluetoothID` config).

- The module advertises with a device name the app matches against a user-configured ID
  (`ESbluetoothID1/2/3`). Match by the VSP **service UUID** in advertisement data instead.
- **No pairing/bonding, no PIN, no passkey, no application handshake.** Confirmed: the smali
  contains no `createBond`, `setPin`, `passkey`, or auth strings.
- Connection sequence (from `Connect.smali` / `MainActivityKt$gattCallBack$1`):
  1. Connect GATT.
  2. Request larger MTU (app requests one; `onMtuChanged` logs "Allowed MTU=").
  3. Discover services; locate the VSP service + write/notify characteristics.
  4. Subscribe to notifications on the notify characteristic (write the CCCD `0x2902`
     descriptor to enable notify).
  5. Write a command string to the write characteristic; responses arrive as notifications.
  - On connect the app issues `{"Cmd": ReadEEP}` to load config. For live monitoring this is
    **not required** - you can go straight to `ReadLive`.

## 2. Commands (host -> module)

Commands are ASCII strings written to the write characteristic. Note the loose,
**non-strict-JSON** format (unquoted values, space after colon), written verbatim:

| Command string | Purpose |
|----------------|---------|
| `{"Cmd": ReadLive}` | **Read live status frame** (compressor current, state, counters) |
| `{"Cmd": ReadEEP}` | Read EEPROM config blob |
| `{"Cmd": NormMode}` | Enter normal mode |
| `{"Cmd": ProgMode}` | Enter programming mode |
| `{"Cmd": ChipErase}` | Erase chip (firmware) |
| `{"Cmd": OtaBegin/OtaPrep/OtaWrt/OtaEnd/OtaAbort}` | OTA firmware update |
| `{"Int": FlashBuff}` / `{"Wrt": FlashBuff}` / `{"End": FlashBuff}` | Flash buffer transfer |

For our use case only **`{"Cmd": ReadLive}`** is needed. Poll it on an interval; the app polls
on a fixed-rate timer at ~1 Hz (confirmed in capture). Our ESPHome component defaults to 2 s.

## 3. Response framing (module -> host)

From `MainActivityKt$gattCallBack$1.onCharacteristicChanged`:

- Each notification is handled two ways simultaneously:
  1. Decoded as an ASCII string (`getStringValue(0)`) into `esNotifyStr`. If it **contains
     `"Success"`** (or `"Fail"`) the app treats the response as complete and dispatches the
     active screen's parser.
  2. Its raw bytes are appended (`copyInto`) into an accumulation buffer selected by the
     current command state (`esCmdState`):
     - `esCmdState == 0` -> `esNotifyLiveData` (ReadLive) <- **our path**
     - `esCmdState == 1 || 3` -> `esNotifyEEPData` (EEPROM)
     - `esCmdState == 4` -> `esNotifyBytes` (firmware/OTA)
- The buffer length (`esNotifyLiveDataLength`) accumulates across fragments, so a response
  **may span multiple notifications**. It is reset before each new request.

**Confirmed:** a `ReadLive` poll produces **two notifications** - the **18-byte** binary live
frame, and a short ASCII status marker `{"Sts": Success}` (or a `Fail` variant). nRF Connect
only displays the most recent value, which is why it showed `{"Sts": Success}`.

**Robust host strategy:** on each poll, clear a receive buffer, send `{"Cmd": ReadLive}` to
the write char (`e2`), and for each notification on the notify char (`e1`): if it starts with
`{` treat it as the ASCII status marker (ignore for live values / use as completion), else it
is the binary frame - decode it. See section 4.

## 4. Live-data frame layout (`ReadLive` response)

**The live frame is exactly 18 bytes.** Decoded from `Status.smali` and **validated against
live hardware** (one of the installed modules, 2026-07-21) - the app's on-screen values matched
the decode exactly (current, peak 24.5 A, freq 59.8 Hz, total starts 4947). Multi-byte values
are **little-endian, unsigned**.

| Offset | Field | Formula | Example (`10 00 00 05 3f 00 a9 20 f5 00 00 00 00 00 53 13 00 00`) |
|-------:|-------|---------|---------|
| [0] | Frame header / length | constant `0x10` | 16 |
| [1] | Reserved | `0x00` | 0 |
| [2] | System state / fault | table section 5 (`>9` -> "Not Defined") | 0 -> Normal |
| [3] | Learned starts | `b[3]` | 5 |
| [4]+[5]*256 | **Live current (A)** | `/ 10` | 63 -> **6.3 A** |
| [6]+[7]*256 | **Line frequency (Hz)** | `500000 / value` (value is a period) | 8361 -> **59.8 Hz** |
| [8]+[9]*256 | Last start peak (A) | `/ 10` | 245 -> **24.5 A** |
| [0xA]+[0xB]*256 | Short-cycle (SCPT) delay | raw u16 | 0 |
| [0xC]+[0xD]*256 | Total faults | raw u16 | 0 |
| [0xE]+[0xF]+[0x10]+[0x11]*... | Total starts | **u32** LE | 0x00001353 -> **4947** |

Notes:

- Line frequency is a **period**, not a scaled integer: `Hz = 500000 / (b[6] + b[7]*256)`.
  ~8361 -> 59.8 Hz (US 60 Hz mains; the +/-3 LSB jitter is +/-0.02 Hz).
- Total starts is a **32-bit** little-endian counter spanning [0x0E]-[0x11].
- The live current is the primary compressor-draw signal; see section 6.

## 5. System-state / fault codes (byte [2])

From the `statusText[]` array in `Status.smali`:

| Code | Meaning |
|-----:|---------|
| 0 | Normal |
| 1 | Unexpctd Curr Flt |
| 2 | Short Cycle Delay |
| 3 | Pwr Intrrptn Fault |
| 4 | Stall Fault |
| 5 | Stuck SR Fault |
| 6 | Open Ovrld Fault |
| 7 | Overcurrent Fault |
| 8 | Bad Wiring Fault |
| 9 | Wrong Voltage Flt |
| >9 | Not Defined |

Note "Short Cycle Delay" (2) is a transient waiting state, not a hard fault.

## 6. Deriving "compressor running / power state"

**The module's BLE radio is only powered while the compressor is on** (observed behavior):
when the compressor turns off, Bluetooth powers down and the device stops advertising / drops
the connection. This makes **BLE presence the primary running signal**:

- **Primary:** compressor running <-> the module is connectable / the GATT connection is up.
  In ESPHome, drive the running `binary_sensor` from the `ble_client` connection state, not a
  current threshold. On disconnect -> running = false and the data sensors go stale/unavailable.
- **Consequence:** you will never observe an idle/standby current over BLE - every reading is
  "running" current, so the /10 scaling is validated against the running value only. A current
  threshold is redundant for on/off but current magnitude is still useful telemetry.
- **Corroborating:** system-state byte [2] - a running compressor shows current with state
  `Normal (0)`; `Short Cycle Delay (2)` means commanded-on but waiting.
- Each compressor power-on produces a fresh advertise -> connect -> service-discovery handshake;
  expect a short delay after power-on before the module is connectable, and auto-reconnect
  churn as it cycles.

## 6a. Earlier HCI (btsnooz) attempt - superseded

Historical note. A Pixel 7a bugreport `btsnooz_hci.log` (filtered mode - ATT payloads
truncated to the first ~3 bytes) gave only partial confirmation before the full-payload
validation in section 7 replaced it:

- Confirmed the GATT handles - notify `0x000e` (CCCD `0x000f`), write `0x0011` - and that the
  write payload begins `7b 22 43` = ASCII `{"C...` (`{"Cmd": ReadLive}`).
- The truncated 3 bytes tracked a compressor start->run->stop cycle (load data present).
- Its framing estimate (~20-byte value) was slightly off due to truncation; the full capture
  showed the frame is **18 bytes** (section 4).

> Takeaway: Pixel/AOSP "Enable Bluetooth HCI snoop log" runs FILTERED, stripping ATT payloads,
> so bugreport HCI is not usable for app-layer RE. Use nRF Connect or the Python monitor.

## 7. Validation status

**Fully validated end-to-end** via `python/easystart_monitor.py` against live
modules, with app-displayed values as ground truth:

| Field | App | Decode |
|-------|-----|--------|
| Live current | 6.6 A | yes (/10; frame instant read 6.3 A) |
| Last start peak | 24.5 A | yes exact |
| Line frequency | 59.8 Hz | yes exact (`500000/period`) |
| Total starts | 4947 | yes exact (u32) |
| System state | Normal | yes (byte [2] = 0) |

Characteristic roles, command string, framing, and the full 18-byte layout are all confirmed.

**Independent cross-check:** this from-scratch decode matches the community ESPHome
implementations byte-for-byte - [Keen-coffee](https://github.com/Keen-coffee/home_assistant/blob/main/easyStart)
(original) and [DerekSeaman](https://github.com/DerekSeaman/ESPHome-Micro-Air-EasyStart) - including
the non-obvious `500000/period` frequency, the u32 total-starts, the two-notification framing,
and write=`e2`/notify=`e1`. This decode additionally reads byte `[3]` = learned starts, which
neither of those implementations decodes.

## 8. Remaining minor unknowns

The protocol is complete for monitoring. A few low-value details are not fully pinned down:

- Byte [1] is always `0` in captures; byte [0] is a constant `0x10` (assumed a frame
  length/opcode). Neither is needed to decode the data.
- The other commands (`ReadEEP`, `NormMode`, `ProgMode`, OTA/flash) are identified but their
  request/response payloads were not reverse-engineered - not needed for read-only monitoring.
- Exact poll interval the app uses (~1 s observed) - irrelevant for our own polling.
