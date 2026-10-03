# Adding an overlay

A device-tree overlay enables a peripheral and selects its pins and settings.
The `s31-overlay` tool loads these descriptions while Linux is running and can
save the selection for the next boot.

## 1. Create the overlay

Create `esp32s31-overlay-NAME.dtso` under
`linux-esp32-s31/arch/riscv/boot/dts/espressif/`. Start with an existing overlay
for a similar device.

An overlay needs the device-tree plugin header, a unique name, and a list of
resources it uses. For example, the I2C0 overlay starts with:

```dts
/dts-v1/;
/plugin/;

/ {
    espressif,overlay-name = "i2c0";
    espressif,resource-claims = "i2c0";
};
```

Resource claims keep two overlays from using the same controller or DMA
channel. Use `espressif,gpio-claims` for fixed pins that are not already
described by the pinmux entries.

## 2. Add the device and pin settings

Enable the controller with `status = "okay"` and supply its pinctrl state.
Include any required clocks, resets, DMA channels, regulators, PHYs, or child
devices.

To let users choose a GPIO, give the pin node an `espressif,route-name` and
`espressif,route-kind`. The supported kinds are `matrix-input`,
`matrix-output`, and `matrix-bidirectional`. Nodes with several separately
named routes use the corresponding `route-names` and `route-kinds` lists.

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

Add the overlay's `.dtbo` target to the DTS Makefile, then build from the
parent project:

```sh
make linux rootfs radio-fs
```

The DTBO is built in `out/linux/arch/riscv/boot/dts/espressif/` and
installed into `/usr/lib/s31-overlays` in the rootfs. `radio-fs` refreshes the
radio image against the rebuilt kernel. Keep the kernel, rootfs/module, and
radio image from the same build when updating the board. Run `make image`
to verify and publish the complete matched set for the flashing workflow.

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
