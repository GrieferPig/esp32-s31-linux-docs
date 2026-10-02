# Build from source

Ubuntu 24.04 LTS is the reference host used by the release workflow. Buildroot
requires Linux; native Windows and macOS builds are not covered here. Allow
space for source trees, toolchains, downloaded packages, and build outputs.
Disk and memory use depend on the selected packages and build parallelism;
no measured minimum is provided here.

## 1. Install host tools

On Ubuntu 24.04, install the build dependencies and the tools used below:

```sh
sudo apt-get update
sudo apt-get install -y \
  git curl wget file python3 python3-pip python3-venv cmake \
  bison bc build-essential ccache cpio device-tree-compiler flex gperf \
  libffi-dev libssl-dev libncurses-dev ninja-build \
  python3-pkg-resources python3-pyelftools rsync unzip xz-utils mtd-utils
```

`libncurses-dev` supports Buildroot's configuration menu. `mtd-utils` supplies
`mkfs.jffs2` for the optional `make persist` target.

## 2. Check out the source

These instructions describe parent revision
`a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104`. Check it out before initializing
the component revisions recorded by that commit:

```sh
git clone https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
git checkout a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104
git submodule update --init --recursive
```

Run the remaining build commands from this directory. For development on
another revision, use its `configs/build-versions.mk` and recorded submodule
commits together; see [Working with submodules](../contribute/submodule-workflow.md).

## 3. Install ESP-IDF and the Linux toolchain

### ESP-IDF

The LP and radio firmware builds use ESP-IDF components, libraries, and its
ESP toolchain. The parent build checks the exact ESP-IDF revision in
`configs/build-versions.mk`; an arbitrary checkout of the default branch does
not satisfy that check.

For a new installation, use an unused directory at `IDF_PATH`:

```sh
export IDF_PATH="$HOME/esp-idf"
git clone https://github.com/espressif/esp-idf.git "$IDF_PATH"
git -C "$IDF_PATH" checkout a602e67b0bf9ee0806dc4e1df7afc9affedf5c33
"$IDF_PATH/install.sh" esp32s31
. "$IDF_PATH/export.sh"
```

Change `IDF_PATH` if that directory belongs to another project. In each new
terminal, export the same `IDF_PATH` and source its `export.sh` again. Build
and flash recipes use this ESP-IDF environment's `esptool`. A separate
installation for release-image flashing is covered in
[Flash and first boot](flash-and-first-boot.md).

### Linux toolchain

The project uses a custom toolchain from
[crosstool-NG-s31](https://github.com/GrieferPig/crosstool-NG-s31), with port-specific
compiler changes. Download the release selected by `configs/build-versions.mk`:

```sh
make toolchain
```

At this source revision the selected release is
`esp32s31-linux-gcc-15.2.0-5`. The target checks the download checksum and installs
the toolchain under `toolchain/riscv32-esp-linux-musl`. See
[ISA and toolchain](../hw-reference/isa.md) before changing compiler or ABI flags.

## 4. Build and flash

Choose a [build profile](build-profiles.md). Local builds default to lean radio.
To match the release workflow and enable optional peripheral drivers, use
full peripherals:

```sh
export S31_LEAN_RADIO=0
make all
```

`make all` builds the component images, combined installation image, manifest,
and checksums on the host. It does not write to a board. Set `JOBS` to limit
parallel compilation when needed, for example `make JOBS=4 all`.

Component targets are also available:

```sh
make uboot
make linux
make rootfs
```

These integrated targets also build their dependencies. For example,
`make rootfs` depends on Linux, radio, and LP firmware work.

To update a connected board while preserving its persist partition, keep the
same profile selected and run:

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

This target builds its dependencies again before flashing. Replace `PORT` with
your board's serial device. Installation, console settings, and first login
are covered in [Flash and first boot](flash-and-first-boot.md).

## 5. Build output

The normal `make all` outputs include:

| Path under `build/` | Content |
|---|---|
| `u-boot-spl-dtb.bin` | SPL with its DTB; intermediate input to the ROM image wrapper |
| `spl_app.bin` | ESP ROM image wrapper around SPL |
| `u-boot.itb` | FIT containing OpenSBI, U-Boot proper, and associated data |
| `esp32s31_generic.dtb` | Linux device tree |
| `xipImage` | Flash-XIP Linux kernel |
| `rootfs.sqfs` | SquashFS root filesystem |
| `radio.sqfs` | Radio module and firmware filesystem |
| `s31_full_flash.bin` | Combined installation image; flashing it overwrites the persist region |
| `build-manifest.json` | Build provenance and artifact metadata |
| `SHA256SUMS` | Checksums for the published image files and manifest |

`make persist` separately creates an empty `build/persist.jffs2`; it is not
an output of `make all`. `make flash-persist` writes that empty filesystem and
erases existing persistent files and settings.

For the complete target list, see the [Make reference](../resources/make-reference.md).
