# Hardware-in-the-loop validation

The hardware-in-the-loop (HIL) system validates an ESP32-S31 coreboard with a
Waveshare ESP32-P4-WIFI6-DEV-KIT as a programmable peer. The P4 board also
checks its onboard ESP32-C6 over the board's SDIO ESP-Hosted-MCU link. Host-side
software controls both serial consoles and records machine-readable evidence.

The implementation is deliberately fail-closed. Tests that need a cable, card,
USB drive, or inter-board wiring report `SKIP` when that fixture is absent. A
driver probe, an interface registration, and an end-to-end data transfer are
different evidence levels and are not treated as interchangeable.

## Components

| Component | Location | Responsibility |
| --- | --- | --- |
| Host runner | [`tools/hil/s31_hil.py`](../tools/hil/s31_hil.py) | Opens both serial consoles, starts bounded cases, prints results, and optionally saves one JSON record |
| S31 agent | [`s31-hil-agent`](../buildroot-external/board/esp32-s31/overlay/usr/bin/s31-hil-agent) | Checks the Linux image, overlays, standalone controllers, SDMMC, Ethernet, USB mass storage, and peer-test preconditions |
| S31 peripheral probe | [`s31-peripheral-test`](../buildroot-external/board/esp32-s31/overlay/usr/bin/s31-peripheral-test) | Exercises controllers that do not require an external protocol peer |
| P4 tester firmware | [`tools/hil/esp32p4-tester`](../tools/hil/esp32p4-tester/) | Provides a guarded UART RPC endpoint, safe GPIO primitives, P4 self-tests, and onboard C6 Wi-Fi/Bluetooth checks |

The expected control path is:

```text
host runner
  +-- S31 CP2102N console --> s31-hil-agent --> Linux drivers/overlays
  `-- P4 CH343 UART0 ------> P4 tester ------> GPIO matrix and onboard C6
