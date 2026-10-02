# Configuration

Use `esp32-config` on the board to configure everyday settings:

```sh
esp32-config
```

The dialog interface manages system settings, networking, Bluetooth,
interfaces, GPIO, and memory/storage selections. Saved settings are stored in `/etc/esp32-conf` and
applied by the startup scripts.

## Choose where to make a change

| Change | Where to configure it |
|---|---|
| Include a driver | Kernel defconfig and build profile |
| Include an application | Buildroot defconfig or external package |
| Enable a peripheral or change its pins | `esp32-config` Interfaces or `s31-overlay` |
| Configure Wi-Fi, Bluetooth, GPIO, startup programs, or storage | `esp32-config` |
| Change CPU frequency | Linux cpufreq interface |
| Change a peripheral's runtime settings | Its Linux subsystem API |
| Change the flash partition layout | Layout configuration, bootloader, and device tree |

For build-time choices, see [Build profiles](../get-started/build-profiles.md).
For runtime peripheral selection, see [Using overlays](overlay-catalog.md).

## Persistent files

The root filesystem combines the read-only SquashFS image with a writable
JFFS2 layer using OverlayFS. Ordinary files written to this merged root survive
a reboot, including `/etc/esp32-conf` and Bluetooth pairing data in
`/var/lib/btstack`. Applications use these normal paths; the JFFS2 backing
store is assembled during early boot.

The following locations are temporary:

| Path | Typical contents |
|---|---|
| `/run` | Service state, process IDs, and startup logs |
| `/tmp` | Temporary files |
| `/var/log` | Runtime logs |

The persistent partition is **576 KiB**, with some space used by filesystem
metadata. The adjacent 64 KiB `hil-scratch` partition is reserved for tests.
Use an SD card or USB storage for larger applications, media, and logs. For
SD cards or FAT/VFAT/ext4-formatted drives, use the
[full-peripheral profile](../get-started/build-profiles.md) and enable the
required storage overlay.

Some firmware-owned files are refreshed from the image during boot. See
[Deploy files that must survive reboot](deploy-files-that-must-survive-reboot)
for those exceptions and the appropriate way to install replacements.

## Keep settings during an update

Use the separate-image flashing procedure or `make flash-all` to update the
firmware while preserving the persistent partition. Flashing
`s31_full_flash.bin`, running `make flash-persist`, or erasing the whole chip
replaces the saved data. See
[Flash and first boot](../get-started/flash-and-first-boot.md).

## Back up and restore settings

Choose **Maintenance → Export configuration** and enter a new `.tar` filename.
To put the backup on [mounted removable storage](../user-guides/memory-and-storage.md):

```sh
esp32-config maintenance backup /mnt/media/esp32-config-backup.tar
```

The backup contains the configuration tool's settings, including the saved
Wi-Fi credentials. Keep it private and copy it off the board before erasing
flash. It does not contain user programs, login passwords, Bluetooth pairing
keys, or files on mounted storage. Existing backup files are not overwritten.

Import through **Maintenance → Import configuration**, or run:

```sh
esp32-config maintenance restore /mnt/media/esp32-config-backup.tar
```

The tool checks the archive and its settings before replacing the saved
configuration. An import restores the complete snapshot of settings managed
by `esp32-config`; it does not merge individual fields with the current
settings. User files remain in place. Restart Linux to apply the restored
settings together; importing does not immediately stop the current program,
release GPIO, or disconnect the network.

## Reset configuration

Choose **Maintenance → Reset configuration** and select a group, or use:

```text
esp32-config maintenance reset network|bluetooth|interfaces|gpio|system|memory|all
```

Supply one group name. For example, to reset only the saved network settings:

```sh
esp32-config maintenance reset network
```

The defaults take effect after restarting Linux. Resetting `system` or `all`
preserves the login password. Bluetooth pairing keys also remain; use
[Clear saved pairings](../user-guides/networking.md) when you want to remove
those. Resetting configuration leaves user programs and other files intact.

## Radio settings

Radio mode is selected when the module loads. The module parameters `mode`,
`direct_hci`, and `firmware` choose the Wi-Fi/Bluetooth profile, Bluetooth
frontend, and firmware file. Use the configuration tools for normal setup;
changing these module parameters requires a reload after stopping radio
applications.

See the [radio reference](../api-reference/radio/index.md) for the parameter
values and Linux interfaces.

## If settings cannot be saved

Check `df -h`, `/proc/mounts`, and `dmesg` for available space and storage
errors. A normal boot has a writable OverlayFS root. If early boot cannot
find or mount persist, assemble OverlayFS, or switch to the merged root,
it prints an error and starts the read-only SquashFS base system. Saving
configuration then fails until writable storage is available again.

For overlay changes, check both the active and desired entries in
`s31-overlay status`. See [Using overlays](overlay-catalog.md) for save
failures, replacement rollback, and restoring the saved selection.
