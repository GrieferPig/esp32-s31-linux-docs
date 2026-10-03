# Memory and storage

Use **Memory & storage** in `esp32-config` to select swap and mount an existing
SD or USB volume. Run the commands below as root on the board.

## Use a swap partition

Connect a drive containing a swap partition, then choose **Swap settings →
Select device and enable**. The menu lists devices with an existing swap
signature. Selecting one enables it immediately and saves the selection for
startup.

The command-line equivalent is:

```sh
esp32-config storage swap enable /dev/sda1
esp32-config storage status
```

Replace `/dev/sda1` with the actual swap device. `UUID=<uuid>` is also accepted;
the menu uses the UUID when one is available so the setting can survive a
change in device numbering. To inspect the device names and current use:

```sh
cat /proc/partitions
cat /proc/swaps
```

To stop the swap enabled by the configuration tool and disable it at startup:

```sh
esp32-config storage swap disable
```

The tool leaves swap owned by another service alone. If `swapoff` fails, close
applications to release memory and try again; wait for a successful result
before removing the drive. The configuration tool does not format storage.

## Mount an SD or USB volume

Filesystem mounting is available when the running image includes the matching
filesystem driver. The standard [full board configuration](../get-started/build-configuration.md)
includes FAT/VFAT and built-in ext4 support. For SD cards, enable the appropriate SDMMC
interface and connect the card as described in [Use peripherals](peripherals.md).

Choose **Removable storage → Select volume and mount**, then select:

1. The existing volume.
2. An empty directory under `/mnt` or `/media`.
3. Read/write or read-only access.
4. Whether to mount it at startup.

The tool mounts the volume when you submit the settings. For example, to mount
an existing volume read/write at `/mnt/media` and restore it at startup:

```sh
esp32-config storage configure /dev/sda1 /mnt/media 1 0
```

The last two arguments mean `AUTOSTART` and `READONLY`, respectively; each is
`0` or `1`. Replace the device with your actual filesystem partition. The tool
manages one removable volume and saves its UUID when available. A missing drive
at boot is skipped; after connecting it, choose **Mount saved volume** or run:

```sh
esp32-config storage mount
```

## Unmount or change startup behavior

Close files and stop applications using the volume, then choose **Safely
unmount** or run:

```sh
esp32-config storage unmount
```

A successful unmount lets you disconnect that volume. Check `/proc/mounts`
and `/proc/swaps` for any other uses of the same drive before unplugging it.
Unmounting keeps the saved startup selection. To leave the volume mounted now
but stop mounting it automatically at boot:

```sh
esp32-config storage autostart 0
```

Choose **Current usage** or run `esp32-config storage status` to see saved
selections alongside the current mounts and swap. Configuration files and their
lifetime are listed in [esp32-config](../resources/esp32-config.md).
