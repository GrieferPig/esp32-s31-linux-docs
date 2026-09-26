# Device-tree bindings

Device-tree bindings describe the properties accepted by each driver. Use
them when adding a board, selecting peripheral resources, or writing an
overlay.

The following S31 schemas are under
`linux-esp32-s31/Documentation/devicetree/bindings/`:

| Schema | Device |
|---|---|
| `clock/espressif,esp32s31-clk.yaml` | Clock and reset controller |
| `counter/espressif,esp32s31-gptimer.yaml` | General-purpose timers |
| `counter/espressif,esp32s31-pcnt.yaml` | Pulse counters |
| `hwmon/espressif,esp32s31-tsens.yaml` | Temperature sensor |
| `i2c/espressif,esp32s31-i2c.yaml` | I2C controller |
| `iio/adc/espressif,esp32s31-adc.yaml` | ADC |
| `iio/dac/espressif,esp32s31-dac.yaml` | DAC |
| `net/wireless/espressif,esp32s31-radio.yaml` | Radio |
| `nvmem/espressif,esp32s31-efuse.yaml` | eFuse |
| `pinctrl/espressif,esp32s31-pinctrl.yaml` | Pin controller and GPIO matrix |
| `power/espressif,esp32s31-pmu.yaml` | Power domains |
| `pwm/espressif,esp32s31-pwm.yaml` | PWM providers |
| `regulator/espressif,esp32s31-ana-i2c.yaml` | Analog-register transport |
| `regulator/espressif,esp32s31-gp-ldo.yaml` | General-purpose LDOs |
| `sound/espressif,esp32s31-i2s.yaml` | I2S controller |
| `spi/espressif,esp32s31-gpspi.yaml` | SPI host and target |

Some devices use generic Linux schemas. Check the node's `compatible` value
and the associated driver when locating its binding.

## Board files and overlays

The base description is `arch/riscv/boot/dts/espressif/esp32s31.dtsi`. Optional
controllers are enabled by `esp32s31-overlay-*.dtso` files in the same
directory. The [overlay guide](../api-guides/adding-an-overlay.md) shows how to
add a controller, pin routes, and user-selectable parameters.

## Validate a change

Use the kernel's `dt_binding_check` target for schema changes and `dtbs_check`
for device-tree changes, with the same RISC-V configuration and toolchain as
the kernel build. These checks require the device-tree schema tools on the
host.

After validation, build the kernel and rootfs to package the updated DTBs and
overlays, then test the device on the board.
