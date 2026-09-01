# Devicetree Binding Index

The kernel contains dedicated ESP32-S31 YAML schemas in these subsystem
directories:

| Binding | Function |
|---|---|
| `clock/espressif,esp32s31-clk.yaml` | Clock/reset controller |
| `counter/espressif,esp32s31-gptimer.yaml` | General-purpose timers |
| `counter/espressif,esp32s31-pcnt.yaml` | Pulse counters |
| `hwmon/espressif,esp32s31-tsens.yaml` | Temperature sensor |
| `i2c/espressif,esp32s31-i2c.yaml` | I2C controllers |
| `iio/adc/espressif,esp32s31-adc.yaml` | ADC |
| `iio/dac/espressif,esp32s31-dac.yaml` | DAC |
| `net/wireless/espressif,esp32s31-radio.yaml` | Radio core/frontends |
| `nvmem/espressif,esp32s31-efuse.yaml` | eFuse provider |
| `pinctrl/espressif,esp32s31-pinctrl.yaml` | Pin controller and matrix routes |
| `power/espressif,esp32s31-pmu.yaml` | PMU domains |
| `pwm/espressif,esp32s31-pwm.yaml` | LEDC/MCPWM/SDM PWM providers |
| `regulator/espressif,esp32s31-ana-i2c.yaml` | Analog-register transport |
| `regulator/espressif,esp32s31-gp-ldo.yaml` | General-purpose LDOs |
| `sound/espressif,esp32s31-i2s.yaml` | I2S controller |
| `spi/espressif,esp32s31-gpspi.yaml` | GPSPI controller/target |

Other S31 nodes use generic subsystem schemas where their properties follow an
existing Linux binding. Every new compatible must either select an appropriate
generic schema or add a dedicated YAML schema. Run `dt_binding_check` and
`dtbs_check` for the affected files.

The base DTS defines providers and disabled optional nodes. Overlay files
enable complete functional groups; applications must not create undocumented
live-tree nodes with arbitrary properties.
