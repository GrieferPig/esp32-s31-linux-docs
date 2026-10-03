# Debugging

Start with the serial console and `dmesg`. Together they show the bootloader
output, driver messages, and errors from the running Linux system.

## Read the logs

Connect to UART0 at 115200 baud, 8N1, then run:

```sh
dmesg
```

Service startup messages are saved separately:

```sh
cat /run/rcS.log
cat /run/rcS.status
```

Services start alongside the login console. The file `/run/rcS.done` appears
when the startup scripts have finished. If a device is missing immediately
after login, check whether startup is still in progress.

Copy useful logs to your computer before resetting the board; `/run` and the
kernel log are cleared at reboot.

## Check the system

These commands give a useful overview:

```sh
uname -a
cat /sys/devices/system/cpu/online
cat /proc/meminfo
cat /proc/interrupts
cat /proc/mtd
cat /proc/mounts
s31-overlay status
```

`online` normally shows `0-1`. The interrupt counters help identify whether a
device is generating interrupts. `/proc/mounts` shows the writable root overlay
and any attached storage.

## Common problems

### The board does not boot

Check the power supply, USB cable, serial port, and boot-mode buttons. Close
other serial monitors before using `esptool`. After flashing, reset the board
into normal boot mode.

If the console stops at ROM or SPL, check the bootloader image and flash
offsets. If Linux starts but cannot mount its root filesystem, check the DTB,
kernel, and rootfs images. The commands in
[Flash and first boot](../get-started/flash-and-first-boot.md) write these to
the expected locations.

### Settings disappear after reboot

Look for JFFS2 or OverlayFS errors in the boot log and check `/proc/mounts`.
Linux can start with a read-only root when the persistent filesystem fails to
mount. Recovery provides volatile `/run`, `/tmp`, and `/var/log`, but persistent
settings are unavailable. The current emulator reaches recovery because
persistent-flash erase fails; a recovery login is not a persistence test.
Check available space with `df -h`; the persistent partition is small.

### A peripheral device is missing

Run `s31-overlay status` and check that the peripheral's overlay is active.
Then inspect `dmesg` for a failed probe or a missing clock, DMA channel, or
other dependency. The
[standard build](../get-started/build-configuration.md) includes the native
peripheral drivers; optional controllers still need their runtime overlays.

### An overlay command fails

Check the error message, `s31-overlay status`, and `dmesg`. A GPIO or controller
may already be used by another overlay or application. Stop that user before
changing the route.

If the error mentions saving or recording the overlay set, the hardware
change may already be active. Check the active and saved entries before
retrying. More details are in [Using overlays](../resources/overlay-catalog.md).

### Wi-Fi or Bluetooth fails to start

Use `esp32-config` to check the selected radio mode. Inspect `dmesg` for
firmware-loading errors and the radio's `radio_health` attribute for
initialization results. For Wi-Fi, also check `iw dev` and the station
manager's connection status. See the [radio reference](../api-reference/radio/index.md).

### An LP command fails

Run `s31-lpctl status`. A missing driver points to the `lp` overlay or kernel
configuration; `ready=0` points to firmware startup. Check `dmesg` for firmware
loading and mailbox errors. For suspend problems, see
[Power management](power-management.md).

## Report a problem

Include the command that failed, what you expected, and the relevant console
output. Add your board model, build or release version, and build configuration.
For a peripheral problem, include the wiring and the connected device. Remove
sensitive information from logs before sharing them.
