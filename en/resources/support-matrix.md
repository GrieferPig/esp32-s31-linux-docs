# Feature support

This page separates implementation and build availability from reported hardware
coverage. The standard [full board configuration](../get-started/build-configuration.md)
includes optional buses, audio, storage, and networking drivers.

Hardware boot and flashing validation of the current compact layout is pending.
Host tests and builds do not establish runtime acceptance. Boot, persistence
and peripheral recovery of the merged image remain unverified.

## Availability labels

| Label | Meaning |
|---|---|
| 🟢 Included | The default build selects this support; runtime setup may still be required |
| 🟡 Implemented | A driver or protocol path exists; the notes describe setup or validation still needed |
| 🟠 WIP | Integration or hardware validation remains incomplete |
| 🔴 Absent | No ESP32-S31 implementation is provided in this repository |

These labels describe the [build configuration](https://github.com/GrieferPig/esp32-s31-linux/blob/main/Makefile)
and driver support. Hardware reports and their tested scope are listed below.

## System

| Feature | Availability | Notes |
|---|---|---|
| Linux, Sv32 MMU, and flash XIP | 🟢 Included | Configured for 16 MiB flash and 16 MiB PSRAM |
| Dual-core SMP | 🟢 Included | Both HP harts are configured to run Linux |
| Persistent root filesystem | 🟢 Included | SquashFS with a JFFS2 writable layer |
| Runtime overlays | 🟢 Included | Peripheral selection, pin routing, and saved settings |
| CPU frequency scaling | 🟢 Included | Shared 80, 160, 240, and 320 MHz policy |
| CPU idle | 🟢 Included | Firmware-assisted WFI |
| LP firmware and mailbox | 🟡 Implemented | remoteproc, PING/PONG, timer and GPIO diagnostics |
| Suspend-to-idle | 🟡 Implemented | The LP timer-wake diagnostic polls on the HP CPU |
| Timed deep sleep | 🟡 Implemented | Timed wake follows the cold-boot path |
| Normal poweroff | 🟡 Implemented | Does not arm timed wake; restart through external reset or a power cycle |
| Suspend-to-RAM and LP GPIO wake | 🟠 WIP | Timer/GPIO wake paths exist; acceptance needs retention, wake-cause, and resumed-device results |

The sleep protocol definitions now agree across Linux, LP firmware, and OpenSBI.
The previously documented protocol mismatch is resolved in the source. Board
validation of suspend-to-RAM and LP GPIO wake remains outstanding. No board-current
measurement is provided here. See [Power management](../api-guides/power-management.md)
for commands and wake-source settings. Source references:
[Linux sleep structure](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/soc/espressif/esp32s31-lp-protocol.h),
[OpenSBI validation](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c).

## Radio

| Feature | Availability | Notes |
|---|---|---|
| Wi-Fi station | 🟢 Included | Single-station mac80211/cfg80211, `iw`, and `wpa_supplicant`; runtime validation pending |
| Bluetooth | 🟢 Included | BTstack with direct HCI; an alternate Linux HCI frontend exists |
| AP and AP+station | 🔴 Absent | Current SoftMAC frontend exposes only a station interface |
| Protected AP | 🔴 Absent | AP mode is not exposed by the current Linux frontend |
| Enterprise authentication | 🟠 WIP | Needs current station-stack acceptance; no firmware EAP vendor interface is exposed |
| Active Wi-Fi suspend/recovery | 🟠 WIP | Running interface vetoes suspend with `EBUSY`; replay/reassociation is not established |

The supplied root filesystem uses BTstack. Trying BlueZ also requires selecting
the Linux HCI frontend and changing the rootfs package/post-build settings:
the current post-build script removes BlueZ, D-Bus, and related library files.
Selecting a BlueZ package alone is insufficient. A complete BlueZ setup is not
validated here. See the [post-build removal rules](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/post-build.sh).

For the available setup paths, see
[Wi-Fi and Bluetooth](../api-reference/radio/index.md) and
[Advanced Wi-Fi](../api-guides/wifi-advanced.md).

## Peripherals

| Feature | Availability | Notes |
|---|---|---|
| GPIO and UART0 console | 🟢 Included | GPIO character device and the UART0 console |
| Optional UARTs | 🟡 Implemented | UART1/2 routes and UART3 DMA; the supplied UART3 HIL cases use internal loopback |
| I2C0/I2C1 | 🟡 Implemented | Long-transfer batching exists; validate the transfer lengths and device used by your application |
| GPSPI2/GPSPI3 host | 🟡 Implemented | 8-bit words; data-lane settings depend on the controller and selected device |
| GPSPI target | 🟡 Implemented | DMA transfers up to 4096 bytes |
| I2S/TDM | 🟡 Implemented | Playback/capture and configurable framing; supplied overlays consume external BCLK/WS |
| SD/MMC | 🟡 Implemented | Slot wiring and bus width selected by overlay; card and mode coverage need fixture results |
| Ethernet | 🟡 Implemented | Requires matching external PHY configuration and wiring |
| USB gadget | 🟡 Implemented | Requires the full-peripheral build and a configured gadget function; outside the standard HIL suite |
| USB host | 🟢 Included | Host controller and storage support are selected by default; device interoperability remains WIP |
| AHB/AXI GDMA | 🟡 Implemented | Used by peripheral drivers; AXI GDMA needs the full-peripheral build |
| Timers, PWM, and pulse counter | 🟡 Implemented | Timer 1 in each timer group is reserved for CPU idle |
| Analog and sensor blocks | 🟡 Implemented | ADC/DAC/touch/comparator through IIO; temperature through hwmon; accuracy/calibration need separate validation |
| Watchdog, NVMEM, RNG, and crypto | 🟡 Implemented | Integrated with their Linux subsystems; each needs its own functional acceptance |
| TWAI/CAN | 🟠 WIP | SocketCAN binding and overlays exist; board/bus acceptance remains incomplete |
| RMT | 🔴 Absent | No ESP32-S31 driver or device-tree node in the repository |

See [Using peripherals](../user-guides/peripherals.md) for setup,
[Peripheral reference](../api-reference/peripherals/index.md) for API settings
and transfer limits, and [Modules and boards](../hw-reference/modules-and-boards.md)
for default GPIO assignments. The [overlay catalog](overlay-catalog.md) lists
the controller selections.

## Testing and current validation limits

The project includes host tests and board/peer test programs. The HIL
`usb-drive` case covers host storage; it does not cover gadget functions or
all USB device classes. See [HIL testing](../contribute/testing-hil.md) for
commands, fixture setup, and result collection.

Acceptance of the current compact image requires a raw run identifying the
image/commit, board and module revision, fixture wiring, transfer settings,
result and cleanup evidence. Keep failures and skipped cases in the record.
Source contracts, old image reports and a recovery console do not establish
current hardware behavior.

### Flash and persistent storage

NOR programming and JFFS2 failures can affect saved settings or startup.
Persistent-flash erase and normal writable-root startup require validation
on the merged image; physical-board acceptance is still outstanding. When reporting a failure, include
the boot log, image identity and triggering operation, including any
`esp32s31-flash: ROM ... failed` or
`S31 overlay: failed to mount persist as JFFS2` message.
