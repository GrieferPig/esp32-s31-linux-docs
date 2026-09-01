# ESP32-S31 Linux support status

This page is the compact support matrix for the ESP32-S31 Linux port. It
summarizes the strongest result obtained with the standard Buildroot image and
the ESP32-P4 programmable HIL peer. A driver probe alone is not reported as a
hardware pass. Its feature-oriented presentation follows the
[linux-sunxi status matrix](https://linux-sunxi.org/Mainlining_Effort#Status_Matrix),
adapted for one SoC and several evidence levels instead of a many-SoC kernel
version table.

Last matrix refresh: **2026-09-01**.

## Status key

| Mark | Meaning |
| --- | --- |
| ✅ | Implemented and validated on hardware, including the relevant payload or operation |
| ◐ | Usable subset validated; an important mode, stress case, or recovery case remains limited |
| 🧪 | Driver and DT support exist, but evidence is limited to probe, controller-only tests, or internal loopback |
| ○ | Not tested on hardware |
| ❌ | Tested and currently broken |
| — | Not applicable or intentionally outside this test scope |

`Automated` means a repeatable test exists in `tools/hil/s31_hil.py` or the S31
HIL agent. It does not by itself imply a pass.

## Core platform

| Feature | Linux support | DT / configuration | Automated | Hardware | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Boot and XIP | S31 arch and cache support | Standard board DT | Yes | Yes | ✅ | NOMMU Linux boots from flash and remains live during bounded XIP stress |
| SMP | S31 IPI/interrupt support | 2 HP CPUs | Yes | Yes | ✅ | Both CPUs stay online under pinned load, DMA, flash, and radio activity |
| Interrupt matrix | S31 irqchip | Built in | Yes | Yes | ✅ | GPIO child IRQ delivery and peripheral IRQ progress pass; dynamic-overlay IRQ mappings are reclaimed |
| Clock, reset, and power domains | S31 providers | Built in | Partial | Yes | ◐ | Provider ownership and peripheral enable/disable are exercised; CPU DVFS and deep idle are not validated |
| Pinctrl and GPIO Matrix | S31 pinctrl/GPIO | Runtime-routable overlays | Yes | Yes | ✅ | Bidirectional patterns, ordered edge IRQs, ownership, and final high-Z state pass |
| Runtime overlay manager | S31 platform driver and `s31-overlay` | Persistent or volatile profiles | Yes | Yes | ✅ | Apply, parameter patch, conflict detection, removal, and repeated lifecycle tests pass |
| AHB/AXI GDMA | S31 DMAengine drivers | `gdma` and consumer overlays | Yes | Yes | ✅ | Memcpy, slave DMA, cyclic DMA, IRQ progress, and cleanup are covered by several peripherals |
| LP core | remoteproc, mailbox, shared memory | `lp` overlay | Yes | Yes | ✅ | Firmware lifecycle, mailbox ping, exact request/reply, statistics, and removal pass |
| Flash critical sections | S31 cache/MTD coordination | Dedicated scratch partition | Yes | Yes | ✅ | Program/erase preserves dual-core XIP progress and resumes cleanly |

## Digital peripherals

| Feature | Linux interface | Instances / overlay | Automated | Hardware | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| GPIO | GPIO character ABI | GPIO Matrix | Yes | P4 peer | ✅ | Static input/output, IRQ edge order, pull following, and fail-safe release pass |
| UART | TTY | `uart1`, `uart2` | Yes | P4 peer | ✅ | Exact bidirectional payloads pass at 115200, 460800, and 921600 baud |
| UART3 | TTY and UHCI DMA | `uart3`, `uart3-dma` | Yes | Internal loopback | ✅ | PIO passes three baud rates; DMA passes 8192 bytes at 921600 baud |
| I2C | I2C adapter | `i2c0`, `i2c1` | Yes | P4 slave | ✅ | 100 kHz, 400 kHz, and 1 MHz are selectable; 1 MHz passes 10/10 complete dual-controller cycles |
| SPI master | SPI/spidev | `gpspi2`, `gpspi3` | Yes | P4 slave | ◐ | Full duplex passes all modes at 13.333 MHz and modes 1/2 at 20 MHz; see limits below |
| SPI target | SPI controller target mode | `gpspi2-target`, `gpspi3-target` | No | No | 🧪 | Driver and mutually exclusive target overlays exist; no external-master acceptance run |
| I2S | ASoC PCM | `i2s0`, `i2s1` | Yes | P4 peer | ◐ | Bounded 8 kHz stereo smoke passes in both directions; full 16 KiB integrity stress remains fixture-limited |
| TWAI | SocketCAN | `twai0`, `twai1` | Probe only | No transceiver | 🧪 | Controller and route lifecycle exist; arbitration, error states, and bus recovery are not tested |
| LEDC PWM | PWM ABI | `pwm-counter` | Yes | P4 measurement | ✅ | P4 measures 998 Hz and exact 25.0% duty |
| PCNT | Counter ABI | `pwm-counter` | Yes | P4 pulse source | ✅ | S31 counts an exact bounded 200-pulse train |
| MCPWM | PWM/capture/fault support | `pwm-counter` | Controller only | No external load | 🧪 | Registration and bounded enable/disable exist; capture, synchronization, and fault braking need fixtures |
| Sigma-Delta | PWM-like output | `pwm-counter` | Controller only | No external measurement | 🧪 | Driver registration is covered; waveform quality is not measured |
| Timers | clocksource/counter APIs | `timers` | Controller only | On-chip | 🧪 | SYSTIMER, RTC timer, and GPTimer register and advance; long-duration accuracy is not characterized |
| Watchdogs | watchdog ABI | `watchdogs` | Controller only | On-chip | 🧪 | Registration and bounded control are covered; an intentional reset test is not part of HIL |

## Storage and networking

| Feature | Linux interface | Fixture | Automated | Hardware | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| SPI NOR / MTD | MTD and XIP | Onboard flash | Yes | Yes | ✅ | Dedicated 64 KiB scratch area passes erase, program, CRC readback, and final erase |
| SD/MMC host 0 | MMC block | 1-bit SD card | Yes | Yes | ✅ | Card enumeration and bounded 1 MiB sector read pass |
| SD/MMC host 1 | MMC block | None | No | No | 🧪 | Driver and overlay exist; no second-slot hardware result |
| SD/MMC 4-bit and UHS-I | MMC block | Additional data lines and 1.8 V path | No | No | 🧪 | DT parameters and UHS overlay exist; only the 1-bit 3.3 V path is validated |
| USB host | DWC2 | USB flash drive | Yes | Yes | ✅ | Enumeration, ext4 mount, 64 KiB write/readback, deletion, sync, and unmount pass |
| USB device / gadget | DWC2 and ConfigFS | Host cable | No | No | ○ | Implemented but intentionally outside the current HIL matrix |
| Ethernet | DWMAC/GMAC | Direct cable to P4 IP101 | Yes | Yes | ✅ | Carrier, ICMP, exact UDP echo, MTU payload, link loss, and recovery pass |
| Ethernet PTP | PHC/timestamp path | Direct cable | No | No | 🧪 | Driver path exists; timestamp accuracy and synchronization are not validated |
| Wi-Fi | cfg80211 full-MAC radio driver | P4/C6 SoftAP | Yes | Yes | ✅ | WPA2 association, DHCP, ICMP, and exact bidirectional UDP payload pass |
| Bluetooth LE | HCI and BTstack | P4/C6 peer | Yes | Yes | ✅ | Advertising, service discovery, characteristic read, disconnect, and reconnect pass |
| Wi-Fi/Bluetooth coexistence | Shared S31 radio | P4/C6 | Partial | Yes | ◐ | Tests restore radio ownership and show zero drops in bounded stress; extended concurrent traffic is not characterized |

## Analog, security, and system services

| Feature | Linux interface | Automated | Hardware | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| ADC | IIO | Controller only | On-chip/pads | 🧪 | Direct, buffered, and differential paths exist; absolute accuracy needs calibrated sources |
| DAC | IIO | Probe only | No external measurement | 🧪 | Channels register; voltage accuracy and settling are not measured |
| Temperature sensor | hwmon | Controller only | On-chip | 🧪 | Readings, thresholds, and events exist; temperature calibration is not independently checked |
| Touch sensor | IIO proximity | Controller only | No touch fixture | 🧪 | Samples are available; sensitivity and threshold behavior need a repeatable electrode fixture |
| Analog comparator | IIO event | Controller only | No analog fixture | 🧪 | Event controls exist; threshold crossings are not externally stimulated |
| Hardware RNG | hwrng | Firmware case | On-chip | ◐ | Device registration and reads pass; statistical quality certification is outside HIL |
| eFuse | nvmem | Probe only | On-chip | 🧪 | Read-only provider exists; field decoding and irreversible programming are not tested |
| Crypto accelerator | Linux crypto API | Partial | On-chip | 🧪 | Driver exists; the standard image still needs a stable packaged end-to-end crypto regression helper |
| GP LDO | regulator | Probe only | No external measurement | 🧪 | Supported voltage selections are exposed; rail voltage and load regulation are not measured |

## Validated operating points

| Interface | Validated point | Result |
| --- | --- | --- |
| UART1/2 | 921600 baud | Exact bidirectional payload and CRC |
| UART3 DMA | 921600 baud, 8192 bytes | Exact internal-loopback payload |
| I2C0/1 | 1 MHz | Repeated start, register write/read, wrong-address NACK, recovery; 10/10 cycles |
| SPI GPSPI2/3 | 13.333 MHz effective, modes 0-3, 4096 bytes | Exact full-duplex payload |
| SPI GPSPI2/3 | 20 MHz, modes 1/2, 4096 bytes | Exact full-duplex payload; repeated stress and fresh-overlay cycles pass |
| SPI GPSPI2/3 | 40 MHz, mode 1, 4096 bytes | S31-to-P4 TX only, 20/20; not a full-duplex qualification |
| I2S0/1 | 8 kHz stereo S16_LE | Bounded bidirectional smoke pass |
| Ethernet | 1472-byte UDP payload | Exact bidirectional echo and PHY recovery |
| SDMMC0 | 1-bit, 3.3 V | Enumeration and 1 MiB read |
| USB host | 64 KiB file | Write, readback, delete, sync, and unmount |
| MTD | Four 8 KiB cycles | Erase/program/readback/final erase with dual-core XIP progress |

## Known limits

- SPI full-duplex qualification stops at 20 MHz. At 26.667 MHz the P4 v1.3
  slave cannot provide a common receive/transmit edge that passes both
  directions; at 40 MHz only S31-to-P4 traffic is validated.
- The P4 v1.3 slave fixture does not validate SPI modes 0/3 at 20 MHz; the same
  behavior occurs with an ESP-IDF S31 master, so this is not assigned to the
  Linux master driver.
- I2S passes the bounded functional gate, while the separate 16 KiB stress case
  remains sensitive to the loose-wire fixture.
- Dynamic OF overlay removal emits the kernel's known property-memory warning.
  Overlay ownership and IRQ mappings are nevertheless released and tested.
- SDMMC evidence covers only host 0 in 1-bit mode. Four-bit, host 1, UHS-I, and
  card write testing require additional fixtures or explicit authorization.
- Destructive flash testing is confined to `hil-scratch`; it never selects the
  kernel, root filesystem, radio firmware, persistent data, or an unknown MTD
  partition.

## Updating the matrix

After a formal HIL run, update the affected row, its validated operating point,
and the refresh date. Preserve failures as a limit or `❌` status until a later
run supersedes them. Raw machine-readable results may be saved with `--output`;
they are run evidence, not part of this status overview.

The wiring, safety contract, commands, and acceptance rules are documented in
[Hardware-in-the-loop validation](hardware-in-the-loop.md).
