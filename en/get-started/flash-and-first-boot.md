# Flash and first boot

This guide shows how to install a release image, open the serial console,
and configure the board. You need an ESP32-S31 board with at least 16 MiB flash and
16 MiB PSRAM.

## 1. Install `esptool`

`esptool` writes images to the board. Use a Python virtual environment to avoid
changing system packages or another SDK's dependencies. If you already use the
pinned ESP-IDF environment from [Build from source](build-from-source.md),
activate that environment instead.

On Linux:

```sh
python3 -m venv ~/.venvs/s31-esptool
. ~/.venvs/s31-esptool/bin/activate
python -m pip install esptool
```

On Windows PowerShell:

```powershell
py -m venv "$HOME\s31-esptool"
& "$HOME\s31-esptool\Scripts\python.exe" -m pip install esptool
$env:Path = "$HOME\s31-esptool\Scripts;$env:Path"
```

Run `esptool --help` and verify that `esp32s31` is an accepted chip before
flashing. See Espressif's [esptool installation guide](https://docs.espressif.com/projects/esptool/en/latest/esp32s31/installation.html).


## 2. Connect the board

Connect the board's download/console USB port to your computer and find its
serial device. The examples below use `/dev/ttyUSB0`. Replace it with your
board's port.

Typical device names are `/dev/ttyUSBx` on Linux and `COMx` on Windows.

## 3. Install a release image

Download `s31_full_flash.bin` and `SHA256SUMS` from the same project
[release](https://github.com/GrieferPig/esp32-s31-linux/releases). Keep
`build-manifest.json` with the images so you can identify their source and
toolchain. Verify the downloaded image before flashing:

```sh
# Linux; missing optional slot images are ignored, present files are checked.
sha256sum --check --ignore-missing SHA256SUMS
```

On Windows, run `Get-FileHash .\s31_full_flash.bin -Algorithm SHA256` and compare
the result with the `s31_full_flash.bin` entry in `SHA256SUMS`. Stop on a mismatch.
Checksums detect corruption; obtain both files from the intended release.
Run the following commands from the download directory:

> **Warning:** These installation commands erase everything in flash. Back up
> anything you need to another device before continuing. Writing the combined
> image also overwrites persist even if you omit `erase-flash`. The slot-image
> method below keeps persist only on a board already using the same layout.
> Whenever changing the installed layout, back up data, perform a clean
> installation, and restore the needed files/settings.

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

The bootloader and Linux print their startup messages on this console.
Hardware validation of this image is pending. The current emulator reaches a
recovery login because persistent-flash erase fails; persistent settings are
unavailable in recovery. See [Debugging](../api-guides/debugging.md).
The source defconfig enables a `root` console login with an empty password;
log in as `root` on an unmodified image. Set a password with `passwd` before
exposing login services. A customized image may use different credentials.
The compact rootfs does not enable an SSH server by default.

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

## 6. Protect persistent data

The persistent JFFS2 area is `[0x1EE000, 0x400000)`. An erased persist area is
a valid empty filesystem; no separate persist image is needed for a clean
installation. Whole-flash writes overwrite this area.

Keep an external, verified backup of important files and settings. Whenever
changing the installed layout, use the clean-install commands in section 3,
then restore the needed files/settings into the writable filesystem. Check
the installed image's [flash layout](../hw-reference/flash-layout.md) before
using the preservation procedure below.

## 7. Update without erasing saved settings

These procedures apply only to boards already using the compact layout above.
Keep an external backup of important data even for a same-layout update.

### Use release component images

Download all six slot images and `SHA256SUMS` from one release and verify them
as above. Keep the set together: the radio XIP payload is linked against that
kernel's addresses. From the download directory, run this on Linux:

```sh
PORT=/dev/ttyUSB0
esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x002000 spl_app.bin 0x00E000 u-boot.itb 0x05E000 esp32s31_generic.dtb \
  0x06E000 radio.bin 0x400000 xipImage 0xA00000 rootfs.sqfs
```

For PowerShell, set `$PORT="COM3"` and replace each line-continuation backslash
with a backtick. Do not run `erase-flash` for this same-layout update. It leaves
persist (`0x1EE000–0x400000`, 2120 KiB) untouched. Use all six images from one
release; there is no HIL scratch partition in this layout.

### Use a source build

After [building the project](build-from-source.md), run this from the source
repository, using the same build configuration as the original build:

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

It resolves the immutable `dist/current` set, verifies it, and writes SPL, U-Boot/OpenSBI, Linux device tree, radio firmware,
the kernel, and the root filesystem, while leaving the current persist slot in
place only when the installed layout matches. Override `PORT` and `BAUD`
for another connection.

For an explicit manual same-build slot-wise update, verify the build manifest
first and write the complete matching set:

```sh
PORT=/dev/ttyUSB0
IMAGES=out/images
python3 tools/release/manifest.py \
  --output-root out --verify "$IMAGES/build-manifest.json"
. configs/esp32s31-layout.cfg
esptool --chip "$CHIP" -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  "$SLOT_SPL" "$IMAGES/$SPL_APP_BIN" \
  "$SLOT_UBOOT_ITB" "$IMAGES/$UBOOT_ITB" \
  "$SLOT_DTB" "$IMAGES/$BASE_DTB" \
  "$SLOT_RADIO" "$IMAGES/$RADIO_IMAGE" \
  "$SLOT_KERNEL" "$IMAGES/$KERNEL_IMAGE" \
  "$SLOT_ROOTFS" "$IMAGES/$ROOTFS_IMAGE"
```

Partial component targets refuse unknown installed companions. Device targets are
listed in the [Make reference](../resources/make-reference.md).
