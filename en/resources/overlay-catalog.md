# Using overlays

Device-tree overlays enable optional peripherals and select their pins.
Use **Interfaces** in `esp32-config` to select an interface and edit its pins
and parameters. The page separates the current enabled state from the saved
startup choice and marks saved field values when they differ. **Unavailable**
means the current state could not be read. You can edit an enabled interface
directly; fixed pins are shown without an editable field.

Choose **Enabled** to show the parameter fields, then **Save and apply** to
update the interface and its startup selection. Saving **Disabled** removes
that interface's saved settings. Saving values that already match both current
and saved settings leaves the interface running without reapplying it.

The `s31-overlay` command provides the same overlay operations for scripts.

## List the available overlays

```sh
s31-overlay list
s31-overlay status
```

`list` shows the overlays installed in the image. In `status`, `active:`
entries come from the running kernel; `persisted:` lists the desired selections
saved for the next boot. Optional peripheral drivers are included in the
standard [full board configuration](../get-started/build-configuration.md);
the overlays and physical hardware still need configuration.

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

The tool applies the overlay immediately and saves that named selection.
For a temporary change that leaves saved settings alone, add `--volatile`:

```sh
s31-overlay apply i2c0 --volatile
```

Use `status` to check the result, then use the peripheral's Linux interface.

## Select pins and parameters

Inspect the available settings first:

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
s31-overlay describe i2c0
```

`routes` and `parameters` show the installed overlay's defaults and available
choices. `describe` reports defaults, current values, and saved values separately
as tab-separated records. If an active overlay's current parameters are not
known, `current_known` is `0` and current-value fields contain `-`. Fixed GPIO
claims are reported as `fixed_gpio` records. If current pin values cannot be
read, the menu asks you to disable the interface before configuring it again.

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
before wiring an external device and lists the default routes.

## Remove or restore overlays

Close applications using the peripheral, then remove its overlay:

```sh
s31-overlay remove i2c0
```

This also clears a saved selection when the overlay is already inactive.

Use `remove --all` to remove all managed overlays. Successful commands update
the active and saved selections as follows:

| Command | Active overlays | Saved selections |
|---|---|---|
| `apply NAME` | Apply or replace `NAME` | Add or replace only the `NAME` entry |
| `remove NAME` | Remove `NAME` | Remove only the `NAME` entry |
| `remove --all` | Remove all managed overlays | Clear all saved entries |
| Any of the above with `--volatile` | Make the same active change | Leave saved entries unchanged |

A later normal command keeps unrelated saved entries as they were. For example,
applying `uart1` with `--volatile`, then applying `uart2` normally, saves only
the `uart2` change. Conversely, removing a saved overlay with `--volatile`
leaves its next-boot selection in place.

Saved overlays are restored automatically at boot. To reload that saved set
manually, run:

```sh
s31-overlay restore
```

When the saved file exists and can be read, `restore` removes the current set
and applies the saved entries, interrupting the peripherals involved. An empty
file clears the active set. If the file is absent, the command succeeds and
leaves active overlays unchanged; an invalid or unreadable file causes it to
stop before changing them.

To check a saved overlay file against the installed catalog without changing
hardware, run `s31-overlay check /etc/esp32-conf/overlays.conf`. This validates
the file, overlay names, and parameters; active pin/resource conflicts are
checked when applying it.

USB role changes also restart the USB controller;
unmount attached USB storage and disable USB-backed swap first.

## Saved settings and troubleshooting

Overlays are loaded through `/dev/s31-overlay`. Their files are stored under
`/usr/lib/s31-overlays`, with saved settings in
`/etc/esp32-conf/overlays.conf`. The CLI records its runtime selections in
`/run/s31-overlay.current`; `status` queries the kernel for the active set.
See [Configuration](configuration.md) for storage capacity and file lifetime.

If an operation fails, inspect its error, `s31-overlay status`, and `dmesg`:

| Failure | What to check |
|---|---|
| Preparing the persistent set fails | Check the saved file's syntax and readability. The command stops before changing active overlays. |
| Replacing an active overlay fails | The kernel attempts to reapply the previous overlay. If that rollback also fails, the previous overlay is lost; look for a rollback error in `dmesg`. |
| `overlay applied, but recording state failed` or the corresponding removal error | The hardware change has already happened. Check active and saved selections separately, resolve the storage error, then repeat the intended command. |
| Applying an entry during `restore` fails | The CLI attempts to remove the partially restored set. It does not recreate the set that was active before `restore`; inspect the active set before continuing. |

`persisted: (none)` also appears when the saved file cannot be read or parsed.
If saved selections unexpectedly disappear from status, inspect
`/etc/esp32-conf/overlays.conf` and the storage checks in
[Configuration](configuration.md).
