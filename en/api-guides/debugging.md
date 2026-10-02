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
test -e /run/rcS.done && cat /run/rcS.status
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

Capture output from reset and use the last completed stage to choose the next
check. These messages provide useful landmarks:

| Output | What it establishes | Next check |
|---|---|---|
| `ESP32-S31 SPL active` | SPL reached its board initialization | Read the following memory and image-loading messages; see [Boot process](../api-reference/system/boot-chain.md). |
| `S31 overlay: failed to mount persist as JFFS2` | Linux reached early userspace but could not mount writable storage | Follow [Configuration](../resources/configuration.md). |
| `S31 early overlay restore failed` | Restoring saved device-tree overlays returned an error | Inspect active overlays and saved selections using [Using overlays](../resources/overlay-catalog.md). |
| A serial login prompt | Linux started the console login service | Check `/run/rcS.log` and `/run/rcS.done` for services still starting. |

### Settings disappear after reboot

Check `df -h`, `/proc/mounts`, and the boot log for storage errors. Follow
[Configuration](../resources/configuration.md) for persistence, capacity, and
read-only fallback behavior. If only an overlay selection is missing, compare
the `active:` and `persisted:` entries in `s31-overlay status`.

### A peripheral device is missing

Run `s31-overlay status` and check that the peripheral's overlay is active.
Then inspect `dmesg` for a failed probe or a missing clock, DMA channel, or
other dependency. Optional peripherals need the
[full-peripheral build](../get-started/build-profiles.md).

### An overlay command fails

Check the error message, `s31-overlay status`, and `dmesg`. A GPIO or controller
may already be used by another overlay or application. Stop that user before
changing the route.

Check both active and saved entries before retrying. The error-specific checks,
including save failures and replacement rollback, are in
[Using overlays](../resources/overlay-catalog.md).

### Wi-Fi or Bluetooth fails to start

Start with the service status:

```sh
esp32-config wifi status
esp32-config bluetooth info
```

Inspect `dmesg` for firmware-loading errors and the radio's `radio_health`
attribute for initialization results. A loaded module can still have a failed
device probe or missing frontend. The [radio reference](../api-reference/radio/index.md)
shows how to read its health state.

For Wi-Fi, check `iw dev` and `wpa_cli -i wlan0 status`. If association
completes but DHCP remains pending, inspect
`/run/esp32-config/udhcpc.wlan0.log`. The normal connection procedure is in
[Network setup](../user-guides/networking.md).

### An LP command fails

Run `s31-lpctl status`. A missing driver points to the `lp` overlay or kernel
configuration; `ready=0` points to firmware startup. Check `dmesg` for firmware
loading and mailbox errors. For suspend problems, see
[Power management](power-management.md).

## Report a problem

Include the command that failed, what you expected, and the relevant console
output. Add your board model, build or release version, and build profile.
For a peripheral problem, include the wiring and the connected device. Remove
sensitive information from logs before sharing them.