```

Both consoles run at 115200 baud. On Linux, the runner prefers stable
`/dev/serial/by-id` names containing `CP2102N` for S31 and `CH343` (or
`1a86_55d3`) for P4. Explicit `--s31-port` and `--p4-port` arguments override
automatic selection. On Windows, COM ports require `pyserial`.

## Result protocol and evidence levels

Agents emit one line per result. Other console output is ignored:

```text
HIL1 {"board":"esp32-s31","status":"PASS","test":"cpu.smp","level":"probe","detail":"online=0-1"}
```

The required fields are `board`, `status`, `test`, `level`, and `detail`.
`status` has the following meaning:

- `PASS`: the named check produced its stated level of evidence.
- `FAIL`: the fixture was present or the operation was expected, but the check
  failed. Any `FAIL` makes the runner exit with status 1.
- `SKIP`: a declared prerequisite was absent or a destructive step was not
  authorized. A `SKIP` is not a pass and does not make the run fail.

Evidence levels prevent a shallow probe from being presented as a functional
test:

| Level | Meaning |
| --- | --- |
| `firmware` | Board identity, firmware readiness, or an internal firmware operation |
| `probe` | Linux device, route metadata, overlay, or interface registration |
| `safety` | High-impedance state, output authorization, or automatic disarm |
| `electrical` | A cable, card, peer, carrier, enumeration, or sampled GPIO state exists |
| `data` | Payload transfer or controller operation completed |
| `destructive` | A state-changing check was intentionally withheld or authorized |
| `summary` | Per-agent aggregate result |

Each agent must finish with a `test="summary"` record. No received records,
no summary, a missing serial endpoint, and any `FAIL` are distinct host-runner
errors. Saved files contain a host timestamp and the unmodified result objects.

## Electrical safety contract

The P4 firmware reserves only GPIO 2, 3, 4, 5, 20, 21, 22, 23, 46, 47, and
48 for fixture work. At boot, on explicit disarm, and after an arm timeout,
every reserved pin is configured as input with both pulls disabled.

Output commands use a per-boot eight-digit hexadecimal token:

1. Send `hil hello` and read the token from `rpc.hello`.
2. Send `hil arm <token>` immediately before an output operation.
3. The arm expires after 10 seconds; the watchdog checks at 100 ms intervals
   and returns all reserved lines to input/no-pull.
4. Send `hil disarm` or `hil reset-lines` after a sequence instead of relying
   only on the timeout.

`hil gpio-write` rejects pins outside the safe pool, invalid levels, expired
arms, and unarmed requests. `hil gpio-input` and `hil gpio-read` are available
without arming. These guards reduce software error risk; they do not replace a
common ground, 3.3 V-only signaling, current limiting where appropriate, or a
wiring continuity check before power is applied.

The S31 fixture lanes currently used to prove GPIO-matrix routing are GPIO
42-45. Firmware-only validation applies one controller at a time and then
removes its volatile overlay:

| Controller | Temporary S31 routes |
| --- | --- |
| UART1 | TX=42, RX=43 |
| I2C0 | SCL=42, SDA=43 |
| GPSPI2 | SCLK=42, MOSI=43, MISO=44, CS0=45 |
| I2S0 | BCK out/in=42, WS out/in=43, data out=44, data in=45 |
| TWAI0 | TX=42, RX=43 |

The installed first four-wire harness keeps the S31 lane number stable across
every protocol.  Its P4 end is physically reversed, and the tester firmware
maps the logical lanes accordingly:

| Logical lane | S31 coreboard | P4 tester | Default state |
| --- | --- | --- | --- |
| L0 | GPIO42 / J2-20 | GPIO23 / P6-6 | Input/no-pull until the active case assigns direction |
| L1 | GPIO43 / J2-17 | GPIO22 / P6-11 | Input/no-pull until the active case assigns direction |
| L2 | GPIO44 / J2-18 | GPIO21 / P6-10 | Input/no-pull until the active case assigns direction |
| L3 | GPIO45 / J2-15 | GPIO20 / P6-12 | Input/no-pull until the active case assigns direction |
| Reference | GND | GND | Common signal reference; do not connect either 3.3 V rail |

The mapping was electrically verified in both directions with all-zero,
all-one, walking-one, walking-zero, and alternating patterns. Host automation
and protocol responders should use `hil lane-*` commands instead of assuming
that P4 GPIO numbers increase with lane numbers.

P4 GPIO 2-5 and 46-48 remain in the guarded safe pool for later dedicated
interrupt, clock, reset, or analyzer lanes. They are not part of the initial
four-wire cable. Before connecting the cable, use a continuity meter to verify
each end and confirm that neither board drives a lane during reset.

The responder is expected to reassign the same four wires per case:

| Case | L0 | L1 | L2 | L3 |
| --- | --- | --- | --- | --- |
| GPIO | Stimulus/sample | Return/sample | Optional IRQ | Spare |
| UART1 | S31 TX / P4 RX | P4 TX / S31 RX | Spare | Spare |
| I2C0 | SCL, open-drain | SDA, open-drain | Optional interrupt | Spare |
| GPSPI2 | S31 SCLK | S31 MOSI | P4 MISO | S31 CS0 |
| I2S0 | S31 BCK | S31 WS | S31 data out | P4 data out |
| PWM/PCNT | S31 PWM / P4 measure | P4 pulse / S31 PCNT | Optional sync | Spare |
| TWAI0 | S31 TX / P4 RX | P4 TX / S31 RX | Spare | Spare |

Directions in this table describe the intended active phase. Every phase must
begin with both ends as inputs, configure the receiver first, arm the P4 only
for the bounded transmit interval, and finish by disarming P4 before removing
the S31 overlay. I2C requires suitable pull-ups to 3.3 V; do not enable both
internal pulls as a substitute for a known bus fixture. A physical CAN-bus
test requires transceivers and termination and is separate from a direct
logic-level TWAI controller test.

This table is a routing contract, not an instruction to short signals together.
The host sequencer and P4 responders implement the receiver-first direction
schedule for GPIO, UART, I2C, SPI, I2S, and PWM/PCNT. Use their dedicated cases
only after the four lanes and common ground have been continuity-checked. TWAI
still requires the appropriate transceiver and termination; it is not part of
the direct four-wire P0-P2 matrix.

## Test matrix

### P4 and onboard C6, no external fixture

`hil selftest` checks:

- the ESP32-P4 identity and two HP cores;
- flash inventory of at least 8 MiB, current free 8-bit heap, and monotonic
  timer behavior;
- high-impedance state of every reserved fixture GPIO;
- ESP-Hosted-MCU initialization and C6 firmware-version RPC over SDIO;
- an active Wi-Fi scan, reporting only AP count, strongest RSSI, and channel,
  never SSIDs;
- NimBLE host synchronization through ESP-Hosted VHCI;
- explicit `SKIP` for the unconnected S31 electrical loopback.

The host runner first sends `hil hello`, retries once if opening the UART reset
the board, and only then starts `hil selftest`. Lack of a bidirectional RPC
response is a firmware-level failure.

### S31 firmware, no external fixture

The `firmware` case checks:

- ESP32-S31 device-tree identity and CPUs 0-1 online;
- `/dev/s31-overlay`, the general peripheral probe, `/dev/hwrng`, and the MTD
  inventory;
- patchable route metadata for UART1, I2C0, GPSPI2, I2S0, and TWAI0;
- apply/register/remove behavior for each temporary GPIO-matrix overlay;
- TIMG/RTC counters and watchdogs;
- LEDC, MCPWM, SDM, and PCNT registration plus bounded PWM enable/disable;
- ADC and touch samples, DAC channel registration, comparator event controls,
  and temperature sampling;
- AHB-GDMA `dmatest` memcpy with one 64 KiB iteration;
- the S31 crypto API test.

The current standalone checks prove driver registration and bounded controller
operations. They do not prove ADC absolute accuracy, output waveform quality,
bus timing margins, or communication with an external device.

### Inter-board peripheral tests

The host runner and P4 tester provide end-to-end cases for GPIO, UART, I2C,
SPI, I2S, and PWM/PCNT. Each case configures the receiver before the transmitter,
performs protocol-specific electrical and payload checks, stops the P4 peer,
removes temporary S31 overlays, and records cleanup. Run cases separately so a
failure in one controller cannot hide evidence from another. `--repeat` repeats
one selected peer case without reboot and is useful for detecting leaked IRQ or
overlay resources.

The current support status and validated operating points are maintained in
[`hil-feature-matrix.md`](hil-feature-matrix.md). Route registration alone is
not an inter-board pass: the corresponding result must contain electrical or
payload evidence and successful cleanup.

### SDMMC

The `sdmmc` case applies `sdmmc0 bus-width=1` only when it is not already
active, waits for enumeration, and reads 1 MiB from the first `/dev/mmcblkN`
device using 4 KiB blocks. This matches the minimal CLK/CMD/DAT0 fixture. No
filesystem is mounted and no write is performed. An absent card is `SKIP`; an
enumerated card that cannot be read is `FAIL`. A temporary overlay is removed
and its cleanup result is recorded. Four-bit and UHS validation require the
additional data wires and, for UHS, a verified 1.8 V-capable power path.

### Direct Ethernet

The `ethernet` case temporarily applies the `gmac` overlay if needed, verifies
`eth0`, brings the interface up with a bounded wait, and reads carrier state.
No cable or carrier is `SKIP`. With carrier present, the agent assigns the
requested local address and requires three ICMP replies from the peer. A
missing reply after carrier is established is `FAIL`, not `SKIP`.

The defaults are S31 `192.168.77.2/24` and P4 `192.168.77.1`. With
`--board both`, the P4 firmware starts its onboard IP101 peer, runs UDP echo,
allows the host to verify MTU-sized payloads, and power-cycles the PHY for
carrier-loss and recovery evidence before cleanup.

### USB mass storage

The `usb-drive` case loads the mass-storage support if available, finds a block
device whose sysfs path is below USB, and mounts its first partition read-only.
Enumeration and read-only mount are reported separately.

Write testing requires `--allow-usb-write`. It mounts read-write, creates a
64 KiB `.s31-hil-probe-*` file from random data, reads it through `sha256sum`,
removes it, synchronizes the filesystem, and unmounts. Without explicit
authorization, the write result is `SKIP` at the `destructive` level. Use a
disposable or backed-up drive: the guard limits the intended write but cannot
make a filesystem or power failure harmless.

USB host mass storage is included in the P1 matrix. USB device/gadget mode is
intentionally outside the requested test scope.

### MTD and dual-core XIP

The `mtd` case uses only the dedicated `hil-scratch` MTD partition. It performs
bounded erase/program/readback cycles, verifies data CRC and final erased state,
and checks that CPU-pinned XIP workers advance and resume around flash-critical
sections. It must never select a kernel, rootfs, radio, persist, or unknown MTD
partition.

### LP core

The `lp-core` case applies the LP overlay, waits for remoteproc readiness,
measures mailbox ping, drains asynchronous startup notifications, verifies an
exact shared-memory request/reply, checks IPC counters, removes the overlay, and
confirms that both HP CPUs remain online.

### SMP, IRQ, and GDMA

The `smp-irq-dma` case runs bounded CPU-pinned load together with XIP, persist,
radio-drop, and kernel-log gates. It then applies a dedicated GDMA overlay, runs
eight 64 KiB `dmatest` copies, verifies both RX and TX interrupt-source counters
advance, and removes the module and overlay.

## Build and deployment

Build the standard S31 kernel, Buildroot root filesystem, and radio module as a
matched set. The kernel configuration changes module ABI details, so flashing a
new kernel while retaining a rootfs radio module from another configuration can
cause an early boot Oops:

```sh
S31_LEAN_RADIO=0 make -C /home/grieferpig/s31linux -j8 rootfs
```

Program and read back both the resulting kernel and rootfs artifacts before a
formal P0-P2 run. A kernel-only flash is not a valid matched-image deployment.

Build and flash the P4 tester with ESP-IDF 6.2 or later and the committed
component versions. The project selects the pre-v3 ESP32-P4 target range so
the normal image remains flashable on the revision 1.3 board; do not bypass
the revision check with a forced v3 image:

```sh
cd tools/hil/esp32p4-tester
source /path/to/esp-idf/export.sh
idf.py -B build-hil set-target esp32p4
idf.py -B build-hil build
idf.py -B build-hil -p /dev/serial/by-id/<P4-CH343> flash
```

After flashing, independently verify that the serial console identifies the
expected board/firmware and that the bytes read back from each programmed
image match the intended artifact. A successful build or flash command alone
is not runtime HIL evidence.

## Running cases

Validate both firmware images before connecting the inter-board harness:

```sh
tools/hil/s31_hil.py \
  --board both \
  --case firmware \
  --output build/hil-firmware.json
