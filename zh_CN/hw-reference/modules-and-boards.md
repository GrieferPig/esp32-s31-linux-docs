# 模组和开发板

本移植面向 ESP32-S31 平台。[项目 README](https://github.com/GrieferPig/esp32-s31-linux/blob/main/README.md)
列出以下目标开发板和模组：

- 乐鑫 ESP32-S31 Coreboard
- 乐鑫 ESP32-S31 Korvo
- 乐鑫 ESP32-S31-WROOM-3 E1H16R16V 模组

请根据底板原理图确认接口、电源输入及下载/复位按钮。下表使用 SoC 的 GPIO
编号，接线前请将其与开发板上的排针标识对应。

## 连接控制台

默认控制台使用 UART0，波特率为 115200，格式为 8N1。通过开发板的 USB-UART
控制台接口连接。S31 使用 GPIO58 发送，使用 GPIO59 接收。

基础配置保留了以下引脚：

| GPIO | 在基础配置中的用途 |
|---|---|
| 26–32 | 为运行中的 flash/XIP 接口保留的引脚组 |
| 33、34 | USB Serial/JTAG |
| 41 | GPIO 驱动和覆盖层工具禁止使用 |
| 58 | UART0 TX，控制台输出 |
| 59 | UART0 RX，控制台输入 |

这些保留项来自[基础 GPIO 配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)
和[覆盖层引脚检查](https://github.com/GrieferPig/esp32-s31-linux/blob/main/rootfs/s31_overlay.c)。
GPIO 驱动的有效引脚掩码还排除了 GPIO29；它已包含在保留的 26–32 引脚组中。

## 连接外设

以下默认值适用于启用相应的[预置覆盖层](https://github.com/GrieferPig/linux-esp32-s31/tree/v6.18-esp32-s31/arch/riscv/boot/dts/espressif)
且未覆盖引脚分配的情况。可选控制器还需要
[完整开发板配置](../get-started/build-configuration.md)中的相应驱动。

### 通过矩阵路由的信号

| 覆盖层 | 默认信号及 GPIO | 接线说明 |
|---|---|---|
| `uart1` | TX 42，RX 43 | TX 接对端 RX，RX 接对端 TX |
| `uart2` | TX 44，RX 45 | 与 `uart1` 的默认路由使用不同引脚 |
| `uart3`、`uart3-dma` | 未提供外部引脚路由 | HIL 测试程序对这两个覆盖层使用内部回环 |
| `i2c0` | SCL 35，SDA 36 | 检查外设的上拉要求 |
| `i2c1` | SCL 44，SDA 45 | 与 `uart2` 的默认引脚相同 |
| `gpspi2`、`gpspi3` | SCLK 42，MOSI 43，MISO 45，低有效 CS 44 | 主机模式；两个覆盖层使用相同的默认 GPIO |
| `gpspi2-target` | SCLK 43，MOSI 40，MISO 42，CS0 44 | 外部主机驱动 SCLK、MOSI 和 CS0 |
| `gpspi3-target` | SCLK 46，MOSI 40，MISO 42，CS0 47 | 外部主机驱动 SCLK、MOSI 和 CS0 |
| `i2s0`、`i2s1` | BCLK 输入 42，WS 输入 43，数据输出 44，数据输入 45 | 预置覆盖层中的播放和采集均使用外部时钟 |
| `twai0` | TX 46，RX 47 | 通过适用的 CAN 收发器连接 |
| `twai1` | TX 48，RX 49 | 通过适用的 CAN 收发器连接 |

接线前，查看镜像中打包的默认路由：

```sh
s31-overlay routes i2c0
```

如果应用覆盖层时指定了引脚分配，请按指定的分配接线。多个覆盖层共用默认
GPIO，同时启用前需要选择互不冲突的引脚。覆盖层管理器会检查 GPIO 和资源
冲突。路由名称和命令语法见[覆盖层目录](../resources/overlay-catalog.md)。

### 固定引脚组

| 覆盖层 | GPIO 组 | 用途 |
|---|---|---|
| `sdmmc0`、`sdmmc-uhs` | CLK 24；CMD 25；DAT0–DAT3：20、21、22、23 | 插槽 0，默认使用四条数据线 |
| `sdmmc1` | CLK 39；CMD 40；DAT0–DAT3：35、36、37、38 | 插槽 1，默认使用四条数据线 |
| `sdmmc-dual` | 上述两个 SDMMC 引脚组 | 两个插槽 |
| `gmac` | 管理接口 5–6；PHY 复位 7；RGMII 发送引脚组 8–13；接收引脚组 14–19 | 见[以太网信号表](ethernet-default-pins)；需要 PHY 和相匹配的开发板接线 |
| `analog` | DAC 4–5；触摸 6–19；比较器 37–40；ADC 42–57 | 即使应用只使用一个功能，覆盖层也会占用整组引脚 |

SDMMC 和以太网信号组定义在[基础 pinctrl 配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)中。
各条 SDMMC 信号与固定版本的
[ESP-IDF 插槽定义](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/components/esp_hal_sd/esp32s31/include/soc/sdmmc_pins.h#L9-L23)一致。
预置 `analog` 覆盖层与多个总线的默认引脚冲突；只需要其中一部分功能时，
请使用缩小引脚范围的自定义覆盖层。

(ethernet-default-pins)=

### 以太网信号

默认 `gmac` 路由使用以下 SoC GPIO。请在底板原理图上逐一核对各信号与 PHY
的连接。

| 信号 | 默认 GPIO | 在 S31 端的方向 |
|---|---|---|
| MDC | 5 | 输出 |
| MDIO | 6 | 双向 |
| PHY 复位 | 7 | 低有效输出 |
| TXD0、TXD1、TXD2、TXD3 | 8、9、10、11 | 输出 |
| TX_CTL | 12 | 输出 |
| TXC | 13 | 输出 |
| RXC | 14 | 输入 |
| RX_CTL | 15 | 输入 |
| RXD0、RXD1、RXD2、RXD3 | 19、18、17、16 | 输入 |

RXD0–RXD3 对应的 GPIO 编号按降序排列。信号名称和时钟方向依据固定版本的
[ESP-IDF RGMII 映射](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/components/esp_hal_emac/esp32s31/emac_periph.c#L190-L401)；
Linux 设备树提供上述路由和
[PHY 复位配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)。

### PWM 和计数器默认引脚

`pwm-counter` 覆盖层会一并启用以下路由：

| 信号 | 默认 GPIO |
|---|---|
| `ledc0.out`、`ledc1.out` | 20、21 |
| `mcpwm0.out`、`mcpwm1.out`、`mcpwm2.out`、`mcpwm3.out` | 42、23、24、25 |
| `mcpwm0.capture0`、`mcpwm0.fault0`、`mcpwm0.sync0` | 40、39、38 |
| `sdm.out`、`pcnt0.in`、`pcnt1.in` | 35、36、37 |

引脚分配和 GPIO 占用声明见
[`pwm-counter` 覆盖层](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-pwm-counter.dtso)。

应用覆盖层前，连接公共地，并检查外设的电压要求、上拉电阻、收发器、codec
或 PHY。配置示例见[使用外设](../user-guides/peripherals.md)。

## 使用其他内存配置

提供的镜像使用固定的 16 MiB flash 布局和 16 MiB PSRAM 映射。要支持其他
容量，需要在烧录前修改启动配置、设备树和镜像布局。

见 [Flash 布局](flash-layout.md)和[内存映射](memory-map.md)。
