# Make reference

Run these targets from the `esp32-s31-linux` repository root. For a first
build, follow [Build from source](../get-started/build-from-source.md).

## Common commands

```sh
make all             # Build the complete image
make linux           # Rebuild Linux and device trees
make rootfs          # Rebuild the root filesystem
make flash-all       # Build and flash the component images
```

Set `JOBS` to choose the number of parallel build jobs, for example
`make JOBS=4 all`. Use `S31_LEAN_RADIO=0` for a full-peripheral build.

## Build targets

| Target | Description |
|---|---|
| `all` | Build the toolchain dependencies, boot firmware, Linux, rootfs, and combined image |
| `download` | Initialize the source submodules |
| `toolchain` | Download the Linux toolchain, or reuse the installed copy |
| `toolchain-source` | Build a toolchain from the configured crosstool-NG source |
| `opensbi` | Build `fw_dynamic.bin` for the U-Boot FIT |
| `uboot`, `bootloader` | Build SPL, `spl_app.bin`, and `u-boot.itb` |
| `linux` | Build the XIP kernel, device trees, overlays, and radio module |
| `rootfs`, `initramfs` | Build `rootfs.sqfs`; both names select the SquashFS target |
| `radio-idf-deps` | Build the ESP-IDF radio dependencies |
| `radio-linux-payload` | Build the external radio firmware and generate import stubs |
| `radio-module` | Build and check the integrated radio module and firmware outputs |
| `radio-fs` | Create `build/radio.sqfs` |
| `radio-package` | Create the engineering radio archive under `build/radio-package/` |
| `lp-firmware` | Build and stage the LP remoteproc firmware |
| `persist` | Create an empty `build/persist.jffs2` |
| `flash-image` | Create the combined `build/s31_full_flash.bin` file |
| `coremark` | Build and copy the benchmark to `build/coremark/coremark.exe` |
| `buildroot-menuconfig` | Open Buildroot configuration |
| `buildroot-clean` | Clean the Buildroot build |
| `clean` | Remove build output |
| `fullclean` | Remove build output and the installed project toolchain |

The parent build reapplies the kernel and rootfs defconfigs. Save lasting
configuration changes in those source files; see
[Build profiles](../get-started/build-profiles.md).

## Flash targets

These targets use `/dev/ttyUSB0` at 2000000 baud. For another port, use the
explicit `esptool` commands in
[Flash and first boot](../get-started/flash-and-first-boot.md).

| Target | What it writes |
|---|---|
| `flash-all` | SPL, FIT, DTB, radio, kernel, and rootfs; keeps persist |
| `flash-bootloader` | SPL and FIT |
| `flash-opensbi` | FIT containing OpenSBI and U-Boot |
| `flash-linux` | Linux DTB and kernel |
| `flash-dtb` | Linux DTB |
| `flash-radio` | Radio filesystem |
| `flash-rootfs` | Root filesystem |
| `flash-existing-radio` | Existing `build/radio.sqfs`, without rebuilding |
| `flash-existing-rootfs` | Existing `build/rootfs.sqfs`, without rebuilding |
| `flash-persist` | Empty persistent filesystem; erases saved files and settings |
| `erase` | Entire flash chip |

The regular flash targets build their dependencies first. The `existing`
variants use the files already on disk, so use them only after a completed
build. `flash-image` belongs to the build table above: it produces a file on
the host.

## Build variables

| Variable | Use |
|---|---|
| `JOBS` | Parallel jobs; defaults to the host CPU count |
| `S31_LEAN_RADIO` | `1` for the compact radio profile, `0` for full peripherals |
| `DEFCONFIG` | Kernel configuration; defaults to `esp32s31_defconfig` |
| `LINUX_TARGET` | Kernel image target; defaults to `xipImage` |
| `IDF_EXPORT` | Path to the ESP-IDF `export.sh` to use |
| `IDF_PATH`, `IDF_ROOT` | ESP-IDF installation and discovery paths |
| `TOOLCHAIN_RELEASE_TAG` | Toolchain release to download; defaults to `latest` |
| `TOOLCHAIN_RELEASE_REPOSITORY` | Repository supplying toolchain releases |
| `CROSSTOOL_NG_DIR` | Source tree for `toolchain-source` |
| `S31_BTSTACK_O2` | BTstack optimization selection |

The integrated radio firmware build selects the combined Wi-Fi/Bluetooth
payload. Choose the active radio mode at runtime with `esp32-config`.

Low-level variables such as `FW_TEXT_START`, `FW_RW_START`, and
`LINUX_XIP_ADDR` are used when changing the boot memory layout. Coordinate
those changes with the linker scripts and device tree; see
[Memory map](../hw-reference/memory-map.md) and
[Flash layout](../hw-reference/flash-layout.md).
