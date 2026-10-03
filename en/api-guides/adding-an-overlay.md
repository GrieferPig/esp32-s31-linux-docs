# Adding an overlay

A device-tree overlay enables a peripheral and selects its pins and settings.
The `s31-overlay` tool loads these descriptions while Linux is running and can
save the selection for the next boot.

## 1. Create the overlay

Create `esp32s31-overlay-NAME.dtso` under
`linux-esp32-s31/arch/riscv/boot/dts/espressif/`. Start with an existing overlay
for a similar device. The
[complete I2C0 overlay](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso)
includes the header, resource declaration, pinctrl nodes, and controller settings.

An overlay needs the device-tree plugin header and an `espressif,overlay-name`.
Choose a new name for a new overlay. Add `espressif,resource-claims` when it uses
a controller, DMA channel, or other resource that competing overlays must not
share. For example, the I2C0 overlay starts with:

```dts
/dts-v1/;
/plugin/;

/ {
    espressif,overlay-name = "i2c0";
    espressif,resource-claims = "i2c0";
};
```

The resource list is optional. Use the same claim name in overlays that need
the same exclusive resource so the manager can detect their conflict. Use
`espressif,gpio-claims` for fixed pins that are not already described by the
pinmux entries.

## 2. Add the device and pin settings

Enable the controller with `status = "okay"` and supply its pinctrl state.
Include any required clocks, resets, DMA channels, regulators, PHYs, or child
devices.

To let users choose a GPIO, give the pin node an `espressif,route-name` and
`espressif,route-kind`. The supported kinds are `matrix-input`,
`matrix-output`, and `matrix-bidirectional`. Nodes with several separately
named routes use the corresponding `espressif,route-names` and
`espressif,route-kinds` lists.

For example, the I2C0 overlay exports `i2c0.scl` and `i2c0.sda`. Users can
inspect them with `s31-overlay routes i2c0` and choose pins when applying the
overlay.

To expose a numeric setting, declare its property name and allowed values:

```dts
&i2c0 {
    espressif,param-name = "clock-frequency";
    espressif,param-values = <100000 400000 1000000>;
    clock-frequency = <100000>;
    status = "okay";
};
```

The tool then accepts `clock-frequency=400000` and rejects values outside the
list. The complete overlay also needs the controller's pinctrl configuration.

## 3. Build and install it

Add the overlay's `.dtbo` target to
`arch/riscv/boot/dts/espressif/Makefile` in the kernel tree, replacing `NAME`
with your overlay name:

```make
dtb-$(CONFIG_ARCH_ESPRESSIF) += esp32s31-overlay-NAME.dtbo
```

From the parent project, build and flash the complete matched image set.
Use the [flash guide](../get-started/flash-and-first-boot.md) to select the port
and prepare the serial connection:

```sh
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

The DTBO is built in `out/linux/arch/riscv/boot/dts/espressif/` and
installed into `/usr/lib/s31-overlays` in the rootfs.
For files copied to the running board during development, follow the
[deployment rules](deploy-files-that-must-survive-reboot)
before relying on them after a reboot.

## 4. Test it on the board

After updating the image, inspect the overlay's settings and try a temporary
application. Substitute your overlay name for `i2c0`:

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
s31-overlay apply i2c0 --volatile
s31-overlay status
dmesg
```

Exercise the peripheral, close its users, and remove the overlay:

```sh
s31-overlay remove i2c0 --volatile
```

Also try conflicting pin selections and invalid parameter values. Once the
normal path works, apply without `--volatile` and reboot to check restoration.
See [Using overlays](../resources/overlay-catalog.md) for saved-selection and
rollback behavior when testing failure cases.
