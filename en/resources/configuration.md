# Configuration

Use `esp32-config` on the board to configure everyday settings:

```sh
esp32-config
```

The dialog interface manages the board's system, Wi-Fi, Bluetooth, and
peripheral selections. Saved settings are stored in `/etc/esp32-conf` and
applied by the startup scripts.

## Choose where to make a change

| Change | Where to configure it |
|---|---|
| Include a driver | Kernel defconfig and build profile |
| Include an application | Buildroot defconfig or external package |
| Enable a peripheral or change its pins | `s31-overlay` |
| Configure Wi-Fi or Bluetooth | `esp32-config` and the radio tools |
| Change CPU frequency | Linux cpufreq interface |
| Change a peripheral's runtime settings | Its Linux subsystem API |
| Change the flash partition layout | Layout configuration, bootloader, and device tree |

For build-time choices, see [Build profiles](../get-started/build-profiles.md).
For runtime peripheral selection, see [Using overlays](overlay-catalog.md).

## Persistent files

The root filesystem combines the read-only SquashFS image with a writable
JFFS2 layer. Files written to the root filesystem normally survive a reboot.
This includes `/etc/esp32-conf` and Bluetooth pairing data in
`/var/lib/btstack`.

The following locations are temporary:

| Path | Typical contents |
|---|---|
| `/run` | Service state, process IDs, and startup logs |
| `/tmp` | Temporary files |
| `/var/log` | Runtime logs |

The persistent partition has 640 KiB of space. Use an SD card or USB storage
for applications, media, and large logs.

## Keep settings during an update

Use the separate-image flashing procedure or `make flash-all` to update the
firmware while preserving the persistent partition. Flashing
`s31_full_flash.bin`, running `make flash-persist`, or erasing the whole chip
replaces the saved data. See
[Flash and first boot](../get-started/flash-and-first-boot.md).

## Radio settings

Radio mode is selected when the module loads. The module parameters `mode`,
`direct_hci`, and `firmware` choose the Wi-Fi/Bluetooth profile, Bluetooth
frontend, and firmware file. Use the configuration tools for normal setup;
changing these module parameters requires a reload after stopping radio
applications.

See the [radio reference](../api-reference/radio/index.md) for the parameter
values and Linux interfaces.

## Troubleshooting saved settings

If changes disappear after a reboot, check `df -h`, `/proc/mounts`, and the
boot log for storage errors. Linux may start with a read-only root when the
persistent layer cannot be mounted.

For overlays, `s31-overlay status` displays both active and saved selections.
The live hardware change happens before the selection is saved, so a full
persistent filesystem can cause a save error even when the peripheral is
already enabled.
