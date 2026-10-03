# USB 功能

在 `esp32-config` 中选择 **Interfaces → USB**，可设置主机模式、串口连接或 USB 网络。
统一的[完整镜像](../get-started/build-configuration.md)包含相应控制器和 gadget 支持；
菜单只提供当前镜像中可用的功能。以下开发板命令以 root 身份运行。

这些设置控制 DWC2。固定的 USB Serial/JTAG 端口属于另一个外设。
请通过开发板原理图确认 DWC2 的连接，并在切换角色时保留独立控制台。

## 选择 USB 功能

| 选择 | 用途 |
|---|---|
| Host | 连接 USB 外设，包括存储设备 |
| USB serial connection | CDC ACM 应用串口或 Linux 登录控制台 |
| USB network connection (ECM) | 与安装 ECM 驱动的电脑建立直接 IPv4 连接 |

从主机模式切换为设备功能前，先卸载全部 USB 文件系统并停用 USB swap。
由工具管理的设备可按[内存与存储](memory-and-storage.md)操作。
这些设备仍在使用时，工具会拒绝角色切换。
连接设备模式线缆前，先断开主机模式外设。

选择的模式会保存，并在启动时恢复。应用不同的 USB 功能会断开当前 USB 连接。

## USB 串口

选择 **USB serial connection**，再选择 **Application serial port** 或
**Linux login console**。通过命令行启用登录控制台：

```sh
esp32-config usb configure serial 1
esp32-config usb status
```

将 DWC2 端口连接到电脑，打开新枚举的串口。
登录控制台使用开发板的账户凭据。应用串口使用 `serial 0`；
应用打开 `usb status` 显示的板端 `/dev/ttyGSN` 路径。

端口编号从 ACM 功能读取。固定 USB Serial/JTAG 驱动已使用 `ttyGS0` 时，
实际编号可能不同。

## USB 网络

选择 **USB network connection (ECM)** 并设置开发板地址，或运行：

```sh
esp32-config usb configure network 0 192.168.7.2/24
esp32-config usb status
```

在电脑的 USB 网络接口上设置同一子网中的另一个地址，例如 `192.168.7.1/24`。
开发板不会启动 DHCP 服务器。例如，在 Linux 电脑上，将 `USB_IFACE` 替换为实际的新接口名：

```sh
sudo ip address add 192.168.7.1/24 dev USB_IFACE
sudo ip link set USB_IFACE up
ping 192.168.7.2
```

如果其他连接已使用这个子网，请另选一个。
USB 地址与 Wi-Fi 地址独立。应用可以通过此连接使用普通网络套接字。

## 返回主机模式

关闭正在使用 USB 连接的程序，再从独立控制台运行：

```sh
esp32-config usb configure host
```

先断开设备模式线缆，再连接主机模式外设。

## 配置自定义 ACM 功能

需要自己的 USB 标识时，可以使用下面的 configfs 配置示例。
它依据源码编写；USB gadget 模式仍[不属于标准 HIL 测试套件](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/hil/README.md)。
先完成[通用引脚与 overlay 检查](peripheral-setup)，并释放配置工具创建的 gadget：

```sh
esp32-config usb stop
```

这会保留已保存的 USB 选择，下次启动时仍会恢复它。

先检查存储使用情况：

```sh
cat /proc/mounts
cat /proc/swaps
```

卸载 USB 存储上的全部文件系统，并对每个位于 USB 存储上的 swap 条目执行
`swapoff`，路径以实际输出为准。先断开 USB 存储设备，再连接设备模式所用的
线缆，然后应用角色覆盖层：

```sh
s31-overlay apply usb-device --volatile
[ -d /sys/kernel/config/usb_gadget ] || mount -t configfs none /sys/kernel/config
ls /sys/class/udc
```

使用项目自己的 USB 厂商/产品 ID。输入十六进制值时加上 `0x` 前缀，
让 configfs 按十六进制解析。以下命令在同一个 shell 中执行；若命令失败
或 `s31-acm` 已存在，应停止：

```sh
printf 'USB vendor ID (hex): '
read -r S31_USB_VID
printf 'USB product ID (hex): '
read -r S31_USB_PID
S31_GADGET=/sys/kernel/config/usb_gadget/s31-acm
mkdir "$S31_GADGET"
echo "$S31_USB_VID" > "$S31_GADGET/idVendor"
echo "$S31_USB_PID" > "$S31_GADGET/idProduct"
mkdir "$S31_GADGET/strings/0x409"
echo 's31-example-001' > "$S31_GADGET/strings/0x409/serialnumber"
echo 'S31 development' > "$S31_GADGET/strings/0x409/manufacturer"
echo 'S31 CDC ACM example' > "$S31_GADGET/strings/0x409/product"
mkdir "$S31_GADGET/configs/c.1"
mkdir "$S31_GADGET/configs/c.1/strings/0x409"
echo 'CDC ACM' > "$S31_GADGET/configs/c.1/strings/0x409/configuration"
mkdir "$S31_GADGET/functions/acm.usb0"
ln -s "$S31_GADGET/functions/acm.usb0" "$S31_GADGET/configs/c.1/acm.usb0"
S31_UDC=$(ls /sys/class/udc | head -n 1)
: "${S31_UDC:?No UDC found}"
echo "$S31_UDC" > "$S31_GADGET/UDC"
S31_ACM_PORT=$(cat "$S31_GADGET/functions/acm.usb0/port_num")
printf 'Device serial node: /dev/ttyGS%s\n' "$S31_ACM_PORT"
```

主机应枚举出 CDC ACM 串口接口，请查看新出现的串口设备。先在主机上打开该
串口，再从 S31 发送一行文本：

```sh
printf 'hello from S31\n' > "/dev/ttyGS$S31_ACM_PORT"
```

S31 的写入可能等待主机打开接口。不能假定 gadget 使用 `/dev/ttyGS0`：固定的
USB Serial/JTAG 驱动可能已经占用了该名称，gadget 分配器会跳过已占用的编号。
configfs 的 `port_num` 属性给出实际编号。清理前先关闭两端的串口：

```sh
echo '' > "$S31_GADGET/UDC"
rm "$S31_GADGET/configs/c.1/acm.usb0"
rmdir "$S31_GADGET/functions/acm.usb0"
rmdir "$S31_GADGET/configs/c.1/strings/0x409"
rmdir "$S31_GADGET/configs/c.1"
rmdir "$S31_GADGET/strings/0x409"
rmdir "$S31_GADGET"
s31-overlay remove usb-device --volatile
```

清理步骤会释放功能并恢复基础配置的主机角色。重新连接主机外设前，应先断开
设备模式线缆。来源：[内核 configfs 生命周期](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/usb/gadget_configfs.rst)、
[S31 串口编号分配](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/usb/gadget/function/u_serial.c)、
[ACM 端口编号](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/usb/gadget/function/f_acm.c)。
