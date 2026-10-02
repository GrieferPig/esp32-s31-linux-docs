# Build profiles

Choose a profile according to the peripherals your application needs. Local
builds default to lean radio. The GitHub release workflow explicitly selects
full peripherals with `S31_LEAN_RADIO=0`.

All S31 target components use `-Os`, including Linux, OpenSBI, U-Boot, radio/LP firmware, BTstack, CoreMark, and rootfs applications. Wi-Fi and Bluetooth frontends are enabled in the default kernel configuration.

The timing-sensitive kernel jitterentropy source retains its required `-O0`; it rejects optimized builds.

Full peripherals covers the S31 controller drivers and their required Linux frameworks. Drivers for external devices, such as SPI displays, USB HID devices, and USB sound cards, are not included automatically.

| Profile | Selection | Included features |
|---|---|---|
| Lean radio | `S31_LEAN_RADIO=1` (local default) | Wi-Fi, Bluetooth, console, flash, persistent settings, and USB mass storage for swap |
| Full peripherals | `S31_LEAN_RADIO=0` (release workflow) | The above plus optional drivers such as I2C, SPI, I2S, Ethernet, and SD/MMC |

The lean profile disables FAT, VFAT, and EXT4 support. USB block-device support
in that profile does not imply that a drive formatted with those filesystems
can be mounted. Use full peripherals for those filesystems and peripheral work.

## Select a profile

Export the choice so subsequent component builds and flash targets use the
same profile:

```sh
export S31_LEAN_RADIO=0
make all
```

To return to lean radio in the same terminal:

```sh
export S31_LEAN_RADIO=1
make all
```

`make all` builds host-side images. Follow
[Flash and first boot](flash-and-first-boot.md) to write them to the board.
A one-command assignment such as `S31_LEAN_RADIO=0 make all` does not apply to
a later, separate `make flash-all`, which rebuilds its dependencies.

Changing the profile or kernel options also requires updating the board's
kernel. Keep the selected profile exported and use
`make flash-all PORT=/dev/ttyUSB0` as described in the flash guide.
`flash-existing-rootfs` writes only the root filesystem; use it for application
updates when the board already runs the selected kernel configuration.

Both profiles use the same flash layout. Optional hardware is selected at
runtime with [overlays](../resources/overlay-catalog.md), and its drivers must
also be enabled in the selected kernel profile.

## Configuration tools in the image

Both profiles include `esp32-config`, its GPIO service, and configuration backup
support. BusyBox supplies the network-time client. The GPIO service starts at
boot when saved assignments exist; automatic time and the startup program are
initially disabled.

The post-build step generates `/usr/share/esp32-config/kernel-features` from
the completed kernel configuration. The menu uses it to offer the supported
interfaces and USB functions. It also checks the running system for usable
storage drivers. Keep the kernel and rootfs on the same selected profile.

The image retains the IANA time zones in `configs/esp32-config-timezones.list`.
To add a zone, update that list; if it belongs to another source region, include
that region in `BR2_TARGET_TZ_ZONELIST` in the Buildroot defconfig as well.
Rebuild the rootfs to update the available time-zone menu.

## Add applications

Both profiles use a compact Buildroot root filesystem. Additional packages
need to be added separately. See
[Adding a userspace tool](../api-guides/adding-a-userspace-tool.md).

## Change build options

The durable configuration inputs are:

| File | Settings |
|---|---|
| `linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` | Starting kernel feature and driver selections |
| Parent `Makefile` | Mandatory kernel selections, profile overrides, and kernel command line |
| `buildroot-external/configs/esp32s31_rootfs_defconfig` | Rootfs packages and system options |
| `buildroot-external/board/esp32-s31/busybox.fragment` | BusyBox utilities, including network time |
| `configs/esp32-config-timezones.list` | Time zones retained in the image |
| `buildroot-external/board/esp32-s31/post-build.sh` | Files kept or removed from the finished rootfs |

The parent build starts from the source defconfigs. For Linux it then applies
its own selections and the selected profile, followed by `olddefconfig` to
resolve dependencies. A source-defconfig edit cannot override an option that
the parent Makefile explicitly changes. Edits made only to
`build/linux-6.18/.config` or `build/buildroot/.config` are replaced on the next
parent build.

To edit Buildroot packages, open its menu and then save the choices back to
the source defconfig **before** another `make rootfs` or
`make buildroot-menuconfig` resets the output configuration. From the parent
repository root:

```sh
make buildroot-menuconfig
make -C buildroot O="$PWD/build/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" \
  savedefconfig DEFCONFIG="$PWD/buildroot-external/configs/esp32s31_rootfs_defconfig"
git diff -- buildroot-external/configs/esp32s31_rootfs_defconfig
```

Review that diff before rebuilding. See [Kernel configuration](../resources/kconfig-reference.md)
for checking the resulting kernel options.

## Radio modes

Both build profiles contain the combined Wi-Fi/Bluetooth payload. The runtime
policy uses the saved Wi-Fi and Bluetooth `enabled` settings to select a mode:

| Enabled services | Runtime mode | Overlay |
|---|---|---|
| Wi-Fi only | `wifi` | `radio-wifi` |
| Bluetooth only | `bt` | `radio-bluetooth` |
| Both | `combo` | `radio-combo` |
| Neither | Radio stopped | Radio profiles removed |

Use `esp32-config` to change the saved selection and apply it. These are
runtime choices, independent of `S31_LEAN_RADIO`; see
[Board configuration](../resources/esp32-config.md).
