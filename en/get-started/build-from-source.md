# Build from Source

The parent repository integrates the toolchain, OpenSBI, U-Boot, Linux,
Buildroot, radio payload, LP firmware, root filesystem, and flash packaging.
Run builds from the parent repository root.

## Integrated build

```sh
make linux
make rootfs
make radio-fs
make radio-package
make flash-image
```

`make all` resolves the toolchain and builds the normal boot chain, kernel,
root filesystem, and flash image. `JOBS` controls parallelism. The default
kernel configuration is `esp32s31_defconfig`, and the default kernel artifact
is `xipImage`.

The default lean radio profile removes optional peripherals. Prefix the build
commands with `S31_LEAN_RADIO=0` to include I2C, SPI target and I2S. See
[build profiles](build-profiles.md). `radio-fs` packs the module and payload in
`radio.sqfs`; `radio-package` produces the redistribution archive from that
staging tree.

## Output directory

Generated artifacts are under `build/`:

| Artifact | Purpose |
|---|---|
| `u-boot-spl-dtb.bin`, `spl_app.bin` | ROM-loadable SPL |
| `u-boot.itb` | U-Boot/OpenSBI FIT |
| `esp32s31_generic.dtb` | Base device tree |
| `xipImage` | Linux XIP image |
| `rootfs.sqfs` | Immutable root filesystem |
| `persist.jffs2` | Optional persistent filesystem image |
| `radio.sqfs` | Separately packaged radio runtime |
| `s31_full_flash.bin` | Combined non-persistent flash image |

## Component builds

Linux is configured as an out-of-tree build under `build/linux-6.18`.
Invoking the kernel submodule directly requires the matching `O=` directory,
cross-compiler prefix, architecture, and ISA/ABI flags. Prefer the parent
targets unless developing a single kernel component.

Radio dependency generation requires an ESP-IDF checkout discoverable through
`IDF_ROOT`, `IDF_PATH`, or `IDF_EXPORT`. The build checks the configured IDF
environment before producing payload objects. LP firmware uses its own linker
layout and is staged under the target firmware directory for remoteproc.

## Reproducibility boundary

Submodule revisions, toolchain release, ESP-IDF revision, configuration files,
and radio redistribution inputs are part of the build identity. Host paths,
elapsed times, and one-off benchmark results are not part of the programming
guide.
