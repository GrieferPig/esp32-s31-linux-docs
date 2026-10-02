# 设备树绑定

设备树绑定描述预期的设备树 ABI。添加开发板、选择外设资源或编写覆盖层时，
应查阅这些绑定，并结合对应驱动和现有设备树节点了解实现细节。存在 schema
文件并不代表它覆盖了所有属性，也不代表已经通过验证。

以下 S31 schema 位于 `linux-esp32-s31/Documentation/devicetree/bindings/` 下：

| Schema | 设备 |
|---|---|
| `clock/espressif,esp32s31-clk.yaml` | 时钟和复位控制器 |
| `counter/espressif,esp32s31-gptimer.yaml` | 通用定时器 |
| `counter/espressif,esp32s31-pcnt.yaml` | 脉冲计数器 |
| `hwmon/espressif,esp32s31-tsens.yaml` | 温度传感器 |
| `i2c/espressif,esp32s31-i2c.yaml` | I2C 控制器 |
| `iio/adc/espressif,esp32s31-adc.yaml` | ADC |
| `iio/dac/espressif,esp32s31-dac.yaml` | DAC |
| `net/wireless/espressif,esp32s31-radio.yaml` | 无线 |
| `nvmem/espressif,esp32s31-efuse.yaml` | eFuse |
| `pinctrl/espressif,esp32s31-pinctrl.yaml` | 引脚控制器和 GPIO 矩阵 |
| `power/espressif,esp32s31-pmu.yaml` | 电源域 |
| `pwm/espressif,esp32s31-pwm.yaml` | LEDC 和 MCPWM 提供者 |
| `regulator/espressif,esp32s31-ana-i2c.yaml` | 模拟寄存器 I2C 的共享供电/复位调节器 |
| `regulator/espressif,esp32s31-gp-ldo.yaml` | 通用 LDO |
| `sound/espressif,esp32s31-i2s.yaml` | I2S 控制器 |
| `spi/espressif,esp32s31-gpspi.yaml` | SPI 主机和目标端 |

部分设备使用通用 Linux schema。查找绑定时，请检查节点的 `compatible` 值和对应驱动。

## 开发板文件和覆盖层

基础硬件描述为 `arch/riscv/boot/dts/espressif/esp32s31.dtsi`。
同一目录下的 `esp32s31-overlay-*.dtso` 文件用于启用可选控制器。
[覆盖层指南](../api-guides/adding-an-overlay.md)介绍了如何添加控制器、引脚路由和用户可选参数。

## 验证更改

修改 schema 后，使用内核的 `dt_binding_check` 目标检查；修改设备树后，使用 `dtbs_check` 检查。
检查时使用与内核构建相同的 RISC-V 配置和工具链。主机上需要安装设备树 schema 工具。

验证后，构建内核和 rootfs，将更新后的 DTB 和覆盖层打包，再在开发板上测试设备。
