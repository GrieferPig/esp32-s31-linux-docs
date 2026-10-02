# 硬件在环测试

HIL 工具在 ESP32-S31 开发板上运行检查；有线或无线对端测试还需要一块可编程测试板。主机脚本控制串口控制台并保存结果。

## 测试工具

| 工具 | 运行位置 | 用途 |
|---|---|---|
| `tools/hil/s31_hil.py` | 主机电脑 | 选择并协调测试用例 |
| `s31-hil-agent` | ESP32-S31 Linux | 运行板端检查 |
| `tools/hil/esp32p4-tester/` | ESP32-P4 测试板 | 提供 GPIO、串口、总线等对端功能 |

P4 测试程序在测试启用输出前，保持夹具输出禁用，并在测试结束后恢复禁用状态。夹具接线和固件说明见其 [README](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/hil/esp32p4-tester/README.md)。

## 1. 运行主机测试

在主仓库工作目录中运行：

```sh
make check-host
```

该目标包含功能契约、selftest、覆盖层和 BTstack 回归测试。功能测试使用主机
C 编译器检查 I2C 命令生成、SPI 字序和 I2S 配置，并检查 EAP 凭据配置。
BTstack 测试使用目标依赖步骤获取的源码。前置条件及完整的 `check-fast`
流程见[开发环境](development-setup.md)。主机测试通过与开发板测试证据是两回事。

## 2. 准备开发板

构建完整外设镜像并烧录 S31：

```sh
export S31_LEAN_RADIO=0
make all
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

请将 `PORT` 替换为 S31 串口设备。`make all` 在主机上构建镜像；
`make flash-all` 重新构建依赖并写入开发板。完成
[首次登录和启动检查](../get-started/flash-and-first-boot.md)后，为需要对端的用例
安装 P4 测试固件。按引脚表连接夹具，确保共地且信号电压兼容。启动主机测试程序前，关闭串口监视程序。

查看测试程序支持的用例和串口选项：

```sh
python3 tools/hil/s31_hil.py --help
```

## 3. 运行测试

使用两块开发板进行有线 I2C 测试：

```sh
mkdir -p logs
python3 tools/hil/s31_hil.py --board both --case i2c \
  --output logs/hil-i2c.json
```

以 400 kHz 重复测试：

```sh
python3 tools/hil/s31_hil.py --board both --case i2c \
  --i2c-speed 400000 --repeat 12 --output logs/hil-i2c-repeat.json
```

其他有线用例包括 `gpio`、`uart`、`spi`、`i2s` 和 `pwm-pcnt`。`spi-stress` 和 `i2s-stress` 使用更长的传输来评估性能和行为。

仅检查 S31 时，选择 `--board s31`：

```sh
python3 tools/hil/s31_hil.py --board s31 --case lp-core \
  --output logs/hil-lp-core.json
python3 tools/hil/s31_hil.py --board s31 --case smp-irq-dma \
  --output logs/hil-smp-irq-dma.json
```

主机测试程序和目标端代理的命令行选项不同。在电脑上控制测试时，请使用上面的主机程序示例。

## 存储测试

运行 `sdmmc` 或 `usb-drive` 前，插入相应的存储设备：

```sh
python3 tools/hil/s31_hil.py --board s31 --case sdmmc
python3 tools/hil/s31_hil.py --board s31 --case usb-drive
```

如果没有已激活的 `sdmmc0` 覆盖层，SD/MMC 用例会临时应用
`sdmmc0 bus-width=1`，用于 1 位 CLK/CMD/DAT0 接线。已有的覆盖层保持不变，
因此请核对其总线宽度和路由是否符合实际接线。该用例从卡中读取 1 MiB 数据。USB 用例默认只读。若要在数据可丢弃的测试盘上启用临时 64 KiB 写入测试，请添加 `--allow-usb-write`。

## 无线测试

连接 P4/C6 无线对端后，运行：

```sh
python3 tools/hil/s31_hil.py --board both --case c6-wifi \
  --peer-connected --output logs/hil-wifi.json
python3 tools/hil/s31_hil.py --board both --case c6-ble \
  --peer-connected --output logs/hil-ble.json
```

Wi-Fi 用例设置夹具接入点和临时 STA 配置，然后检查关联、地址分配和数据包交换。它还会临时更改无线服务，并在清理时恢复。

进行电源管理测试前，先查看当前的[挂起限制](../api-guides/power-management.md)。GPIO 唤醒需要连接 LP GPIO0–7，而不是夹具通常使用的较高编号引脚。

## 查看结果

开发板结果使用 `HIL1` JSON 记录。测试报告 PASS、FAIL 或 SKIP，并附上操作、证据级别和简短说明。
probe 级别的 PASS 表示注册或存在性检查通过；data 级别的 PASS 表示该条结果
所指的操作检查通过。两者都不能证明未经测试的模式或外设已正常工作。开始下一个用例前，请检查失败或跳过的前置条件，以及清理阶段的错误。

保存输出文件，并简要记录开发板、固件构建、接线和所用命令。数据传输测试应附上对端结果；电源测试应另外记录唤醒原因和电流测量值。如果结果改变了文档中的功能状态，请更新[支持矩阵](../resources/support-matrix.md)。

## 添加测试用例

添加测试所需的主机操作序列、S31 操作和对端响应。为等待设置超时，并为成功、错误和中断情况编写清理逻辑。有效的用例应检查返回数据或设备的实际行为；缺少必要设备或夹具时，应给出明确说明。
