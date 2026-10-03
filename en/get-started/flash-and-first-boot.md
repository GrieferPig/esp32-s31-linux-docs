# Flash and first boot

This guide installs a release image and opens the serial console. The supplied
configuration targets 16 MiB flash and 16 MiB PSRAM; check your board's memory,
connections, and download procedure against [Modules and boards](../hw-reference/modules-and-boards.md).

## 1. Install `esptool`

For standalone release-image flashing, use Python 3.10 or newer and an
`esptool` 5.x release at least as new as 5.3.0. That release added the S31 stub
flasher and fixes for S31 flash commands; see the
[esptool release notes](https://github.com/espressif/esptool/releases/tag/v5.3.0).
The following virtual environments keep this installation separate from the
ESP-IDF environment used for [source builds](build-from-source.md).

### Install on Linux

On Ubuntu, install `python3` and `python3-venv` first if they are missing.
Then run:

```sh
python3 -m venv "$HOME/s31-flash-env"
. "$HOME/s31-flash-env/bin/activate"
python -m pip install --upgrade "esptool>=5.3,<6"
python -m esptool version
```

Activate this environment again when opening a new terminal.

### Install on Windows (PowerShell)

Install Python 3.10 or newer with the Python launcher, then run:

```powershell
py -3 -m venv "$env:USERPROFILE\s31-flash-env"
$S31_PYTHON = "$env:USERPROFILE\s31-flash-env\Scripts\python.exe"
& $S31_PYTHON -m pip install --upgrade "esptool>=5.3,<6"
& $S31_PYTHON -m esptool version
```

Keep this PowerShell session open for the commands below. In a new session,
set `S31_PYTHON` to the same path again. Espressif's
[installation guide](https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html)
covers other installation methods.

## 2. Connect the board

Connect the board's download/console port and identify its serial device.
Examples below use `/dev/ttyUSB0` on Linux and `COM3` on Windows; replace them
with your actual port. The USB bridge and board wiring determine the device
name and whether automatic download/reset works. Close other serial programs
before flashing.

## 3. Install a release image

Download `s31_full_flash.bin` from the project's
[releases](https://github.com/GrieferPig/esp32-s31-linux/releases), using the
release tag to identify its source revision. The current release workflow
publishes only that combined image; it verifies the complete matched set in CI
but does not attach the component images, manifest or `SHA256SUMS`.

If a release explicitly supplies a checksum file as well, verify it before
flashing: on Linux use `sha256sum --check --ignore-missing SHA256SUMS`; on Windows
use `Get-FileHash .\s31_full_flash.bin -Algorithm SHA256` and compare with the
expected value. Stop on a mismatch. A locally calculated hash alone cannot
verify the download without a trusted expected hash. Run the following commands
from the download directory.

> **Warning:** The commands below erase the entire flash chip, including saved
> settings. Keep a verified backup on another device first. Flashing the combined image also overwrites the persist region
> even if the explicit erase step is omitted. For an update that keeps that
> region, use the complete matched slot-image procedure below, only when the
> installed layout matches. Layout changes require backup, clean installation
> and restoration of needed files/settings.

### Flash on Linux

```sh
PORT=/dev/ttyUSB0
python -m python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
python -m python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x0 s31_full_flash.bin
```

### Flash on Windows (PowerShell)

```powershell
$PORT="COM3"
& $S31_PYTHON -m python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
& $S31_PYTHON -m python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash `
  --flash-mode dio --flash-freq 80m --flash-size 16MB `
  0x0 s31_full_flash.bin
```

If automatic download or reset is unavailable, use the board's documented
buttons to enter download mode and reset it after flashing. If transfers fail,
try a lower flashing baud rate, such as `921600`.

## 4. Open the console and log in

Open the serial port in a terminal program with these settings:

| Setting | Value |
|---|---|
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |

Use these source-defined boot messages to identify stages; optional banners
may vary.

| Landmark | What it indicates |
|---|---|
| `ESP32-S31 SPL active` | SPL has entered board initialization |
| `OpenSBI` banner | M-mode firmware has reached its banner output, if enabled |
| `Starting kernel ...` | U-Boot is handing control to Linux |
| `Linux version` | The kernel has started printing its version banner |
| `S31 SMP: cpu1 online` | Linux has confirmed the second HP CPU is online |
| `esp32-s31 login:` | The default hostname's serial login is available |

For the default source configuration, log in as **`root` with no initial
password**. A source customization or an existing persist partition can change
those credentials.

After logging in, check the running kernel, CPUs, root mount, and startup:

```sh
uname -r
cat /sys/devices/system/cpu/online
grep ' / ' /proc/mounts
test -e /run/rcS.done && echo "rcS finished" || echo "rcS still running"
cat /run/rcS.log
```

Hardware boot/flashing acceptance of the current compact image is pending.
Runtime boot, persistence and LP readiness have not been validated on the merged
image. A recovery login does not establish a normal writable-root boot.
Set a password with `passwd` before exposing login services. The standard image
has no SSH server.

The configured kernel is based on Linux 6.18; the release suffix may vary.
The normal two-CPU result is `0-1`, and a successful writable-root setup shows
an `overlay` mount at `/`. Early `S31 overlay:` errors can leave a recovery
login on the read-only SquashFS root.

The login prompt can appear while board services are still starting in the
background. `/run/rcS.done` means the startup sequence finished, not that every
service succeeded. Inspect `/run/rcS.log` for service errors and use `dmesg` for
kernel messages.

## 5. Configure the board

Run the configuration menu:

```sh
esp32-config
```

Use **Network** to connect Wi-Fi, **Bluetooth** for Bluetooth setup, and
**Interfaces** for GPIO and peripherals. **System** contains the hostname,
login password, time, and startup program. Configuration is saved under `/etc/esp32-conf` when the
writable root is mounted. See [Board configuration](../resources/esp32-config.md)
for individual settings and status commands.

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

### If a complete component set is supplied

The current release workflow publishes only the combined installation image,
which cannot preserve persist. Use a [source build](#use-a-source-build) for a
normal preserve-data update. If a release explicitly provides all six slot
images and their `SHA256SUMS`, verify them together as above. Keep the set
matched: the radio XIP payload is linked against that kernel's addresses.
From the directory containing that complete set, run on Linux:

```sh
PORT=/dev/ttyUSB0
python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x002000 spl_app.bin 0x00E000 u-boot.itb 0x05E000 esp32s31_generic.dtb \
  0x06E000 radio.bin 0x400000 xipImage 0xA00000 rootfs.sqfs
```

For PowerShell, set `$PORT="COM3"`, replace `python -m esptool` with
`& $S31_PYTHON -m esptool`, and replace continuation backslashes with backticks. Do not run `erase-flash` for this same-layout update. It leaves
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
python -m esptool --chip "$CHIP" -p "$PORT" -b 2000000 write-flash \
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
