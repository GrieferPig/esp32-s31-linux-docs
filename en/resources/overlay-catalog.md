# Using overlays

Device-tree overlays enable optional peripherals and select their pins.
Use `s31-overlay` from the board's Linux console to list, apply, and remove
them.

## List the available overlays

```sh
s31-overlay list
s31-overlay status
```

`list` shows the overlays installed in the image. `status` shows the active
set and the settings saved for the next boot. Optional peripheral drivers
need the [full board configuration](../get-started/build-configuration.md).

| Group | Overlay names | Notes |
|---|---|---|
| UART | `uart1`, `uart2`, `uart3`, `uart3-dma` | DMA uses UHCI0 and AHB GDMA pair 0 |
| I2C | `i2c0`, `i2c1` | Separate controller and SCL/SDA routes |
| SPI | `gpspi2`, `gpspi2-target`, `gpspi3`, `gpspi3-target` | Choose host or target for each controller |
| Audio | `i2s0`, `i2s1` | I2S controller and audio routes |
| CAN | `twai0`, `twai1` | External CAN transceiver required |
| SD/MMC | `sdmmc0`, `sdmmc1`, `sdmmc-dual`, `sdmmc-uhs` | Variants share the SD/MMC host |
| Ethernet | `gmac` | External PHY and RGMII wiring |
| USB | `usb-device` | Switches the USB OTG controller to device mode |
| Timers | `timers` | Exposes timer 0 in each timer group |
| PWM/counter | `pwm-counter` | PWM and pulse-counter blocks |
| Analog | `analog` | Analog blocks and their pad selections |
| Watchdogs | `watchdogs` | Watchdog blocks |
| DMA | `gdma` | AHB GDMA pair 4 |
| Radio | `radio-wifi`, `radio-bluetooth`, `radio-combo` | Select one radio overlay |
| LP core | `lp` | LP remoteproc and mailbox |

## Apply an overlay

To enable I2C0 with its default settings:

```sh
s31-overlay apply i2c0
```

The tool applies the overlay immediately and saves the selection. For a
one-session experiment, add `--volatile`:

```sh
s31-overlay apply i2c0 --volatile
```

Use `status` to check the result, then use the peripheral's Linux interface.

## Select pins and parameters

Inspect the available settings first:

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
```

For example, to use GPIO35 for SCL, GPIO36 for SDA, and a 400 kHz bus:

```sh
s31-overlay apply i2c0 i2c0.scl=35 i2c0.sda=36 clock-frequency=400000
```

Route keys come from the overlay. The following numeric parameters are
provided by the standard catalog:

| Overlays | Parameter | Allowed values |
|---|---|---|
| `i2c0`, `i2c1` | `clock-frequency` | `100000`, `400000`, `1000000` |
| SD/MMC variants | `bus-width` | `1`, `4` |

The manager checks for overlapping GPIOs, input routes, and controller or DMA
resources. Flash and console pins are reserved. The
[board guide](../hw-reference/modules-and-boards.md) explains what to check
before wiring an external device.

The generic overlay manager applies these pin restrictions:

| GPIOs | Restriction |
|---|---|
| 26–32 | Live XIP flash bus; cannot be reassigned |
| 33, 34, 41 | Rejected by the manager's valid-pin filter |
| 58, 59 | Reserved for the live UART0 console |
| Outside 0–61 | Outside the driver's GPIO range |

Other pins still depend on board/module availability, active overlays, and
GPIO character-device consumers. This table describes software restrictions,
not a carrier-board connector map. Inspect `s31-overlay routes NAME` and the
board schematic before wiring.

## Remove or restore overlays

Close applications using the peripheral, then remove its overlay:

```sh
s31-overlay remove i2c0
```

Use `remove --all` to remove the managed set. Both forms save the resulting
selection unless `--volatile` is supplied.

Saved overlays are restored automatically at boot. To reload that saved set
manually, run:

```sh
s31-overlay restore
```

This removes the current set and applies the saved entries, interrupting any
peripherals involved. USB role changes also restart the USB controller;
unmount attached USB storage and disable USB-backed swap first.

## Saved settings and troubleshooting

Overlays are loaded through `/dev/s31-overlay`. Their files are stored under
`/usr/lib/s31-overlays`, with saved settings in
`/etc/esp32-conf/overlays.conf` and the current selection in
`/run/s31-overlay.current`.

If an operation fails, check `s31-overlay status` and `dmesg`. A save error can
leave the new overlay active, while a failed replacement can leave the old
one unavailable.

`--volatile` skips saving for that command. A later command that saves the
current set can include an overlay previously applied with `--volatile`.
