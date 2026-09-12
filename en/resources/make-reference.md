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
| `radio-package` | Package `radio.sqfs`, the radio module, payload, overlays, configuration, notices, and manifest as `build/radio-package/esp32s31-radio-<mode>.tar.xz` |
| `persist` | Produce an explicit JFFS2 persistent image |
| `flash-image` | Assemble the contiguous full image without a persist payload |
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
| `FW_TEXT_START`, `FW_RW_START` | OpenSBI text and writable link addresses |

Flash offsets and partition sizes are centralized in
`configs/esp32s31-layout.cfg`; do not duplicate them in Make recipes.

## Local validation and build identity

`make check-host` runs the layout and host regression checks; `make check-docs`
builds Sphinx with warnings treated as errors. `make check-dt` validates S31
bindings, base DTBs and each individually merged overlay and fails on validator diagnostics even if Kbuild returns
zero. `make check-fast` runs all three. Install `docs/requirements.txt` and
`dtschema==2026.6` into a host virtual environment first.

`configs/build-versions.mk` selects the ESP-IDF commit, IDF compiler release,
and Linux toolchain release for both local builds and CI. `IDF_EXPORT` can
select its installation location. A different IDF revision requires the explicit
experimental override `S31_ALLOW_UNPINNED=1`; the build manifest still records
its actual identity. `TOOLCHAIN_RELEASE_TAG=latest` is an explicit opt-in to a
moving toolchain and is not the reproducible default. After `toolchain-source`,
use `TOOLCHAIN_RELEASE_TAG=local` to keep that explicitly selected local compiler.

`make build-manifest` records actual source revisions, dirty-tree fingerprints,
configuration hashes, compiler identity, and available artifact hashes in
`build/build-manifest.json`. `flash-image` generates it with `build/SHA256SUMS`;
radio packages include the manifest. Missing artifacts are absent from the
manifest; generating it alone does not build or validate them.

`radio-image` is retired and fails with a migration message. Use `radio-fs`
for `radio.sqfs` or `radio-package` for an archive. The old `FW_PAYLOAD`,
`FW_JUMP_ADDR`, and `LINUX_XIP_ADDR` knobs have no supported build effect.

Flash commands reject missing, empty or oversized images before serial access
and accept `PORT` and `BAUD`. Select the board's download port
explicitly, for example `make PORT=BOARD_PORT BAUD=2000000 flash-all`.

Source checkout initialization is explicit: run `make download` separately,
then build. The package script completes `radio-fs` before generating its
manifest even when Make parallelism is inherited. Image releases use one
layout-driven artifact list for publication and checksums.

The DT gate validates all schemas selected by the base DTBs and merged overlays,
including generic IP bindings. Its only schema adaptation adds the named
`/chosen/opensbi-config` child through the explicit in-tree OpenSBI binding;
other `/chosen` properties remain validated. Untracked source input names such
as Makefiles, init scripts and Buildroot packages are included in dirty identity.
