# 烧录与首次启动

本指南介绍发布镜像的安装和串口控制台的使用。提供的配置面向 16 MiB Flash
和 16 MiB PSRAM；请结合[模组与开发板](../hw-reference/modules-and-boards.md)
核对开发板的内存、接线和下载操作。

## 1. 安装 `esptool`

独立烧录发布镜像时，请使用 Python 3.10 或更新版本，以及不低于 5.3.0 的
`esptool` 5.x 版本。5.3.0 增加了 S31 stub 烧录器，并修复了 S31 Flash 命令；
参见 [esptool 发布说明](https://github.com/espressif/esptool/releases/tag/v5.3.0)。
下面使用独立虚拟环境，与[源码构建](build-from-source.md)所用的 ESP-IDF
环境分开安装。

### 在 Linux 上安装

在 Ubuntu 上，如果尚未安装 `python3` 和 `python3-venv`，请先安装它们。
然后执行：

```sh
python3 -m venv "$HOME/s31-flash-env"
. "$HOME/s31-flash-env/bin/activate"
python -m pip install --upgrade "esptool>=5.3,<6"
python -m esptool version
```

打开新终端后，请重新激活此环境。

### 在 Windows 上安装（PowerShell）

安装带有 Python 启动器的 Python 3.10 或更新版本，然后执行：

```powershell
py -3 -m venv "$env:USERPROFILE\s31-flash-env"
$S31_PYTHON = "$env:USERPROFILE\s31-flash-env\Scripts\python.exe"
& $S31_PYTHON -m pip install --upgrade "esptool>=5.3,<6"
& $S31_PYTHON -m esptool version
```

请在同一个 PowerShell 会话中执行后续命令。在新会话中，需要再次将
`S31_PYTHON` 设为相同路径。其他安装方式见 Espressif 的
[安装指南](https://docs.espressif.com/projects/esptool/en/latest/esp32/installation.html)。

## 2. 连接开发板

连接开发板的下载/控制台端口，并确定其串口设备。以下示例在 Linux 上使用
`/dev/ttyUSB0`，在 Windows 上使用 `COM3`；请替换为实际端口。
USB 桥接芯片和开发板接线决定了设备名称，以及是否支持自动进入下载模式和
复位。烧录前请关闭其他占用串口的程序。

## 3. 安装发布镜像

从项目的[发布页面](https://github.com/GrieferPig/esp32-s31-linux/releases)
下载 `s31_full_flash.bin`，并通过发布说明确认其源码版本。发布文件还包括
独立组件镜像、`build-manifest.json` 和 `SHA256SUMS`。
在下载目录中执行以下命令。

> **警告：** 下列命令会擦除整个 Flash 芯片，包括已保存的设置。即使省略显式
> 擦除步骤，烧录合并镜像仍会覆盖 persist 区域。若要更新并保留该区域，请使用
> 下文的独立组件烧录方法。

### 在 Linux 上烧录

```sh
PORT=/dev/ttyUSB0
python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
python -m esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  0x0 s31_full_flash.bin
```

### 在 Windows 上烧录（PowerShell）

```powershell
$PORT="COM3"
& $S31_PYTHON -m esptool --chip esp32s31 -p "$PORT" -b 2000000 erase-flash
& $S31_PYTHON -m esptool --chip esp32s31 -p "$PORT" -b 2000000 write-flash `
  --flash-mode dio --flash-freq 80m --flash-size 16MB `
  0x0 s31_full_flash.bin
```

如果不支持自动下载或复位，请按开发板说明操作按钮，进入下载模式，并在烧录
完成后复位。如果传输失败，可尝试降低烧录波特率，例如改为 `921600`。

## 4. 打开控制台并登录

使用终端程序打开串口，参数如下：

| 设置 | 值 |
|---|---|
| 波特率 | 115200 |
| 数据位 | 8 |
| 校验位 | 无 |
| 停止位 | 1 |
| 流控制 | 无 |

可使用以下源码定义的启动消息识别启动阶段；可选的横幅输出可能不同。

| 标志 | 含义 |
|---|---|
| `ESP32-S31 SPL active` | SPL 已进入开发板初始化阶段 |
| `OpenSBI` 横幅 | M 模式固件已执行到横幅输出位置，前提是启用了该输出 |
| `Starting kernel ...` | U-Boot 正在将控制权交给 Linux |
| `Linux version` | 内核已开始输出版本横幅 |
| `S31 SMP: cpu1 online` | Linux 已确认第二个 HP CPU 上线 |
| `esp32-s31 login:` | 默认主机名对应的串口登录已可用 |

默认源码配置使用 **`root` 用户，初始密码为空**。定制源码配置或已有的
persist 分区可能会改变这些凭据。

登录后，检查运行中的内核、CPU、根挂载及启动状态：

```sh
uname -r
cat /sys/devices/system/cpu/online
grep ' / ' /proc/mounts
test -e /run/rcS.done && echo "rcS finished" || echo "rcS still running"
cat /run/rcS.log
```

配置中的内核基于 Linux 6.18，版本后缀可能不同。正常的双 CPU 结果为 `0-1`；
可写根文件系统建立成功时，`/` 处应显示 `overlay` 挂载。启动早期出现
`S31 overlay:` 错误时，系统可能仍可登录恢复环境，但根文件系统会是只读
SquashFS。

开发板服务在后台启动时，登录提示符可能已经出现。`/run/rcS.done` 只表示启动
序列已经结束，不代表每项服务都成功。请在 `/run/rcS.log` 中检查服务错误，
并用 `dmesg` 查看内核消息。

## 5. 配置开发板

运行配置菜单：

```sh
esp32-config
```

在 **Network** 中连接 Wi-Fi，在 **Bluetooth** 中设置蓝牙，
在 **Interfaces** 中配置 GPIO 和外设。**System** 包含主机名、登录密码、时间和开机程序。
可写根文件系统挂载成功时，配置会保存在 `/etc/esp32-conf`。各项设置和状态命令见
[开发板配置](../resources/esp32-config.md)。

外设设置见[叠加层目录](../resources/overlay-catalog.md)。启动问题的排查方法见
[调试](../api-guides/debugging.md)。

## 6. 更新源码构建的系统

[构建项目](build-from-source.md)后，请保持其 ESP-IDF 环境和所选
`S31_LEAN_RADIO` 配置有效。在主仓库根目录执行：

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

该目标会重新构建其依赖，并写入 SPL、U-Boot/OpenSBI、Linux 设备树、无线
文件系统、内核和根文件系统，同时保留 persist 分区。保留该分区可以保留已
保存的设置，但下次启动仍会执行迁移和软件包文件清理；具体见
[配置文件](../resources/configuration.md)和
[部署重启后需要保留的文件](deploy-files-that-must-survive-reboot)。

要直接写入已构建的组件文件而不重新构建，请在主仓库根目录使用 ESP-IDF
环境中的 `esptool`：

```sh
PORT=/dev/ttyUSB0
. configs/esp32s31-layout.cfg
esptool --chip "$CHIP" -p "$PORT" -b 2000000 write-flash \
  --flash-mode dio --flash-freq 80m --flash-size 16MB \
  "$SLOT_SPL" "build/$SPL_APP_BIN" \
  "$SLOT_UBOOT_ITB" "build/$UBOOT_ITB" \
  "$SLOT_DTB" "build/$BASE_DTB" \
  "$SLOT_RADIO" "build/$RADIO_IMAGE" \
  "$SLOT_KERNEL" "build/$KERNEL_IMAGE" \
  "$SLOT_ROOTFS" "build/$ROOTFS_IMAGE"
```

请使用一整套成功构建且相互匹配的组件。各组件烧录目标及其重新构建行为见
[Make 命令参考](../resources/make-reference.md)。
