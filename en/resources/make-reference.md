# Make reference

Run GNU Make from the parent repository. Component-native systems own compilation;
the parent selects configuration inputs, output paths, ordering, validation and publication.
For installation, see [Build from source](../get-started/build-from-source.md).

## Common commands

```sh
make help                         # Default; no build or hardware access
make doctor                       # Diagnose host tools and configured paths
make fetch                        # Explicitly prepare pinned dependencies
make build                        # Build the matched component set
make image                        # Merge, verify and publish the image set
make check                        # Host, documentation and devicetree checks
```

Every build uses the full board configuration. `DEBUG=1` adds the debug fragment.
Use `JOBS=4` to bound native parallelism. Machine paths and job limits may be set
in ignored `local.mk`. See [Build configuration](../get-started/build-configuration.md).

## Build targets

| Target | Description |
|---|---|
| `build` | Build boot firmware, Linux, rootfs and the paired radio image |
| `image`, `all`, `flash-image` | Build, merge, verify and atomically publish the image set |
| `fetch` | Explicitly prepare pinned sources, toolchain, BTstack and Buildroot downloads |
| `fetch-rootfs` | Fetch the selected Buildroot package sources without building target packages |
| `download` | Initialize pinned source submodules |
| `toolchain` | Validate an installed toolchain |
| `toolchain-fetch` | Fetch the pinned prebuilt Linux toolchain |
| `toolchain-source` | Build a toolchain from configured crosstool-NG source |
| `opensbi` | Build native OpenSBI output |
| `uboot`, `bootloader` | Build SPL, ROM wrapper and FIT |
| `linux` | Build XIP kernel, device trees, overlays and radio module |
| `rootfs`, `initramfs` | Build the SquashFS root filesystem |
| `radio-idf-deps` | Build the ESP-IDF radio dependency closure |
| `radio-linux-payload` | Build relocatable payload and generated import stubs |
| `radio-module` | Build and check the radio module and payload outputs |
| `radio-image`, `radio-fs` | Build the radio XIP image bound to this kernel/module |
| `radio-package` | Create an engineering archive from the verified image set |
| `lp-firmware` | Build LP firmware and stage it in the build staging overlay |
| `persist` | Create an empty JFFS2 image; does not flash it |
| `coremark` | Build and copy the benchmark into build staging |
| `buildroot-menuconfig` | Open Buildroot configuration |
| `buildroot-clean`, `buildroot-reconfigure` | Remove only the selected Buildroot output |
| `idf-check` | Check ESP-IDF against the dependency lock |
| `check-layout` | Validate flash, SRAM, linker and devicetree contracts |
| `check-host` | Run host regression tests without downloads or hardware |
| `check-docs` | Build documentation with strict Sphinx warnings |
| `check-dt` | Validate device trees, schemas and overlays |
| `check`, `check-fast` | Combine host, documentation and devicetree validation |
| `build-manifest` | Verify existing artifacts and record build provenance |
| `check-artifacts` | Verify existing images against `out/images/build-manifest.json` |
| `clean`, `fullclean` | Remove the build output; retain shared caches |

Final build artifacts live in `out/images/`; verified published sets live in
`dist/`, with `dist/current` selecting the current set. Native component
objects, generated files, staging and reports stay under `out/`. Downloads
and toolchains are shared in `cache/`.

For lasting selections, edit tracked defconfigs and `configs/kernel/*.config`.
Changed Linux, U-Boot, or radio configuration inputs trigger native
reconfiguration; unchanged inputs retain native incremental builds. Buildroot
package-selection or toolchain changes require `make buildroot-reconfigure`
before rebuilding, so stale target contents cannot survive a configuration
change. Save intended Buildroot menu changes in its tracked defconfig before
that command, which removes the selected Buildroot output tree.

`ROOTFS_BASELINE=/absolute/path/to/rootfs.sqfs` is an explicit incremental
repack option with recorded provenance, not a clean Buildroot rebuild. It
checks the full userspace runtime inventory and the exact module list; an
incomplete baseline is rejected. Inherited target binaries are
not claimed to have been rebuilt with size optimization.
If only stock logging/cron startup scripts are missing, set
`ROOTFS_BUSYBOX_BUILD=/path/to/busybox-build` to explicitly allow their restoration
from the pinned Buildroot checkout. The repacker checks actual inherited applet/help
bytes, records exact additions, and preserves existing filesystem metadata.

## Device targets

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-existing-all
```

`flash-existing-all` and its alias `flash-all` resolve `dist/current` once, verify that immutable set, and write SPL,
FIT, DTB, radio, kernel and rootfs slot-wise. They never build. `build-flash`
explicitly builds first. Persist is preserved only when the board already uses
the same layout. The combined image overwrites persist; see
[Flash and first boot](../get-started/flash-and-first-boot.md).

Partial targets (`flash-radio`, `flash-linux`, `flash-rootfs`, `flash-dtb`,
`flash-bootloader`, `flash-opensbi`, and the partial `flash-existing-*` aliases)
fail closed because the installed companions cannot be proven. There is no
unsafe override. `flash-persist` and `erase` also refuse; destructive maintenance
requires an explicit separate procedure.

The manifest checks component and combined-image hashes, radio's build-time
kernel/module/payload/import bindings, and configuration identity. These
are host checks; they do not establish a successful hardware boot.

## Build variables

| Variable | Use |
|---|---|
| `DEBUG` | `1` adds debug kernel configuration |
| `JOBS` | Parallel native build jobs |
| `OUT_ROOT`, `CACHE_DIR` | Output and shared-cache roots |
| `PORT`, `BAUD` | Device port and baud rate |
| `IDF_EXPORT`, `IDF_PATH`, `IDF_ROOT` | Local ESP-IDF paths |
| `TOOLCHAIN_PREFIX` | Installed cross-toolchain directory |
| `TOOLCHAIN_RELEASE_TAG` | Dependency-lock release, or explicit local experiment |
| `CROSSTOOL_NG_DIR` | Source tree for `toolchain-source` |
| `S31_ALLOW_UNPINNED` | Explicit experimental ESP-IDF override |
| `ROOTFS_BASELINE` | Explicit verified rootfs for incremental module repack |
| `ROOTFS_BUSYBOX_BUILD` | Optional existing BusyBox build evidence to restore missing full-service init scripts from pinned Buildroot sources |

Low-level boot-address changes must be coordinated with linker scripts, the
layout file and devicetree. See [Memory map](../hw-reference/memory-map.md) and
[Flash layout](../hw-reference/flash-layout.md).
