# 构建配置

所有构建均使用同一套完整开发板配置，包含 Wi-Fi、蓝牙、USB、I2C、SPI、I2S、以太网、SD/MMC 等原生控制器驱动。无需选择构建变体。可选硬件通过运行时[覆盖层](../resources/overlay-catalog.md)启用。

```sh
make build
make image
```

构建输出、暂存文件和报告位于 `out/`，最终镜像位于 `out/images/`。同一个输出目录的写入由构建锁串行化。共享下载及工具链保留在 `cache/`。发布的匹配镜像集位于 `dist/<build-id>/`；验证成功后才会更新 `dist/current`。

完整配置包含 S31 控制器及必要的 Linux 框架，但不会自动包含每一种外接 SPI 屏幕、USB HID 设备或 USB 声卡的驱动。

## 源码配置

| 文件 | 设置 |
|---|---|
| `linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` | 原生开发板默认选项 |
| `configs/kernel/common.config`、`configs/kernel/board.config` | 完整内核配置 |
| `configs/kernel/debug.config` | `DEBUG=1` 时增加的诊断选项 |
| `mk/config.mk` | 构建路径、工具链、内核命令行和配置片段选择 |
| `buildroot-external/configs/esp32s31_rootfs_defconfig` | 根文件系统软件包和系统选项 |
| `buildroot-external/board/esp32-s31/busybox.fragment` | BusyBox 工具，包括网络校时 |
| `configs/esp32-config-timezones.list` | 镜像中保留的时区 |
| `buildroot-external/board/esp32-s31/post-build.sh` | 最终根文件系统的安装与精简策略 |

需要长期保留的更改应写入源码配置。内核配置输入变化时，会重新生成 `out/linux/.config`；输入标识未变化时，保留原生增量构建行为。已有 Buildroot 输出中的软件包或工具链配置输入变化时，构建会要求运行 `make buildroot-reconfigure` 后重建，下载缓存仍保留。

先用 `make fetch` 准备 Buildroot 输出，再打开配置菜单并导出供审查的配置副本：

```sh
make buildroot-menuconfig
make -C buildroot O="$PWD/out/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" \
  savedefconfig DEFCONFIG="$PWD/out/generated/buildroot-menu.defconfig"
```

将需要的软件包和系统选项从该文件合入 `buildroot-external/configs/esp32s31_rootfs_defconfig`。不要把已解析的主机专用 `BR2_TOOLCHAIN_EXTERNAL_PATH` 或暂存目录的 `BR2_ROOTFS_OVERLAY` 路径写回源码；主构建会在配置时注入这些值。审查源码差异后，分别运行 `make buildroot-reconfigure`、`make fetch-rootfs` 和 `make image`。这也会清理手工改过的输出配置；主构建会拒绝直接复用该配置。额外应用仍需在 Buildroot 中单独选择，参见[添加用户空间工具](../api-guides/adding-a-userspace-tool.md)。最终内核选项的核对方法见[内核配置](../resources/kconfig-reference.md)。

## 体积优化

目标代码使用原生构建接口进行体积优化，不修改上游构建算法：

- Linux 使用 `CONFIG_CC_OPTIMIZE_FOR_SIZE=y`，并通过逐目标 CFLAGS 将开发板的速度优化例外及 LZ4 调整为 `-Os`。jitterentropy 熵源保留其强制要求的 `-O0`。
- U-Boot/SPL 使用原生体积优化配置，包括库优化。
- OpenSBI 在原生 Makefile 之后加载补充 Makefile，在保留 ISA/ABI 选项的同时追加 `-Os`。
- Buildroot 使用 `BR2_OPTIMIZE_S=y`；项目应用继承 `TARGET_CFLAGS`。CoreMark 通过原生 `PORT_CFLAGS`/`XCFLAGS` 接口构建，并保留两个 pthread。
- ESP-IDF 无线和 LP 固件使用原生 SIZE 配置；LP 和项目无线 C 源码使用 `-Os`。

主机工具保留各自的优化设置。供应商二进制库、工具链运行库和继承的根文件系统二进制不会因此重新编译。重打包基线 rootfs 时，必须将继承代码的优化状态标记为未验证。汇编指令序列不变；CoreMark 性能需要重新建立基准，代码更小并不保证更快。

完整 XIP 内核使用 6 MiB（6,291,456 字节）分区；ext4 和 JBD2 保持内置。镜像必须通过体积检查；超出预算会直接失败，不会自动禁用驱动或发布超大镜像。影响内核体积的更改需要明确修改源码配置并重新验证。

`make image` 成功后，检查本次发布产物的实际大小，不要依赖其他构建记录中的数值：

```sh
stat -c %s dist/current/xipImage
```

实际大小及清单对应具体的源码和配置；主机体积检查通过不代表硬件启动成功。

## 内核导出符号裁剪

默认启用 `CONFIG_TRIM_UNUSED_KSYMS=y`。内核保留同次构建中的模块所引用的导出符号，并通过 `CONFIG_UNUSED_KSYMS_WHITELIST` 保留外部 XIP 无线载荷所需的导入。构建从载荷生成 `out/generated/radio-kernel-symbols.txt`，其内容随载荷输入重新生成；原生内核配置使用该文件的绝对路径。用以下命令查看自己构建生成的列表行数：

```sh
wc -l out/generated/radio-kernel-symbols.txt
```

不能清空白名单，否则可能裁掉运行时所需的导出。

此设置不承诺未来模块或树外模块的 ABI。新增模块应与内核一起构建，或明确将必要导出加入原生白名单，然后重新检查分区预算及模块加载。

## 镜像中的配置工具

镜像包含 `esp32-config`、GPIO 服务和配置备份。网络校时客户端由 BusyBox 提供。启动时存在已保存的 GPIO 配置才启动 GPIO 服务；自动校时和开机程序初始为关闭。

post-build 根据最终内核配置生成 `/usr/share/esp32-config/kernel-features`，菜单据此提供接口和 USB 功能。存储功能也会检查运行系统中的文件系统驱动。内核与 rootfs 必须来自同一个匹配镜像集。

添加时区时，修改 `configs/esp32-config-timezones.list`；若来源区域尚未包含，还需在 Buildroot defconfig 的 `BR2_TARGET_TZ_ZONELIST` 中加入该区域，然后重新构建 rootfs。

## 无线模式

集成构建始终生成 Wi-Fi/蓝牙组合载荷。板端通过 `esp32-config wifi enable|disable` 和 `esp32-config bluetooth enable|disable` 保存策略并重新加载无线服务；重新加载可能断开活动连接。

| 已启用的服务 | 运行时模式 | 覆盖层 |
|---|---|---|
| 仅 Wi-Fi | `wifi` | `radio-wifi` |
| 仅蓝牙 | `bt` | `radio-bluetooth` |
| 两者均启用 | `combo` | `radio-combo` |
| 两者均未启用 | 停止无线模块 | 移除无线覆盖层配置 |

当前 mac80211 前端只提供一个 STA 接口；完整开发板配置不会增加 AP 支持。参见[无线接口](../api-reference/radio/index.md)和[开发板配置](../resources/esp32-config.md)。
