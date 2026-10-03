# 使用外设

这些示例适用于完整外设镜像。目标端命令在 S31 上以 root 身份运行；明确标注
为构建命令的步骤在 Linux 构建主机上执行。按[从源码构建](../get-started/build-from-source.md)
准备完整匹配镜像集。rootfs 包含 libgpiod v2 工具、I2C 工具、
`spidev_test`、`aplay`/`arecord`、`candump` 和 `cansend`。下文 CAN 示例还需要
完整的 iproute2，外部 codec 示例则需要额外的内核选项。

示例依据驱动、随仓库提供的覆盖层，以及现有辅助程序/HIL 用法编写。
已记录的硬件状态见[支持矩阵](../resources/support-matrix.md)，
控制器限制和错误说明见[外设参考](../api-reference/peripherals/index.md)。

(peripheral-setup)=

## 连接前的准备

先用[开发板默认路由](../hw-reference/modules-and-boards.md)确定 SoC GPIO 编号，
再用自己开发板的原理图找到对应焊盘或连接器引脚。仓库没有提供完整的排针
映射。应匹配信号电平，并在需要时共地。

每次只运行一个示例：UART1、SPI2 和 I2S0 默认配置会复用 GPIO42–45。
先查看活动覆盖层和可用路由：

```sh
s31-overlay list
s31-overlay routes uart1
s31-overlay routes gpspi2
s31-overlay routes i2s0
```

继续前先停止占用冲突引脚的程序，并移除相应的临时覆盖层。各示例都使用
`--volatile`，不会更改已保存的启动选择。启动时恢复的持久覆盖层仍可能与
临时示例冲突。应用命令失败时应停止，不要继续假定设备或引脚路由已经生效。

## 配置 GPIO

在 `esp32-config` 中选择 **Interfaces → GPIO**，选中引脚并设置模式：

| 模式 | 效果 |
|---|---|
| Application controlled | 释放引脚，交给应用或驱动使用 |
| Input | 保持输入模式，可选择无上下拉、上拉或下拉 |
| Output low | 保持逻辑 0 输出 |
| Output high | 保持逻辑 1 输出 |

选择 **Save and apply** 后立即生效，并在 Linux 启动时恢复。
提交前返回会放弃本页编辑。引脚列表显示当前用途，以及尚未成功应用的保存设置。
配置工具不能申请保留引脚，也不能占用其他应用或接口正在使用的引脚。

例如，GPIO42 空闲时：

```sh
esp32-config gpio list
esp32-config gpio set 42 high
```

退出命令或菜单后，输出仍会保持。将 GPIO43 配置为上拉输入，再读取电平：

```sh
esp32-config gpio set 43 input up
esp32-config gpio read 43
```

辅助服务运行期间会持续持有这些 GPIO 请求。
通过 libgpiod 或其他接口使用这些引脚前，先释放它们：

```sh
esp32-config gpio set 42 application
esp32-config gpio set 43 application
```

选择应用控制会移除该引脚的保存配置。释放后不保证保持某个电平。
启动恢复从 Linux 服务开始运行时生效；如果上电起就需要确定的电平，
应通过板级电路或更早运行的固件处理。

## 在应用中使用 GPIO

确认 GPIO42 和 GPIO43 空闲后，将 GPIO42 接到 GPIO43，构成数字回环。
先查看线路：

```sh
gpioinfo -c gpiochip0
```

在一个终端中，将 GPIO42 保持为高电平：

```sh
gpioset -c gpiochip0 42=1
```

在另一个终端读取 GPIO43，应报告有效/高电平输入：

```sh
gpioget --unquoted -c gpiochip0 43
```

在第一个终端按 Ctrl-C 释放输出请求，再使用 `42=0` 重复测试；GPIO43 应报告
无效/低电平。Ctrl-C 会释放线路，应用不能依赖释放后的输出电平。将这些引脚
分配给外设之前，先拆除回环线。

这些命令使用[GPIO HIL 执行器](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/hil/s31_hil.py)
采用的 libgpiod v2 语法。

## UART1 接线回环

