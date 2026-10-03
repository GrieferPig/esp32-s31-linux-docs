# Feature support

This page summarizes the port's features and current limitations. Status labels
are the project's reported maturity, not a claim that every feature has passed
hardware testing on every current build. The standard
[full board configuration](../get-started/build-configuration.md) includes optional
bus, audio, storage, and networking drivers; runtime overlays enable the devices.

Hardware boot and flashing validation of the current
[compact flash layout](../hw-reference/flash-layout.md) is pending. Successful
host checks and image builds do not establish runtime validation.

## Legend

| Status | Meaning |
|---|---|
| 🟢 Stable | Fully supported and tested |
| 🟡 Experimental | Supported; may have limitations or require further testing |
| 🟠 WIP | Driver exists, but full functionality is work in progress |
| 🔴 Unsupported | Not implemented or supported |

## System

| Feature | Status | Notes |
|---|---|---|
| Linux, Sv32 MMU, and flash XIP | 🟢 Stable | 16 MiB flash and 16 MiB PSRAM layout |
| Dual-core SMP | 🟢 Stable | Both HP cores run Linux |
| Persistent root filesystem | 🟢 Stable | SquashFS with a JFFS2 writable layer |
| Runtime overlays | 🟢 Stable | Peripheral selection, pin routing, and saved settings |
| CPU frequency scaling | 🟢 Stable | Shared 80, 160, 240, and 320 MHz policy |
| CPU idle | 🟢 Stable | Firmware-assisted WFI |
| LP firmware and mailbox | 🟡 Experimental | remoteproc, PING/PONG, timer and GPIO diagnostics |
| Suspend-to-idle | 🟡 Experimental | Exercises suspend/resume with the HP CPU polling |
| Timed deep sleep | 🟡 Experimental | Restarts through a cold boot |
| Normal poweroff | 🟡 Experimental | External reset or a power cycle starts the board again |
| Suspend-to-RAM | 🟠 WIP | Experimental APPWR retention, timer recovery, and optional LP GPIO wake |

See [Power management](../api-guides/power-management.md) for the commands and
wake-source settings. Linux, OpenSBI, and LP firmware share the 112-byte ABI-v1
control block in the current source; rebuild them together. Matching protocol
code does not establish hardware retention or recovery. Current consumption
still needs measurement.

## Radio

The supplied rootfs uses BTstack through direct HCI. BlueZ and its supporting
userspace stack are not packaged; the post-build script also removes those
files from the target tree. Using BlueZ with the alternate Linux HCI frontend
requires a custom rootfs configuration and packaging changes, plus a radio
reload with `direct_hci=0`.

| Feature | Status | Notes |
|---|---|---|
| Wi-Fi station | 🟡 Experimental | Single-station mac80211/cfg80211 frontend; `iw` and `wpa_supplicant` |
| Bluetooth | 🟡 Experimental | BTstack with direct HCI; alternate Linux HCI frontend |
| AP and AP+station | 🔴 Unsupported | Current SoftMAC frontend rejects non-station interfaces |
| Protected AP | 🔴 Unsupported | AP mode is not exposed by the current frontend |
| Active Wi-Fi suspend/recovery | 🟠 WIP | Active-interface suspend/replay unsupported; recovery is not established |

For the available setup paths, see
[Wi-Fi and Bluetooth](../api-reference/radio/index.md) and
[Advanced Wi-Fi](../api-guides/wifi-advanced.md).

## Peripherals

| Feature | Status | Notes |
|---|---|---|
| GPIO and UART | 🟢 Stable | UART0 console, optional UART routes and UART3 DMA |
| I2C0/I2C1 | 🟡 Experimental | Not tested on long transfers |
| GPSPI2/GPSPI3 host | 🟡 Experimental | Controller and data-lane settings depend on the selected device |
| GPSPI target | 🟡 Experimental | DMA transfers up to 4096 bytes |
| I2S/TDM | 🟡 Experimental | Playback/capture and configurable framing. Need testing on more external codecs |
| SD/MMC | 🟡 Experimental | Slot wiring and bus width selected by overlay |
| Ethernet | 🟡 Experimental | Requires the board's external PHY setup |
| USB gadget | 🟡 Experimental | Needs more runtime role testing |
| AHB/AXI GDMA | 🟡 Experimental | Used by peripheral drivers |
| Timers, PWM, and pulse counter | 🟡 Experimental | Timer 1 in each timer group is reserved for CPU idle |
| Analog and sensor blocks | 🟡 Experimental | ADC, DAC, touch, comparator, and temperature interfaces |
| Watchdog, NVMEM, RNG, and crypto | 🟡 Experimental | Through their Linux subsystems |
| TWAI/CAN | 🟠 WIP | Not tested |
| USB host | 🟠 WIP | Not tested |
| RMT | 🔴 Unsupported | No documented driver support |

The [peripheral reference](../api-reference/peripherals/index.md) gives the
API settings and transfer limits. The [overlay catalog](overlay-catalog.md)
lists the controller selections.

## Testing and known issues

The project includes host tests and board/peer tests for the major interfaces.
See [HIL testing](../contribute/testing-hil.md) for commands and fixture setup.

### I2S
Reported I2S board tests cover S16_LE stereo at 8, 16, and 48 kHz. SPI target
reports cover modes 0–3 and 8-, 16-, and 32-bit MSB-first transfers through
4096 bytes at 100 kHz.

### SPI Flash

NOR programming and JFFS2 failures can affect saved settings or startup.
