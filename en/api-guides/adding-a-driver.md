# Adding a driver

Add peripheral drivers in the `linux-esp32-s31` source tree, using the Linux
subsystem that matches the device: I2C, SPI, ALSA, IIO, PWM, Counter, SocketCAN,
or another standard framework. Keep the hardware description, kernel build
options and enabling overlay together with the driver integration.

## 1. Follow a complete integration example

The existing I2C0 support shows how the pieces fit together. Paths in this table
are relative to `linux-esp32-s31`.

| Integration piece | I2C0 example |
| --- | --- |
| Driver and device match | [`drivers/i2c/busses/i2c-esp32s31.c`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/i2c-esp32s31.c#L779-L859): probe, I2C adapter registration and `espressif,esp32s31-i2c` match. |
| Binding | [`Documentation/devicetree/bindings/i2c/espressif,esp32s31-i2c.yaml`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/devicetree/bindings/i2c/espressif,esp32s31-i2c.yaml#L15-L55): registers, IRQ, clock, optional reset and bus frequency. |
| Base hardware node | [`arch/riscv/boot/dts/espressif/esp32s31.dtsi`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L1180-L1192): `i2c0` at `0x20385000`, matrix interrupt source 23, clock/reset references and `status = "disabled"`. |
| Enabling overlay | [`arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso#L7-L43): resource claim, named SCL/SDA routes, bus-frequency parameter and `status = "okay"`. |
| Kernel build | [`drivers/i2c/busses/Kconfig`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/Kconfig#L1597-L1605) defines `I2C_ESP32S31`; the [directory Makefile](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/Makefile#L164) selects the object; [`esp32s31_defconfig`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/configs/esp32s31_defconfig#L185-L188) enables it. |
| Overlay build | [`arch/riscv/boot/dts/espressif/Makefile`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/Makefile#L24-L25) registers the `.dtbo` target. |

For a new peripheral, add or reuse the corresponding binding, describe its real
resources in the base device tree, and provide an overlay for optional hardware.
Document pin selection and resource claims as described in
[Adding an overlay](adding-an-overlay.md). Include DMA, regulator and power-domain
dependencies only when the device uses them.

## 2. Acquire resources and register the subsystem

In the I2C example, probe maps the register resource, obtains and enables the
clock, registers a managed clock-disable action, gets the optional reset, and
initializes bus timing. It then requests the IRQ and registers the I2C adapter.
Provider errors pass through `dev_err_probe()`, preserving `-EPROBE_DEFER` when
returned by a provider.
[Probe and cleanup registration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/i2c-esp32s31.c#L774-L839).

Use managed helpers where they fit the lifetime of the resource, and propagate
the actual resource-acquisition error. Shared hardware and execution-context
rules are covered in [Clock, reset and power](../api-reference/system/clock-reset-power.md),
[Interrupts and SMP](../api-reference/system/interrupts-smp.md), and
[DMA and cache](dma-and-cache.md).

Design error, remove and suspend paths with the active transfer lifetime in mind.
Stop new work, quiesce hardware and callbacks, and then release resources. Add
suspend/resume operations if the device needs state saved or restored. Managed
allocation alone does not specify how an active transfer stops; for DMA, follow
the termination and synchronization rules in the DMA guide.

## 3. Build the driver and overlay

Add the driver's Kconfig dependencies and object rule, enable it in
`arch/riscv/configs/esp32s31_defconfig` or your selected `DEFCONFIG`, and register
new overlay targets in the DTS directory Makefile. The parent `linux` target
reapplies the selected defconfig, so keep intended configuration changes there.
[Parent Linux target](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L287-L289).

From the parent project, build and flash the full-peripheral configuration.
Use the [flash guide](../get-started/flash-and-first-boot.md) to select the port
and prepare the serial connection:

```sh
export S31_LEAN_RADIO=0
make flash-all PORT=/dev/ttyUSB0
```

`rootfs` already depends on `linux`, which builds the kernel, modules and device
trees. `S31_LEAN_RADIO=0` keeps the optional peripheral configuration available.
The rootfs post-build step installs built overlays into `/usr/lib/s31-overlays`.
[Build profile](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L226-L232);
[Linux artifacts](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L399-L406);
[rootfs dependency](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L438-L445);
[overlay installation](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/post-build.sh#L237-L249).

After the board restarts, enable the overlay with the procedure in
[Adding an overlay](adding-an-overlay.md).

## 4. Validate behavior

For the existing I2C/SPI example, this host test exercises extracted I2C command
and long-transfer logic plus SPI target-buffer copying:

```sh
python -m unittest tools.tests.test_s31_feature_contracts.DriverContracts.test_driver_wire_contracts -v
```

The [test harness](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/tests/test_s31_feature_contracts.py#L243-L257)
compiles selected source functions with simulated inputs. For a new driver,
add focused checks for its own parsing, transfer construction or error handling
where these can run independently of hardware.

On the board, check overlay application and probe output, exercise the subsystem's
userspace API, and verify data against a known peer or instrument. Test invalid
settings, timeout recovery, repeated transfers and removal after users have
closed the device. If the driver supports suspend/resume, test that path with
its intended wake source and an active or recently completed transfer. Record
the wiring, build revision and commands with the results.
