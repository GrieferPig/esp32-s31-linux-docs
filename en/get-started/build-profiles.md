# Build profiles

Choose a profile according to the peripherals your application needs.

The binary releases on GitHub uses the `Lean radio` profile.

| Profile | Selection | Included features |
|---|---|---|
| Lean radio | `S31_LEAN_RADIO=1` (default) | Wi-Fi, Bluetooth, console, flash, persistent settings, and USB host/storage |
| Full peripherals | `S31_LEAN_RADIO=0` | The above plus optional drivers such as I2C, SPI, I2S, Ethernet, and SD/MMC |

## Select a profile

To use the full-peripheral profile, set the variable before building:

```sh
S31_LEAN_RADIO=0 make all
```

To return to the lean-radio profile:

```sh
S31_LEAN_RADIO=1 make all
```

Both profiles use the same flash layout. Optional hardware is selected at
runtime with [overlays](../resources/overlay-catalog.md).

## Add applications

Both profiles use a compact Buildroot root filesystem. 
Additional packages need to be added separately.
See [Adding a userspace tool](../api-guides/adding-a-userspace-tool.md).

## Change build options

The main source configuration files are:

| File | Settings |
|---|---|
| `linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` | Kernel features and drivers |
| `buildroot-external/configs/esp32s31_rootfs_defconfig` | Rootfs packages and system options |
| `buildroot-external/board/esp32-s31/post-build.sh` | Files kept or removed from the finished rootfs |

Edit these files for changes you intend to keep. The parent build regenerates
the output configurations from the source defconfigs, so edits made only to
`build/linux-6.18/.config` or `build/buildroot/.config` are replaced on the
next build.

`make buildroot-menuconfig` opens the Buildroot menu. Save the resulting
choices back to the source defconfig before using `make rootfs` again.

## Radio modes

TODO