随仓库提供的 `uart1` 覆盖层将 TX 路由到 GPIO42、RX 路由到 GPIO43。
将两者连接起来，确保 RX 上没有其他发送器驱动，然后执行：

```sh
s31-overlay apply uart1 --volatile
s31-hil-io uart /dev/ttyS1 115200 256
s31-overlay remove uart1 --volatile
```

辅助程序将串口设为原始模式、115200 波特率，发送 256 字节的测试模式并逐字节
比较回传数据。成功时输出 `PASS uart`；未接线、超时或数据不匹配都会使命令
失败。这里使用物理回传路径；`uart-loopback` 是辅助程序中另一种内部回环操作。
连接外部 UART 设备时，将设备 TX 接到 S31 RX、设备 RX 接到 S31 TX，并匹配
帧格式和波特率。保留 UART0 用作控制台。
参见[UART 辅助程序实现](https://github.com/GrieferPig/esp32-s31-linux/blob/main/rootfs/s31_hil_io.c)
和[UART1 路由](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-uart1.dtso)。

(spi-host-loopback)=

## SPI 主机：接线回环

未修改的 `gpspi2` 覆盖层使用 GPIO42 作为 SCLK、GPIO43 作为 MOSI、GPIO44
作为 CS0、GPIO45 作为 MISO。此回环只需将 MOSI 接到 MISO。以 100 kHz
运行 8 位传输：

```sh
s31-overlay apply gpspi2 --volatile
spidev_test -D /dev/spidev2.0 -s 100000 -b 8 -v -p '\x01\x02\x03\x04'
s31-overlay remove gpspi2 --volatile
```

详细输出中的 TX 和 RX 字节序列应一致。连接真实外设时，先拆除回环线，按
需要连接 SCLK/MOSI/MISO/CS，并使用该外设规定的模式、事务格式和允许的
时钟速率。主机驱动只接受 8 位字长；16/32 位支持属于目标模式。随仓库提供的
spidev 子节点还将传输速率限制为最高 20 MHz。

现有 `s31-hil-io spi` 辅助程序要求外部响应器返回特定的变换后模式，不能用它
检查 MOSI/MISO 原样回传。来源：[主机字长掩码](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/spi/spi-esp32s31.c)、
[覆盖层默认配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-gpspi2.dtso)、
[spidev_test 选项](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/tools/spi/spidev_test.c)。

## SD 卡和 USB 存储

修改或关闭 SDMMC 接口前，先卸载 SD 文件系统并停用 SD 上的 swap。
两个卡槽共用控制器，因此需要检查两个卡槽。
任一 SD 卡仍被挂载或用于 swap 时，配置菜单会拒绝改动；保存未修改的设置不会重启控制器。

以下命令假定介质上已有 FAT 分区。先查看检测到的设备，必要时替换示例分区名；
如果文件系统直接位于整个设备上，应使用磁盘节点而不是带 `p1`/`1` 的分区节点。

使用 SDMMC0 时，将合适的卡座连接到开发板表格中的固定引脚。默认覆盖层选择
4 位总线；仅接了 1 位数据线的卡座需要在应用时指定 `bus-width=1`。
即使 DAT3 未连接到 S31，也要确保卡座在卡的 DAT3 引脚上提供 10 kΩ 上拉电阻。
初始化时 DAT3 必须保持高电平，卡才能进入原生 SD 模式；未接到卡的 S31 焊盘
上的上拉无法作用于卡引脚。参见固定版本的
[S31 SD 卡接线及 1 位模式说明](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/examples/storage/sd_card/sdmmc/README.md#L92-L108)
和 Linux 的 [SD 初始化要求](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/mmc/core/mmc_ops.c)。
完成卡座接线和供电后，执行：

```sh
s31-overlay apply sdmmc0 --volatile
ls /sys/class/mmc_host
cat /proc/partitions
mkdir -p /mnt/sd
mount -t vfat -o ro /dev/mmcblk0p1 /mnt/sd
ls /mnt/sd
umount /mnt/sd
s31-overlay remove sdmmc0 --volatile
```

基础设备树选择 USB 主机模式。确认 `usb-device` 未处于活动状态，通过开发板
的 DWC2 主机连接接入存储设备，并在挂载前查看新增磁盘：

```sh
cat /proc/partitions
dmesg | tail -n 30
mkdir -p /mnt/usb
mount -t vfat -o ro /dev/sda1 /mnt/usb
ls /mnt/usb
umount /mnt/usb
```

成功列出目录表示已经能访问该文件系统。若未枚举出设备，应检查供电、接线、
驱动探测消息和当前 USB 角色。若磁盘已出现但挂载失败，应检查分区和文件系统
类型。完整内核包含 VFAT 和 EXT4；本示例以只读方式挂载 VFAT。
仓库还提供了[SD 读取和 USB 挂载 HIL 用例](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/overlay/usr/bin/s31-hil-agent)。

(audio-with-an-external-codec)=

## 连接外部 codec 播放音频

请参阅[连接外部 codec 播放音频](audio.md)，完成 PCM5102A 播放集成，
包括接线、内核选项、声卡 overlay 和播放检查。该指南还说明了如何使用
仓库提供的、接收外部时钟的 I2S overlay 进行录音。

## USB CDC ACM gadget

请参阅 [USB CDC ACM gadget](usb-gadget.md)，切换 DWC2 角色、
配置串口功能、确定其设备节点，并在清理后恢复 host 模式。

## 通过外部收发器使用 CAN

按照开发板表格，将 TWAI0 TX/RX 接到合适的 CAN 收发器，再连接终端电阻正确
配置、且有另一个活动节点的总线。两个节点必须使用相同的位速率。另一节点
提供应答，也可发送已知帧用于接收检查。

rootfs 选择了 `candump` 和 `cansend`，但当前源 defconfig **没有选择 iproute2**。
使用下方 `ip ... type can` 命令之前，应在主机上的
`buildroot-external/configs/esp32s31_rootfs_defconfig` 中，用以下设置替换现有的
禁用项，运行 `make buildroot-reconfigure`，再用 `make image` 构建完整匹配集并通过 `make flash-existing-all` 烧录：

```text
BR2_PACKAGE_IPROUTE2=y
```

在 S31 上配置 500 kbit/s 总线：

```sh
s31-overlay apply twai0 --volatile
ip link set can0 type can bitrate 500000
ip link set can0 up
ip -details -statistics link show can0
candump can0
```

保持 `candump` 运行，在第二个终端发送以下帧并在对端查看。再让对端发回
一个已知帧，检查 `candump` 输出：

```sh
cansend can0 123#11223344
```

按 Ctrl-C 停止 `candump`，然后释放接口：

```sh
ip link set can0 down
s31-overlay remove twai0 --volatile
```

若发送失败，应检查错误计数器及对端接收情况。支持矩阵仍将 CAN 列为开发中。来源：
[rootfs 软件包选择](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/configs/esp32s31_rootfs_defconfig)、
[SocketCAN 位速率设置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/networking/can.rst)。

## 使用仓库提供的 PHY 配置连接以太网

`gmac` 覆盖层启用基础 RGMII 配置，针对 MDIO 地址为 0、复位使用 GPIO7 的
YT8531DC-CA PHY。请结合开发板
表格和基础 DTS，匹配 RGMII/MDIO 接线、PHY 地址、复位与延时；使用不同 PHY
时应编写相应的板级设备树。

在匹配的开发板上连接有 DHCP 服务的网络后：

```sh
s31-overlay apply gmac --volatile
ip link set eth0 up
cat /sys/class/net/eth0/carrier
udhcpc -n -q -i eth0
ip addr show dev eth0
```

载波状态应变为 `1`，成功的 DHCP 交互会分配地址。使用该地址与已知对端交换
数据包。若 DHCP 失败，应分别检查
链路状态和网络地址服务。关闭使用以太网的应用后：

```sh
ip link set eth0 down
s31-overlay remove gmac --volatile
```

此示例依据[具体 PHY 描述](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)
和[现有以太网探测/链路检查](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/overlay/usr/bin/s31-hil-agent)。
报告硬件结果时，请记录开发板版本、PHY、内核/构建配置、链路对端和观察结果。

```{toctree}
:hidden:

audio
usb-gadget
```
