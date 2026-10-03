# Build from source

Ubuntu 24.04 LTS on x86-64 Linux is the reference build platform. The pinned
prebuilt Linux toolchain is an x86-64 Linux executable. Other Linux
distributions need compatible development tools and libraries; another host
architecture requires a suitable source-built toolchain. Native Windows and
macOS source builds are not covered here.

Before you start building for the ESP32-S31 Linux port, make sure you have the following prerequisites. 

- A relatively recent Linux distribution.
- Sufficient free disk for the source history, toolchain, ESP-IDF tools/download
  cache, and build outputs. Do not treat 10 GiB as a verified full-build minimum;
  usage depends on clone depth and retained toolchain/package caches. Check
  available space with `df -h` before building and leave room for temporary
  downloads and rebuilds.
- Modest amount of RAM (8+ GiB recommended).

## 1. Clone the Repository

Clone the ESP32-S31 Linux port repository and initialize its pinned submodules:

```sh
git clone --recurse-submodules https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
git submodule update --init --recursive
```

## 2. Install Development Tools and Libraries

The ESP-IDF environment installed below supplies `esptool` for image generation
and flashing. A separate global installation is not needed for a source build.
For flashing only, use the isolated installation in
[Flash and first boot](flash-and-first-boot.md).

### Build Essentials

These provide the essential development tools and libraries required to build and work with the ESP32-S31 Linux port. Install with

```sh
sudo apt-get update
sudo apt-get install -y \
  git curl wget file python3 python3-venv cmake \
  bison bc build-essential ccache cpio device-tree-compiler flex gperf \
  libffi-dev libssl-dev ninja-build python3-pkg-resources python3-pyelftools \
  python3-dev swig rsync unzip xz-utils mtd-utils squashfs-tools
```

---

### ESP-IDF

ESP-IDF is the official development framework for the ESP32 series of chips. LP and Radio firmwares in `esp32-s31-linux` depend on ESP-IDF's proprietary libraries and toolchain. 

Use the exact ESP-IDF revision in `configs/build-versions.mk`, not a moving
`master` branch or a version number alone. The current pin is
`a602e67b0bf9ee0806dc4e1df7afc9affedf5c33`. From the project root, install it
into a new directory:

```sh
export IDF_PATH="$HOME/esp-idf"
ESP_IDF_REF=$(sed -n 's/^ESP_IDF_REF := //p' configs/build-versions.mk)
git clone --filter=blob:none https://github.com/espressif/esp-idf.git "$IDF_PATH"
git -C "$IDF_PATH" checkout "$ESP_IDF_REF"
git -C "$IDF_PATH" submodule update --init --recursive
"$IDF_PATH/install.sh" esp32s31
```

If you already have an ESP-IDF installation, use a separate checkout or save
its local changes before switching revisions. `make idf-check` rejects a
checkout that differs from the pin. `S31_ALLOW_UNPINNED=1` is an explicit
experimental override, not the reproducible build path.

Espressif's [ESP32-S31 installation guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/get-started/index.html#installation)
provides platform setup help; retain this project's pinned revision when
following it.

### Custom Toolchains

A fork of espressif's `crosstool-ng` is used to build custom toolchains for the ESP32-S31 Linux port. These custom toolchains contain optimizations specific to this port and the S31 chip.

Sources can be found on [GitHub](https://github.com/GrieferPig/crosstool-NG-s31). The release binaries are built via GitHub Actions. Download them to `cache/toolchains/riscv32-esp-linux-musl` by

```sh
make toolchain-fetch
```

The default release is pinned in `configs/build-versions.mk`
(`esp32s31-linux-gcc-15.2.0-5` at this revision). The target checks the downloaded
archive against the release's SHA-256 file. Use `TOOLCHAIN_RELEASE_TAG=local`
only when deliberately testing an already installed custom toolchain.

## 3. Build the Project

Activate ESP-IDF in your terminal:

```sh
export IDF_PATH="$HOME/esp-idf" # Replace with the path to your ESP-IDF installation if different
. "$IDF_PATH/export.sh"
```

Build the complete image on the host:

```sh
make doctor
make fetch
make image
```

`image` builds the boot firmware, kernel, rootfs, radio XIP image, and combined
flash image, verifies the paired artifacts, and publishes them atomically to `dist/`.
`all` is a compatibility alias for `image`. It does not access a serial port or flash a board. The default is
the full board configuration with all peripheral drivers. Set `JOBS`, for example `make JOBS=4 all`, to limit parallel compilation.
See [Build configuration](build-configuration.md).

To build a particular component, use

```sh
make uboot
make linux
make rootfs
```

To update a connected board already using the compact layout while preserving
its persist partition, select the port explicitly:

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

This target verifies and writes the immutable `dist/current` set without rebuilding. Complete
`make image` first, before flashing. Partial update targets are disabled because the installed companion
identities are unknown. `make build-flash` explicitly combines build and flash. For first
installation, data backup, and release-image updates, see
[Flash and first boot](flash-and-first-boot.md).


## 4. Build output

| Path under `out/images/` | Content |
|---|---|
| `u-boot-spl-dtb.bin` | SPL with its DTB |
| `spl_app.bin` | ESP ROM image wrapper around SPL |
| `u-boot.itb` | FIT containing OpenSBI, U-Boot proper and associated data |
| `esp32s31_generic.dtb` | Linux device tree |
| `xipImage` | Flash-XIP Linux kernel |
| `rootfs.sqfs` | SquashFS root filesystem |
| `radio.bin` | Prelinked flash-XIP radio payload; paired with this build's kernel |
| `s31_full_flash.bin` | Combined installation image; overwrites persist |
| `radio.json` | Build-time kernel/module/payload/import binding and radio hash |
| `build-manifest.json` | Source, configuration, toolchain, artifact hashes and build provenance |
| `SHA256SUMS` | Checksums for the release artifacts |
| `persist.jffs2` | Empty JFFS2 image, produced only by `make persist`; destructive flashing requires a separate maintenance procedure |

For more build targets, see the [Make reference](../resources/make-reference.md).

Native build trees live beside `images/`: `linux/`, `opensbi/`, `u-boot/`,
`idf-radio/`, `radio/`, `lp/`, and `buildroot/`. Shared downloads and toolchains
are under `cache/`; `make clean` only removes the build output.

Host-specific settings belong in the ignored `local.mk`, for example:

```make
IDF_EXPORT := /opt/esp-idf/export.sh
JOBS := 4
```

An explicitly requested `ROOTFS_BASELINE=/absolute/path/to/rootfs.sqfs` build
repackages a verified existing rootfs with the current radio module. Its manifest
records incremental provenance, validates the full runtime inventory and module
list, and rejects incomplete userspace. With explicit `ROOTFS_BUSYBOX_BUILD`
evidence it can restore only missing stock logging/cron init scripts from pinned
sources. Inherited binaries retain their original optimization. This is not a
clean Buildroot rebuild and does not validate unrelated rootfs source changes.