```

Use explicit ports when automatic selection is ambiguous:

```sh
tools/hil/s31_hil.py \
  --board both \
  --s31-port /dev/serial/by-id/<S31-CP2102N> \
  --p4-port /dev/serial/by-id/<P4-CH343> \
  --case firmware \
  --timeout 90 \
  --output build/hil-firmware.json
```

Run peer and external-fixture cases independently so one failure does not hide
evidence from another:

```sh
# Four-wire peer cases
for case in gpio uart i2c spi i2s pwm-pcnt; do
  tools/hil/s31_hil.py --board both --case "$case" \
    --output "logs/hil-${case}.json"
done

# Repeat one overlay-heavy case without reboot
tools/hil/s31_hil.py --board both --case i2c --repeat 12 \
  --output logs/hil-i2c-repeat.json

# Onboard C6 as the S31 Wi-Fi/BLE peer
tools/hil/s31_hil.py --board both --case c6-wifi --peer-connected \
  --output logs/hil-c6-wifi.json
tools/hil/s31_hil.py --board both --case c6-ble --peer-connected \
  --output logs/hil-c6-ble.json

# Diagnostic only: isolate protected-authentication failures with an open AP
tools/hil/s31_hil.py --board both --case c6-wifi --wifi-ap-open \
  --peer-connected --output logs/hil-c6-wifi-open.json

