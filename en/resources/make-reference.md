# Make Reference

## Primary targets

| Target | Result |
|---|---|
| `all` | Toolchain, boot chain, Linux, rootfs, and combined flash image |
| `toolchain` | Fetch or prepare the RISC-V musl toolchain |
| `toolchain-source` | Build the configured toolchain from source |
| `opensbi` | Build the S31 OpenSBI firmware |
| `uboot` | Build SPL and U-Boot FIT |
| `linux` | Build DTBs, overlays, modules, and `xipImage` |
| `rootfs` | Build the selected target root filesystem |
| `radio-idf-deps` | Build ESP-IDF-derived radio dependencies |
| `radio-linux-payload` | Build the external Linux radio payload |
| `radio-module` | Build radio kernel modules |
| `radio-package` | Produce the separately licensed `radio.sqfs` |
| `persist` | Produce an explicit JFFS2 persistent image |
| `flash-image` | Assemble normal non-persistent flash contents |
| `flash-*` | Write explicitly selected images or slots |
| `buildroot-menuconfig` | Open Buildroot configuration UI |

## Important variables

| Variable | Default role |
|---|---|
| `JOBS` | Parallel build count |
| `DEFCONFIG` | `esp32s31_defconfig` |
| `LINUX_TARGET` | `xipImage` |
| `S31_LEAN_RADIO` | Select reduced radio/rootfs packaging |
| `S31_WIFI_ONLY` | Omit Bluetooth portions where supported |
| `S31_BTSTACK_O2` | Select BTstack optimization policy |
| `IDF_ROOT`, `IDF_PATH`, `IDF_EXPORT` | Locate ESP-IDF environment |
| `TOOLCHAIN_RELEASE_REPOSITORY`, `TOOLCHAIN_RELEASE_TAG` | Select prebuilt toolchain release |
| `FW_TEXT_START`, `FW_RW_START`, `LINUX_XIP_ADDR` | Firmware/Linux link and handoff addresses |

Flash offsets and partition sizes are centralized in
`configs/esp32s31-layout.cfg`; do not duplicate them in Make recipes.
