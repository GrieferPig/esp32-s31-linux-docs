# Adding a driver

Peripheral drivers live in the `linux-esp32-s31` Linux source. A typical addition
consists of a driver, a device-tree binding, build options, and an overlay that
enables the hardware.

## 1. Choose the Linux subsystem

Use the subsystem that matches the device: I2C, SPI, ALSA, IIO, PWM, Counter,
SocketCAN, or another standard framework. This gives applications the usual
Linux interface and lets the driver reuse existing infrastructure.

The S31 I2C and SPI drivers are useful examples of platform-driver setup.
They obtain registers, interrupts, clocks, and resets from the device tree.

## 2. Describe the hardware

Add or reuse a YAML binding under `Documentation/devicetree/bindings/`.
Describe the registers, interrupts, clocks, resets, pins, and any DMA,
regulator, or power-domain dependencies.

Add the device node to `arch/riscv/boot/dts/espressif/esp32s31.dtsi`. Optional
peripherals normally start with `status = "disabled"`; an overlay enables
them and selects their pins. See [Adding an overlay](adding-an-overlay.md).

## 3. Implement the driver

During probe, acquire the resources described by the binding, enable the
hardware, and register the device with its Linux subsystem. Use managed
resource helpers where practical, and return `-EPROBE_DEFER` when a required
provider is still starting.

Use the common clock, reset, regulator, and power-management APIs for shared
hardware. For DMA buffers, follow [DMA and cache](dma-and-cache.md). Interrupt
handlers should acknowledge the device promptly and schedule longer work in a
worker or another suitable subsystem context.

The remove and error paths should stop transfers, disable interrupts, and
release the resources acquired during probe. Implement suspend and resume
where the device needs to save or restore state.

## 4. Add the build options

Add a Kconfig entry and Makefile rule in the driver directory. Include the
subsystem and provider dependencies in Kconfig, then select the driver in the
S31 defconfig and parent `configs/kernel/` fragments where appropriate.
Keep lasting changes in these source files, not generated `out/linux/.config`.
The build enables `CONFIG_TRIM_UNUSED_KSYMS=y`, so build new modules together
with the kernel to retain their required exports. Out-of-tree modules may
require an explicit export whitelist; see
[Build configuration](../get-started/build-configuration.md).

From the parent project, rebuild the kernel, rootfs, and radio image:

```sh
make linux rootfs radio-fs
```

The rootfs build installs the Linux radio module and device-tree overlays; `radio-fs`
prelinks the radio image against the rebuilt kernel. Update kernel,
rootfs/module, and `radio.bin` as a matched set. A new driver selected as `m`
needs an explicit package/install step for its `.ko`; the parent build does
not install every kernel module automatically. Run `make image` to verify and
publish the matched image set before flashing. Follow
[Flash and first boot](../get-started/flash-and-first-boot.md) to update the board.

## 5. Test it

Enable the overlay, check the probe log, and exercise the device through its
userspace API. Test removal after closing applications, invalid settings, and
error recovery as well as normal transfers.