# SD card: bounded raw read, never writes
tools/hil/s31_hil.py --board s31 --case sdmmc \
  --output logs/hil-sdmmc.json

# Direct Ethernet with the P4 IP101 peer
tools/hil/s31_hil.py --board both --case ethernet \
  --output logs/hil-ethernet.json

# USB drive: read-only first, then explicit disposable-drive write test
tools/hil/s31_hil.py --board s31 --case usb-drive \
  --output logs/hil-usb-read.json
tools/hil/s31_hil.py --board s31 --case usb-drive --allow-usb-write \
  --output logs/hil-usb-write.json

# On-chip destructive/concurrency cases
tools/hil/s31_hil.py --board s31 --case mtd --output logs/hil-mtd.json
tools/hil/s31_hil.py --board s31 --case lp-core --output logs/hil-lp-core.json
tools/hil/s31_hil.py --board s31 --case smp-irq-dma \
  --output logs/hil-smp-irq-dma.json
```

`--case all` runs all S31 cases sequentially, but separate case files are
preferred for bring-up because they preserve fixture-specific preconditions.
The P4 runner currently executes its self-test for every selected P4 run; the
S31 `--case` selection does not change that behavior.

The normal `c6-wifi` case asks the P4/C6 fixture to create WPA2 SoftAP
`S31-HIL-P4` on channel 6. It requires the persistent S31 Wi-Fi policy to be
disabled and the persistent supplicant profile to be absent. The runner pauses
an existing BTstack user, loads the Wi-Fi radio overlay only for the test, and
stores the supplicant profile under `/tmp`. It then requires association,
DHCP, ICMP, and 64 exact 1472-byte UDP echo exchanges. The P4 report must show
64 packets, 94208 bytes, and zero pattern/echo errors; this proves S31-to-P4
uplink reception and P4-to-S31 downlink echo independently. Cleanup stops the
AP, removes temporary Wi-Fi state, and restores the prior BT radio/service
without changing `/etc/esp32-conf`.

`--wifi-ap-open` is fault-isolation only and does not replace the WPA2 gate.
`--case c6-wifi-recover` restores backup artifacts left by the older
reboot-persistent Wi-Fi workflow; the current runtime-only case does not create
those backups.

## Status record

[`hil-feature-matrix.md`](hil-feature-matrix.md) is the authoritative support
snapshot. Immediately after every formal test run finishes, update the affected
feature row, validated operating point, known limit, and refresh date as
needed. A failed or skipped result must remain visible until it is superseded;
do not turn probe-only evidence into a hardware pass.

Saved JSON files are local evidence for the exact source, images, firmware,
wiring, and fixture state used by that run; they are not permanent proof for a
later revision. Regenerate them after changing any of those inputs.

## Completion criteria

A peripheral is considered end-to-end validated only when its required
evidence chain is complete:

1. the relevant driver and overlay probe successfully;
2. the expected electrical peer or medium is detected;
3. a protocol-appropriate payload operation succeeds;
4. temporary overlays, mounts, addresses, files, and P4 output state are
   cleaned up;
5. the saved record contains no `FAIL` and contains a summary from every
   selected agent.

A firmware-only pass is useful regression evidence, but it does not satisfy
steps 2 and 3 for an external peripheral.
