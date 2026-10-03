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
| Include a driver | Kernel defconfig and build configuration |
| Include an application | Buildroot defconfig or external package |
| Enable a peripheral or change its pins | `s31-overlay` |
| Configure Wi-Fi or Bluetooth | `esp32-config` and the radio tools |
| Change CPU frequency | Linux cpufreq interface |
| Change a peripheral's runtime settings | Its Linux subsystem API |
| Change the flash partition layout | Layout configuration, bootloader, and device tree |

For build-time choices, see [Build configuration](../get-started/build-configuration.md).
For runtime peripheral selection, see [Using overlays](overlay-catalog.md).

## Persistent files

The root filesystem combines the read-only SquashFS image with a writable
JFFS2 layer. Files written to the root filesystem normally survive a reboot.
This includes `/etc/esp32-conf` and Bluetooth pairing data in
`/var/lib/btstack`.

Package-owned radio executables, selected startup scripts, and installed DTBO
names are exceptions: `/init` removes stale writable-layer copies during boot
so a rootfs update can supply the current versions. Make lasting customizations
in the source package/overlay, or use a new filename, rather than replacing
those packaged files on the running board.

The following locations are temporary:

| Path | Typical contents |
|---|---|
| `/run` | Service state, process IDs, and startup logs |
| `/tmp` | Temporary files |
| `/var/log` | Runtime logs |

The persistent partition has 2120 KiB of raw flash capacity; JFFS2 metadata
and live files reduce the usable space. Use an SD card or USB storage
for applications, media, and large logs.

## Keep settings during an update

On a board already using the compact layout, use the separate-image flashing
procedure or `make flash-all` to preserve the persistent partition. Whenever
changing the installed layout, back up data externally, perform a clean
installation, and restore needed files/settings. Flashing
`s31_full_flash.bin`, explicitly writing an empty persist image, or erasing the whole chip
replaces the saved data. See
[Flash and first boot](../get-started/flash-and-first-boot.md).

## Radio settings

Radio mode is selected when the module loads. The module parameters `mode`
and `direct_hci` choose the Wi-Fi/Bluetooth profile and Bluetooth frontend.
The XIP payload comes from the fixed radio flash slot, not a firmware filename
parameter. Use the configuration tools for normal setup;
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
