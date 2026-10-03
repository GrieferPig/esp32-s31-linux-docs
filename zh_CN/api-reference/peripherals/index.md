# 外设

本移植通过 TTY、I2C、SPI、ALSA 和 SocketCAN 等标准 Linux 接口提供外设功能。
使用设备树覆盖层启用可选控制器并选择引脚。

本章中的原生 I2C、SPI、I2S、以太网和 SD/MMC 驱动均包含在统一的[完整配置](../../get-started/build-configuration.md)中；实际外接设备可能需要额外驱动。

## 启用外设

例如，要启用 I2C0：

```sh
s31-overlay apply i2c0
```

该选择会被保存，并在启动时恢复。添加 `--volatile` 可使配置仅临时生效。
查看引脚和可用设置：

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
```

连接设备前请检查开发板原理图。[覆盖层目录](../../resources/overlay-catalog.md)
列出了可用控制器及其配置选项。

接线、命令、预期现象和清理步骤见[外设示例](../../user-guides/peripherals.md)。
GPIO 编号表示 SoC 信号；[开发板默认配置](../../hw-reference/modules-and-boards.md)
列出了随仓库提供的路由和预留资源。

## 接口

| 外设 | Linux 接口 | 覆盖层或设置 |
|---|---|---|
| GPIO | GPIO 字符设备；`gpioinfo`、`gpioget`、`gpioset` | 选择板上的空闲引脚 |
| UART | `/dev/ttyS*` | `uart1`、`uart2`、`uart3` 或 `uart3-dma` |
| I2C | `/dev/i2c-*` | `i2c0` 或 `i2c1` |
| SPI | SPI 子系统；用户空间客户端使用 `/dev/spidev*` | `gpspi2`、`gpspi3` 或对应的目标模式配置 |
| I2S/TDM | ALSA PCM | `i2s0` 或 `i2s1` |
| TWAI/CAN | SocketCAN | `twai0` 或 `twai1`；需要外部收发器 |
| SD/MMC | MMC 块设备 | `sdmmc0`、`sdmmc1`、`sdmmc-dual` 或 `sdmmc-uhs` |
| 以太网 | 网络接口和 PHY 驱动 | `gmac`；需要外部 PHY |
| USB | DWC2 主机或 USB gadget | 主机设置或 `usb-device` |
| GDMA | 内核 DMAengine API | 由客户端选择 AHB/AXI 提供者 |
| 通用定时器 | Counter 框架 | `timers` |
| LEDC、MCPWM、SDM 和脉冲计数器 | PWM 和 Counter 框架 | `pwm-counter` |
| ADC、DAC、触摸、比较器 | IIO | `analog` 和合适的模拟引脚 |
| 温度传感器 | hwmon | `analog` |
| 看门狗 | Watchdog 框架 | `watchdogs` |
| eFuse、随机数、加密 | 只读 NVMEM、hwrng 和内核 crypto API | 对应的内核驱动 |

UART0 用作串口控制台。UART3 的 DMA 覆盖层还会使用 UHCI0 和一个 AHB
GDMA 通道。当前功能状态见[支持矩阵](../../resources/support-matrix.md)。

## I2C

两个 I2C 控制器都支持 7 位和 10 位地址，以及组合写入/读取事务。默认总线
速率为 100 kHz。要选择 400 kHz 并将 I2C0 路由到 GPIO35 和 GPIO36：

```sh
s31-overlay apply i2c0 i2c0.scl=35 i2c0.sda=36 clock-frequency=400000
```

SCL 和 SDA 需要合适的上拉电阻。覆盖层还接受 100000 和 1000000 Hz。

列出适配器：

```sh
i2cdetect -l
```

对于适配器 0 上地址为 `0x51` 的设备，可以在一次事务中先用一个字节选择
寄存器，再读取一个字节：

```sh
i2ctransfer -y 0 w1@0x51 0x00 r1
```

将适配器、地址和寄存器替换为你的设备对应的值。在 C 中，使用 `I2C_RDWR`
执行这一组合操作，使写入和读取之间以重复 START 分隔。

### 传输限制和错误

用户空间 `I2C_RDWR` 的每条消息最多可包含 8192 字节。内核客户端使用 16 位
消息长度，最多允许 65535 字节。支持零长度写入；不支持零长度读取和协议修改标志。

长传输会分批处理，每批最多发送 32 字节或接收 31 字节。控制器在批次之间
保持总线，并在最后一条消息之后发送 STOP。每批的完成超时时间为 500 ms。

| 错误 | 含义 |
|---|---|
| `ENXIO` | 目标未应答 |
| `EAGAIN` | 丢失仲裁 |
| `ETIMEDOUT` | 硬件超时或等待完成超时 |
| `EIO` | 接收 FIFO 计数异常 |

驱动包含总线恢复功能。如果反复超时，还应检查上拉电阻、接线、总线速率和
目标设备的行为。

## SPI

GPSPI2 和 GPSPI3 均可作为主机或目标端运行。根据控制器实例和角色选择
对应的覆盖层，例如 `gpspi2` 或 `gpspi2-target`。

主机客户端使用 Linux SPI API。使用 spidev 的应用通过其 ioctl 选择模式、
时钟速率和传输缓冲区。**主机模式只接受 8 位字长。** 随仓库提供的主机覆盖层
为 spidev 子节点设置了 20 MHz 的最高速率；请求的速率还必须处于控制器的
时钟范围内。[主机回环示例](spi-host-loopback)
从 100 kHz 开始。

### 目标模式传输

目标模式等待外部主机提供时钟和片选。它支持模式 0–3、高电平有效的片选，
以及 8、16 或 32 位字长。传输长度必须为字长的整数倍。

| 设置 | 限制 |
|---|---|
| DMA 传输 | 4096 字节 |
| 仅使用 FIFO 的传输 | 64 字节 |
| 等待外部主机 | 可中断；无固定超时 |
| 事务结束后等待 DMA 完成 | 每个需要的传输方向为 100 ms |

目标端将 Linux 小端序数据字转换为选定的总线字节序。对于 16 位和 32 位的
MSB 优先传输，发送时会反转每个字内的字节顺序，接收时再转换回来。

拉有效片选前，应留出足够时间让目标端准备好每次传输。需要就绪信号的应用
应单独实现握手。目标模式使用单数据通道，没有独立的命令、地址或空周期阶段。

等待被中断或取消时返回 `EINTR`。事务长度异常时返回 `EMSGSIZE`，
DMA 完成超时时返回 `ETIMEDOUT`。

## I2S 和 TDM

I2S0 和 I2S1 使用 ALSA SoC，通过 GDMA 支持播放和录音。启用对应的覆盖
配置后，列出 PCM 设备：

```sh
aplay -l
arecord -l
```

在应用中使用输出里的声卡和设备编号。随仓库提供的 `i2s0` 和 `i2s1` 覆盖层
在播放和录音两个方向都接收外部 BCLK 和帧时钟，需要由 codec 或测试对端
产生时钟。如果 DAC 也需要接收这两个时钟，就必须使用不同的声卡和引脚配置，
具体见[完整音频示例](audio-with-an-external-codec)。

### PCM 设置

| 设置 | 可用值 |
|---|---|
| 采样格式 | `S8`、`S16_LE`、`S24_LE`、`S32_LE` |
| 采样率 | 8–192 kHz，受时钟和声卡配置限制 |
| 通道数 | 1–16 |
| 周期大小 | 256–4032 字节 |
| 每个缓冲区的周期数 | 2–8 |

播放和录音共用 MCLK，同时配置两个流时必须使用相同的采样率。两个流还需
使用兼容的时钟设置。ALSA 负责非一致性 DMA 缓冲区的缓存同步。

### 帧格式和时钟

CPU DAI 支持 I2S、左对齐、DSP A 和 DSP B 帧格式。它可以同时提供 BCLK
和帧时钟，也可以同时接收另一设备提供的这两个时钟。支持帧时钟反相，
目前不支持混合时钟角色、位时钟反相和外部 MCLK 输入。

`set_sysclk()` 使用 ID 0 和 `SND_SOC_CLOCK_OUT` 配置内部 MCLK。速率设为
零时自动选择 MCLK。接收外部 BCLK 时，内部模块时钟必须至少达到 BCLK 的八倍。

### TDM 时隙

使用 `set_tdm_slot()` 选择 1–16 个时隙，每个时隙宽度为 8–32 位。时隙宽度
必须能容纳采样数据，每帧的总位数必须为偶数。非零的 TX/RX 掩码选择活动
时隙，每个 PCM 通道必须对应一个置位位。将时隙数和掩码都设为零，可清除
显式时隙设置。

更改格式、时隙或 MCLK 之前，先释放已配置的流。允许重新应用相同的设置。

### 连接外部 codec

带外部 codec 的开发板应使用 ASoC machine 驱动，例如 `simple-audio-card`。
向所选控制器添加以下属性：

```dts
&i2s0 {
    #sound-dai-cells = <0>;
    espressif,external-card;
    status = "okay";
};
```

然后在 machine 声卡中描述 CPU/codec 链路、引脚、帧格式、时钟，以及需要的
TDM 设置。`espressif,external-card` 会禁用内置虚拟声卡，让外部声卡使用该
控制器。还需在内核配置中启用 machine 驱动和所选 codec 的驱动；完整外设
配置本身不会选择 `CONFIG_SND_SIMPLE_CARD` 或真实 codec。machine 驱动的
格式设置会选择两个方向的时钟角色。随仓库提供的虚拟声卡覆盖层在两个方向
都使用时钟输入。

驱动中也提供原始 PDM 选项；这些选项不提供 PCM 到 PDM 的转换。

## 存储、网络和其他外设

SD 卡使用 MMC 块层，TWAI 使用 SocketCAN，以太网使用常规 Linux 网络接口。
对应的覆盖层选择控制器和引脚，底板则提供卡座、收发器或 PHY。

基础设备树启用 DWC2 主机模式，包含 USB 存储路径。`usb-device` 覆盖层选择
gadget 模式，随后还需配置 gadget 功能并将其绑定到 UDC。切换角色之前，
请卸载 USB 文件系统并禁用位于 USB 存储上的 swap。
[存储和 gadget 示例](../../user-guides/peripherals.md)给出了配置与清理步骤；
实现是否存在与支持矩阵中记录的硬件状态是两个不同的问题。

定时和模拟设备使用各自的 Linux 子系统接口。在 `timers` 覆盖层中，
每个定时器组的定时器 0 可供应用使用，定时器 1 则保留用于 CPU 空闲唤醒。
模拟和数字信号路由可能共用物理焊盘，因此每个引脚只应选择一种功能。

驱动源码位于 `linux-esp32-s31/drivers/`，音频驱动位于
`sound/soc/espressif/`。集成步骤见[添加驱动](../../api-guides/adding-a-driver.md)。
