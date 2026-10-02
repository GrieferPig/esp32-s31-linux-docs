# 构建配置

根据应用所需的外设选择构建配置。本地构建默认为精简无线配置。
GitHub 发布工作流通过 `S31_LEAN_RADIO=0` 明确选择完整外设配置。

S31 的所有目标组件统一使用 `-Os`，包括 Linux、OpenSBI、U-Boot、radio/LP 固件、BTstack、CoreMark 和 rootfs 应用。默认内核配置启用 Wi-Fi 与蓝牙前端。

内核 jitterentropy 熵源依赖时序采样，保留其源码强制要求的 `-O0`；该源文件会拒绝优化构建。

完整外设配置包含 S31 控制器驱动及其必要的 Linux 框架；不会自动包含 SPI 屏幕、USB HID 设备、USB 声卡等外接器件驱动。

| 配置 | 选择方式 | 包含的功能 |
|---|---|---|
| 精简无线 | `S31_LEAN_RADIO=1`（本地默认值） | Wi-Fi、蓝牙、控制台、Flash、持久化设置，以及用于交换空间的 USB 大容量存储 |
| 完整外设 | `S31_LEAN_RADIO=0`（发布工作流） | 上述功能，以及 I2C、SPI、I2S、以太网和 SD/MMC 等可选驱动 |

精简配置禁用了 FAT、VFAT 和 EXT4。该配置支持 USB 块设备，并不意味着可以
挂载使用这些文件系统的存储设备。如需这些文件系统或进行外设开发，请选择
完整外设配置。

## 选择配置

导出配置选项，使后续组件构建和烧录目标使用相同的配置：

```sh
export S31_LEAN_RADIO=0
make all
```

要在同一终端中恢复精简无线配置：

```sh
export S31_LEAN_RADIO=1
make all
```

`make all` 只在主机上构建镜像。写入开发板的步骤见
[烧录与首次启动](flash-and-first-boot.md)。
`S31_LEAN_RADIO=0 make all` 这样的单次赋值不会影响后续单独执行的
`make flash-all`，而该目标会重新构建其依赖。

切换构建配置或修改内核选项后，也需要更新开发板上的内核。保持所选配置已导出，
并按烧录指南运行 `make flash-all PORT=/dev/ttyUSB0`。
`flash-existing-rootfs` 只写入根文件系统；开发板已运行所选内核配置时，
可用它更新应用程序。

两种配置使用相同的 Flash 布局。可选硬件通过
[设备树叠加层](../resources/overlay-catalog.md)在运行时选择，但其驱动也必须
在所选内核配置中启用。

## 镜像中的配置工具

两种构建配置都包含 `esp32-config`、GPIO 服务和配置备份功能。
网络校时客户端由 BusyBox 提供。启动时存在已保存的 GPIO 配置才启动 GPIO 服务；
自动校时和开机程序初始为关闭。

post-build 步骤根据完成构建的内核配置生成
`/usr/share/esp32-config/kernel-features`，菜单据此提供受支持的接口和 USB 功能。
存储功能还会检查运行系统中可用的文件系统驱动。
内核与根文件系统应采用相同的构建配置。

镜像保留 `configs/esp32-config-timezones.list` 中列出的 IANA 时区。
添加时区时修改该列表；如果该时区属于尚未包含的来源区域，
还需在 Buildroot defconfig 的 `BR2_TARGET_TZ_ZONELIST` 中加入该区域。
重新构建根文件系统后，时区菜单会包含新的选项。

## 添加应用程序

两种配置都使用精简的 Buildroot 根文件系统。额外的软件包需要单独添加。
参见[添加用户空间工具](../api-guides/adding-a-userspace-tool.md)。

## 修改构建选项

需要长期保留的配置来自以下文件：

| 文件 | 设置 |
|---|---|
| `linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` | 内核功能和驱动的初始选择 |
| 主仓库 `Makefile` | 内核强制选项、构建配置覆盖项和内核命令行 |
| `buildroot-external/configs/esp32s31_rootfs_defconfig` | 根文件系统软件包和系统选项 |
| `buildroot-external/board/esp32-s31/busybox.fragment` | BusyBox 工具，包括网络校时 |
| `configs/esp32-config-timezones.list` | 镜像中保留的时区 |
| `buildroot-external/board/esp32-s31/post-build.sh` | 最终根文件系统中保留或删除的文件 |

主构建流程从源码中的 defconfig 开始。对于 Linux，随后还会应用主 Makefile
自身的选项和所选构建配置，再通过 `olddefconfig` 解析依赖。如果主 Makefile
明确修改了某个选项，仅编辑源码 defconfig 无法覆盖它。只修改
`build/linux-6.18/.config` 或 `build/buildroot/.config` 的内容，会在下次主构建时
被替换。

修改 Buildroot 软件包时，先打开菜单，再将选择保存到源码 defconfig。
必须在再次执行 `make rootfs` 或 `make buildroot-menuconfig` 重置输出配置
**之前**保存。在主仓库根目录执行：

```sh
make buildroot-menuconfig
make -C buildroot O="$PWD/build/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" \
  savedefconfig DEFCONFIG="$PWD/buildroot-external/configs/esp32s31_rootfs_defconfig"
git diff -- buildroot-external/configs/esp32s31_rootfs_defconfig
```

重新构建前请检查差异。如何核对最终内核选项，参见
[内核配置](../resources/kconfig-reference.md)。

## 无线模式

两种构建配置都包含 Wi-Fi/蓝牙组合载荷。运行时策略根据已保存的 Wi-Fi 和
蓝牙 `enabled` 设置选择模式：

| 已启用的服务 | 运行时模式 | 叠加层 |
|---|---|---|
| 仅 Wi-Fi | `wifi` | `radio-wifi` |
| 仅蓝牙 | `bt` | `radio-bluetooth` |
| 两者均启用 | `combo` | `radio-combo` |
| 两者均未启用 | 停止无线模块 | 移除无线叠加层配置 |

使用 `esp32-config` 修改并应用保存的选择。这些运行时选择独立于
`S31_LEAN_RADIO`；参见[开发板配置](../resources/esp32-config.md)。
