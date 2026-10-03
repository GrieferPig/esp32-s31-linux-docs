# Build configuration

Every build uses the full board configuration. Wi-Fi, Bluetooth, USB, I2C, SPI,
I2S, Ethernet, SD/MMC and the other native board drivers use one configuration.
There is no build variant selector. Optional hardware is enabled at runtime with
[overlays](../resources/overlay-catalog.md).

```sh
make build
make image
```

Native outputs, staging and reports live in `out/`; final images are in
`out/images/`. One lock serializes writers of this output tree. Shared downloads
and toolchains stay in `cache/`. Published matched sets live in `dist/<build-id>/`
with `dist/current` updated only after verification.

The full XIP kernel fits the 6 MiB slot using size optimization and unused-export
trimming. The integrated kernel build measures 6,228,940 bytes, leaving 62,516 bytes
in the 6,291,456-byte slot. This is a host artifact measurement, not hardware
validation, and changes with the exact source/configuration. Builds fail the size gate rather
than silently remove drivers or publish oversized images. Kernel-size changes
require explicit source configuration changes and revalidation.

## Source configuration

| File | Settings |
|---|---|
| `linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` | Native board defaults |
| `configs/kernel/common.config`, `configs/kernel/board.config` | Canonical full kernel choices |
| `configs/kernel/debug.config` | Optional `DEBUG=1` diagnostic additions |
| `buildroot-external/configs/esp32s31_rootfs_defconfig` | Rootfs packages and system options |
| `buildroot-external/board/esp32-s31/post-build.sh` | Rootfs installation policy |

Edit source configuration for lasting changes. Generated `out/linux/.config`
and `out/buildroot/.config` are regenerated when their source inputs change.
Unchanged input identities retain native incremental builds. Buildroot refuses
changed package/toolchain inputs in a populated output; use
`make buildroot-reconfigure` before rebuilding it. Download caches are retained.

`make buildroot-menuconfig` opens the Buildroot menu. Save desired choices back
to the source defconfig. Additional applications must be selected in Buildroot;
see [Adding a userspace tool](../api-guides/adding-a-userspace-tool.md).

## Configuration tools and time zones

The full image includes `esp32-config`, its GPIO service and configuration backup.
BusyBox supplies network time. The GPIO service starts when assignments are
saved; automatic time and the startup program are initially disabled.

The rootfs post-build step generates `/usr/share/esp32-config/kernel-features`
from the completed kernel configuration. Keep the kernel and rootfs matched so
the menu describes the running image. Retained IANA zones come from
`configs/esp32-config-timezones.list`; adding a new source region also requires
updating `BR2_TARGET_TZ_ZONELIST` in the Buildroot defconfig.

## Radio modes

The integrated build always creates the combined Wi-Fi/Bluetooth payload.
On the board, `esp32-config wifi enable|disable` and
`esp32-config bluetooth enable|disable` save service policy and reload the
radio. Reloading can disconnect active users. The mac80211 frontend supports
one station interface; the full board configuration does not add AP support.
See the [radio reference](../api-reference/radio/index.md).

## Size optimization

Target code uses size optimization through native interfaces, without changing
upstream build algorithms:

- Linux: `CONFIG_CC_OPTIMIZE_FOR_SIZE=y`; native per-object CFLAGS override the
  board's speed-only exceptions and LZ4. The entropy-source object retains its
  mandatory `-O0`; optimizing it would invalidate its assumptions.
- U-Boot/SPL: native size configuration, including size-optimized libraries.
- OpenSBI: the parent passes a second GNU Make file after the native Makefile.
  It appends `-Os` after the native flags while retaining ISA/ABI options.
- Buildroot: `BR2_OPTIMIZE_S=y`; board-owned userspace inherits TARGET_CFLAGS.
  CoreMark uses its native PORT_CFLAGS/XCFLAGS interfaces and retains two pthreads.
- ESP-IDF radio and LP firmware: native SIZE defaults; native LP compilation
  and board-owned radio C sources use `-Os`.

Host utilities retain their own optimization settings. Vendor binary archives,
toolchain runtime libraries and inherited rootfs binaries are not recompiled by
these choices. A baseline rootfs repack must explicitly report inherited
optimization as unverified. Assembly instruction sequences are unchanged.
CoreMark results need a new baseline; smaller code does not guarantee a speedup.

The kernel must fit its 6,291,456-byte slot. Check the exact artifact and manifest
after every source/configuration change. No peripheral feature is disabled or
moved into a module by this policy; ext4 and JBD2 remain built-in.

## Kernel export trimming

`CONFIG_TRIM_UNUSED_KSYMS=y` is enabled by default. Linux retains exported symbols
used by modules built in the same invocation. The radio payload also needs
kernel exports resolved dynamically during XIP prelinking. The parent derives
`out/generated/radio-kernel-symbols.txt` from the payload's undefined symbols
and passes it as `CONFIG_UNUSED_KSYMS_WHITELIST`; the validated integrated build
retains 162 symbols through that generated list.

Do not remove that list merely because the radio module links: the payload's
runtime imports are a separate contract. Regenerate it through the normal radio
build whenever firmware changes. For future or out-of-tree modules, build them
with the kernel and preserve their required exports, then rebuild and validate
the slot budget, payload prelink and module loading. Do not bypass the image-size
gate.
