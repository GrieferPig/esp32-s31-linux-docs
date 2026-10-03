# Feature support

The standard [full board configuration](../get-started/build-configuration.md)
includes optional buses, audio, storage, and networking drivers.

## Availability labels

| Label | Meaning |
|---|---|
| 🟢 Included | The default build selects this support; runtime setup may still be required |
| 🟡 Implemented | A driver or protocol path exists |
| 🟠 WIP | Integration remains incomplete |
| 🔴 Absent | No ESP32-S31 implementation is provided in this repository |

These labels describe the [build configuration](https://github.com/GrieferPig/esp32-s31-linux/blob/main/Makefile)
and driver support.

## System

| Feature | Availability | Notes |
|---|---|---|
| Linux, Sv32 MMU, and flash XIP | 🟢 Included | Configured for 16 MiB flash and 16 MiB PSRAM |
| Dual-core SMP | 🟢 Included | Both HP harts are configured to run Linux |
| Persistent root filesystem | 🟢 Included | SquashFS with a JFFS2 writable layer |
| Removable storage and swap | 🟢 Included | FAT/VFAT, built-in ext4, SD/MMC, USB storage, and swap |
| Runtime overlays | 🟢 Included | Peripheral selection, pin routing, and saved settings |
| CPU frequency scaling | 🟢 Included | Shared 80, 160, 240, and 320 MHz policy |
| CPU idle | 🟢 Included | Firmware-assisted WFI |
| LP firmware and mailbox | 🟡 Implemented | remoteproc, PING/PONG, timer and GPIO diagnostics |
| Suspend-to-idle | 🟡 Implemented | The LP timer-wake diagnostic polls on the HP CPU |
| Timed deep sleep | 🟡 Implemented | Timed wake follows the cold-boot path |
| Normal poweroff | 🟡 Implemented | Does not arm timed wake; restart through external reset or a power cycle |
| Suspend-to-RAM and LP GPIO wake | 🟡 Implemented | Timer/GPIO wake paths exist |

Linux, LP firmware, and OpenSBI use matching sleep protocol definitions. See [Power management](../api-guides/power-management.md)
for commands and wake-source settings. Source references:
[Linux sleep structure](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/soc/espressif/esp32s31-lp-protocol.h),
[OpenSBI validation](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c).

## Radio

| Feature | Availability | Notes |
|---|---|---|
| Wi-Fi station | 🟢 Included | Single-station mac80211/cfg80211, `iw`, and `wpa_supplicant` |
| Bluetooth | 🟢 Included | BTstack with direct HCI; an alternate Linux HCI frontend exists |
| AP, AP+station, and protected AP | 🔴 Absent | These modes are not exposed by the current SoftMAC frontend |
| Software monitor | 🟠 WIP | Uses the station-filtered receive path; not full promiscuous capture |
| Enterprise authentication | 🟠 WIP | No firmware EAP vendor interface is exposed |
| Active Wi-Fi suspend/recovery | 🔴 Absent | A running interface vetoes suspend with `EBUSY`; active-link replay/reassociation is not implemented |

The supplied root filesystem uses BTstack. Trying BlueZ also requires selecting
the Linux HCI frontend and changing the rootfs package/post-build settings:
the current post-build script removes BlueZ, D-Bus, and related library files.
Selecting a BlueZ package alone is insufficient. See the [post-build removal rules](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/post-build.sh).

For the available setup paths, see
[Wi-Fi and Bluetooth](../api-reference/radio/index.md) and
[Advanced Wi-Fi](../api-guides/wifi-advanced.md).

## Peripherals

| Feature | Availability | Notes |
|---|---|---|
| GPIO and UART0 console | 🟢 Included | GPIO character device and the UART0 console |
| Optional UARTs | 🟡 Implemented | UART1/2 routes and UART3 DMA; the supplied UART3 HIL cases use internal loopback |
| I2C0/I2C1 | 🟡 Implemented | Long-transfer batching exists |
| GPSPI2/GPSPI3 host | 🟡 Implemented | 8-bit words; data-lane settings depend on the controller and selected device |
| GPSPI target | 🟡 Implemented | DMA transfers up to 4096 bytes |
| I2S/TDM | 🟡 Implemented | Playback/capture and configurable framing; supplied overlays consume external BCLK/WS |
| SD/MMC | 🟡 Implemented | Slot wiring and bus width selected by overlay |
| Ethernet | 🟡 Implemented | Requires matching external PHY configuration and wiring |
| USB gadget | 🟡 Implemented | The standard kernel includes ACM/ECM configfs support; select a function at runtime; outside the standard HIL suite |
| USB host | 🟢 Included | Host controller and storage support are selected by default |
| AHB/AXI GDMA | 🟡 Implemented | Both providers are built in and used by the corresponding peripheral drivers |
| Timers, PWM, and pulse counter | 🟡 Implemented | Timer 1 in each timer group is reserved for CPU idle |
| Analog and sensor blocks | 🟡 Implemented | ADC/DAC/touch/comparator through IIO; temperature through hwmon |
| Watchdog, NVMEM, RNG, and crypto | 🟡 Implemented | Integrated with their Linux subsystems |
| TWAI/CAN | 🟡 Implemented | SocketCAN binding and overlays exist |
| RMT | 🔴 Absent | No ESP32-S31 driver or device-tree node in the repository |

See [Using peripherals](../user-guides/peripherals.md) for setup,
[Peripheral reference](../api-reference/peripherals/index.md) for API settings
and transfer limits, and [Modules and boards](../hw-reference/modules-and-boards.md)
for default GPIO assignments. The [overlay catalog](overlay-catalog.md) lists
the controller selections.

## Testing

The project includes host tests and board/peer test programs. The HIL
`usb-drive` case covers host storage; it does not cover gadget functions or
all USB device classes. See [HIL testing](../contribute/testing-hil.md) for
commands, fixture setup, and result collection.

### Flash and persistent storage

The compact layout gives persist 2120 KiB and Linux/rootfs 6 MiB each, with no
HIL scratch partition. Only matched slot-wise updates of the same layout
preserve persist; back up externally before changing the layout.

NOR programming and JFFS2 failures can affect saved settings or startup.
When reporting a failure, include
the boot log, image identity and triggering operation, including any
`esp32s31-flash: ROM ... failed` or
`S31 overlay: failed to mount persist as JFFS2` message.
