# 添加驱动

在 `linux-esp32-s31` 源码树中添加外设驱动，使用与设备相符的 Linux 子系统，例如 I2C、SPI、ALSA、IIO、PWM、Counter、SocketCAN 或其他标准框架。集成驱动时，一并维护硬件描述、内核构建选项和启用设备的覆盖层。

## 1. 参考完整的集成示例

现有的 I2C0 支持展示了各部分如何配合。下表中的路径均相对于 `linux-esp32-s31`。

| 集成部分 | I2C0 示例 |
| --- | --- |
| 驱动与设备匹配 | [`drivers/i2c/busses/i2c-esp32s31.c`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/i2c-esp32s31.c)：probe、I2C 适配器注册以及 `espressif,esp32s31-i2c` 匹配项。 |
| 绑定 | [`Documentation/devicetree/bindings/i2c/espressif,esp32s31-i2c.yaml`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/devicetree/bindings/i2c/espressif,esp32s31-i2c.yaml)：寄存器、IRQ、时钟、可选复位及总线频率。 |
| 基础硬件节点 | [`arch/riscv/boot/dts/espressif/esp32s31.dtsi`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)：`i2c0` 的寄存器地址为 `0x20385000`，使用矩阵中断源 23，引用时钟和复位资源，默认设置为 `status = "disabled"`。 |
| 启用覆盖层 | [`arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso)：声明资源占用、命名 SCL/SDA 路由、总线频率参数，并设置 `status = "okay"`。 |
| 内核构建 | [`drivers/i2c/busses/Kconfig`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/Kconfig) 定义 `I2C_ESP32S31`；[目录 Makefile](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/Makefile) 选择对应对象文件；[`esp32s31_defconfig`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/configs/esp32s31_defconfig) 启用驱动。 |
| 覆盖层构建 | [`arch/riscv/boot/dts/espressif/Makefile`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/Makefile) 注册 `.dtbo` 构建目标。 |

添加新外设时，先添加或复用相应绑定，在基础设备树中描述实际资源，并为可选硬件提供覆盖层。按照[添加覆盖层](adding-an-overlay.md)说明引脚选择和资源占用声明。设备实际使用 DMA、稳压器或电源域时，再描述相应依赖。

## 2. 获取资源并注册到子系统

I2C 示例的 probe 先映射寄存器资源，获取并启用时钟，注册托管的时钟关闭动作，获取可选复位，然后初始化总线时序。随后，它请求 IRQ 并注册 I2C 适配器。资源提供方返回的错误通过 `dev_err_probe()` 传递；提供方返回 `-EPROBE_DEFER` 时，该错误会得到保留。
[Probe 与清理动作注册](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/i2c-esp32s31.c)。

在适合资源生命周期的地方使用托管辅助函数，并传递资源获取时的实际错误。共享硬件和执行上下文的规则见[时钟、复位与电源](../api-reference/system/clock-reset-power.md)、[中断与 SMP](../api-reference/system/interrupts-smp.md)以及 [DMA 与缓存](dma-and-cache.md)。

设计错误处理、驱动移除和设备挂起路径时，应考虑正在进行的传输。先停止接收新任务，等待硬件和回调停止，再释放资源。如果设备需要保存或恢复状态，应添加挂起和恢复操作。托管分配本身并未规定如何停止活动传输；使用 DMA 时，应遵守 DMA 指南中的终止和同步规则。

## 3. 构建驱动与覆盖层

添加驱动的 Kconfig 依赖和对象文件规则，在 `arch/riscv/configs/esp32s31_defconfig` 或所选 `DEFCONFIG` 中启用驱动，并在 DTS 目录的 Makefile 中注册新的覆盖层目标。主项目的 `linux` 目标会重新应用所选 defconfig，因此应将需要保留的配置更改写入该配置文件。
[主项目的 Linux 构建目标](https://github.com/GrieferPig/esp32-s31-linux/blob/main/mk/linux.mk)。

在主项目目录中构建并烧录完整外设配置。按[烧录指南](../get-started/flash-and-first-boot.md)选择端口并准备串口连接：

```sh
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

`rootfs` 已依赖 `linux`，后者会构建内核、模块和设备树。完整配置保留原生可选外设驱动。根文件系统的 post-build 步骤将构建好的覆盖层安装到 `/usr/lib/s31-overlays`。
[构建配置](https://github.com/GrieferPig/esp32-s31-linux/blob/main/mk/linux.mk)；[Linux 构建产物](https://github.com/GrieferPig/esp32-s31-linux/blob/main/mk/linux.mk)；[rootfs 依赖](https://github.com/GrieferPig/esp32-s31-linux/blob/main/mk/linux.mk)；[覆盖层安装](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/post-build.sh)。

开发板重启后，按照[添加覆盖层](adding-an-overlay.md)中的流程启用覆盖层。

## 4. 验证行为

对于现有的 I2C/SPI 示例，以下主机测试会提取并测试 I2C 命令和长传输逻辑，以及 SPI 目标设备缓冲区的复制逻辑：

```sh
python -m unittest tools.tests.test_s31_feature_contracts.DriverContracts.test_driver_wire_contracts -v
```

[测试框架](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/tests/test_s31_feature_contracts.py)将选定的源码函数与模拟输入一起编译。为新驱动添加测试时，可优先检查能够脱离硬件运行的解析、传输构造和错误处理逻辑。

在开发板上检查覆盖层应用结果和 probe 输出，通过子系统的用户空间 API 操作设备，并使用已知对端或仪器核对数据。测试无效设置、超时恢复、重复传输，以及使用方关闭设备后的驱动移除。如果驱动支持挂起和恢复，应结合预期唤醒源，分别在传输进行中或刚完成时测试该路径。记录结果时，一并记录接线、构建版本和执行命令。
