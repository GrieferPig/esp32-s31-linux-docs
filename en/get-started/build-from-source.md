# Build from source

For the sake of simplicity, Ubuntu 24.04 LTS is used as the reference platform, though other distributions should work as well if they have the necessary development tools and libraries installed. Other platforms such as Windows and macOS aren't supported currently.

Before you start building for the ESP32-S31 Linux port, make sure you have the following prerequisites. 

- A relatively recent Linux distribution.
- At least 10 GiB of free disk space for source, toolchain downloads and building artifacts.
- Modest amount of RAM (8+ GiB recommended).

## 1. Clone the Repository

Clone the ESP32-S31 Linux port repository and check out the specific commit used in this guide:

```sh
git clone --recurse-submodules https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
git submodule update --init --recursive
```

## 2. Install Development Tools and Libraries

### `esptool`

`esptool` is a Python utility used for flashing firmware onto ESP32 devices. If you don't have already, install `esptool` via

```bash
pip install esptool --break-system-packages
```

Installing `esptool` globally is recommended, as it'll come in handy in multiple places during the development process.

--- 

### Build Essentials

These provide the essential development tools and libraries required to build and work with the ESP32-S31 Linux port. Install with

```sh
sudo apt-get update
sudo apt-get install -y \
  git curl python3 python3-venv cmake \
  bison bc build-essential ccache cpio device-tree-compiler flex gperf \
  libffi-dev libssl-dev ninja-build python3-pkg-resources python3-pyelftools \
  rsync unzip xz-utils mtd-utils
```

---

### ESP-IDF

ESP-IDF is the official development framework for the ESP32 series of chips. LP and Radio firmwares in `esp32-s31-linux` depend on ESP-IDF's proprietary libraries and toolchain. 

ESP-IDF 6.2 is used in this port. Install with

```sh
export IDF_PATH="$HOME/esp-idf"
git clone https://github.com/espressif/esp-idf.git "$IDF_PATH"
"$IDF_PATH/install.sh" esp32s31
```

This will install ESP-IDF in `~/esp-idf`. Alternatively, you may use the official installation guide from Espressif: [ESP-IDF Getting Started Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/index.html#installation).

### Custom Toolchains

A fork of espressif's `crosstool-ng` is used to build custom toolchains for the ESP32-S31 Linux port. These custom toolchains contain optimizations specific to this port and the S31 chip.

Sources can be found on [GitHub](https://github.com/GrieferPig/crosstool-NG-s31). The release binaries are built via GitHub Actions. Download them to `toolchain/riscv32-esp-linux-musl` by

```sh
make toolchain
```

## 3. Build the Project

Activate ESP-IDF in your terminal:

```sh
export IDF_PATH="$HOME/esp-idf" # Replace with the path to your ESP-IDF installation if different
. "$IDF_PATH/export.sh"
```

Build the entire project and flash with a connected S31 board with

```sh
make all # equivalent to make uboot, linux, rootfs, flash-all
```

To build a particular component, use

```sh
make uboot
make linux
make rootfs
```

and flash with

```sh
make flash-all
```


## 4. Build output

| Path under `build/` | Content |
|---|---|
| `u-boot-spl-dtb.bin` | SPL with its DTB |
| `spl_app.bin` | ESP ROM image wrapper around SPL |
| `u-boot.itb` | FIT containing OpenSBI, U-Boot proper and associated data |
| `esp32s31_generic.dtb` | Linux device tree |
| `xipImage` | Flash-XIP Linux kernel |
| `rootfs.sqfs` | SquashFS root filesystem |
| `radio.sqfs` | Radio module and firmware filesystem |
| `s31_full_flash.bin` | Combined  installation image (will overwrite persist partition) |
| `persist.jffs2` | Empty JFFS2 image |

For more build targets, see the [Make reference](../resources/make-reference.md).