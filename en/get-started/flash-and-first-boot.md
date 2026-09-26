# Flash and first boot

This guide shows how to install a release image, open the serial console,
and configure the board. You need an ESP32-S31 board with at least 16 MiB flash and
16 MiB PSRAM.

## 1. Install `esptool`

`esptool` is a Python utility used for flashing firmware onto ESP32 devices. If you don't have already, install `esptool` via

```bash
pip install esptool # add --break-system-packages if your system package manager manages python packages
```

Installing `esptool` globally is recommended, as it'll come in handy in multiple places during the development process.


## 2. Connect the board

Connect the board's download/console USB port to your computer and find its
serial device. The examples below use `/dev/ttyUSB0`. Replace it with your
board's port.

Typical device names are `/dev/ttyUSBx` on Linux and `COMx` on Windows.

## 3. Install a release image

Download `s31_full_flash.bin` from the project's
[releases](https://github.com/GrieferPig/esp32-s31-linux/releases).
Run the following commands from the download directory:

> **Warning:** Installing the combined image erases everything in flash. Back up
> anything you need before continuing. For an existing Linux update that keeps settings,
> use the source-build method below.

### Linux
```sh
PORT=/dev/ttyUSB0
esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x0 s31_full_flash.bin
```

### Windows (PowerShell)
```powershell
$PORT="COM3"
esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash `
  --flash-mode dio --flash-freq 80m --flash-size 16MB `
  0x0 s31_full_flash.bin
```

The board should restart when flashing finishes. If it does not enter download
mode automatically, use the download and reset buttons described in your
board's instructions. If transfers fail, try a lower flashing baud rate.

## 4. Open the console

Open the serial port in your terminal program with these settings:

| Setting | Value |
|---|---|
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |

You should see the bootloader and Linux messages, followed by a login prompt.

## 5. Configure the board

Run the configuration menu:

```sh
esp32-config
```

Use it to select the radio mode and configure Wi-Fi, Bluetooth, and other
board settings. Configuration is saved under `/etc/esp32-conf`.

For peripheral setup, continue with the
[overlay catalog](../resources/overlay-catalog.md). For boot problems, see
[Debugging](../api-guides/debugging.md).

## 6. Update a source-built system

After [building the project](build-from-source.md), use this command for a
board on `/dev/ttyUSB0`:

```sh
make flash-all
```

It writes SPL, U-Boot/OpenSBI, the Linux device tree, radio firmware, the kernel,
and the root filesystem, while leaving the persist partition in place.

Alternatively, you can flash individual components manually using `esptool` as shown below.

```sh
PORT=/dev/ttyUSB0
. configs/esp32s31-layout.cfg
esptool --chip "$CHIP" -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  "$SLOT_SPL" "build/$SPL_APP_BIN" \
  "$SLOT_UBOOT_ITB" "build/$UBOOT_ITB" \
  "$SLOT_DTB" "build/$BASE_DTB" \
  "$SLOT_RADIO" "build/$RADIO_IMAGE" \
  "$SLOT_KERNEL" "build/$KERNEL_IMAGE" \
  "$SLOT_ROOTFS" "build/$ROOTFS_IMAGE"
```

The individual component targets are
listed in the [Make reference](../resources/make-reference.md).
