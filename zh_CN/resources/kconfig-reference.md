# 内核配置

内核选项用于选择 Linux 中包含的驱动和系统功能。
S31 defconfig 位于 `linux-esp32-s31/arch/riscv/configs/` 下。
顶层构建应用 `configs/kernel/common.config` 和 `configs/kernel/board.config`，可用 `DEBUG=1` 追加诊断片段。所有构建使用[完整配置](../get-started/build-configuration.md)。

## S31 选项

下列名称省略了 `.config` 文件中使用的 `CONFIG_` 前缀。

| 选项 | 用途 |
|---|---|
| `ESP32S31_CLIC` | 核心本地中断控制器 |
| `ESP32S31_SYSTIMER_CLOCKSOURCE` | S31 defconfig 使用的 SYSTIMER 驱动，提供 16 MHz 时钟源和 S31 定时事件辅助函数 |
| `ESP32S31_SYSTIMER` | 构建同一个 SYSTIMER 驱动的另一项 Kconfig 入口 |
| `ESP32S31_SYSTEM_TIMERS` | 通过 Counter 框架只读访问 SYSTIMER 和 LP RTC 计数器 |
| `ESP32S31_COPROC_CONTEXT` | 保存和恢复协处理器状态 |
| `ESP32S31_CACHE` | 缓存支持 |
| `ESP32S31_CLOCK` | 时钟和复位提供程序 |
| `ESP32S31_PMU` | 电源域提供程序 |
| `ESP32S31_DT_OVERLAY` | 运行时覆盖层管理器 |
| `ESP32S31_AHB_GDMA`, `ESP32S31_AXI_GDMA` | DMAengine 提供程序 |
| `ESP32S31_GPTIMER`, `ESP32S31_PCNT` | 通用定时器和脉冲计数器 |
| `ESP32S31_ADC`, `ESP32S31_DAC` | 模拟转换 |
| `ESP32S31_COMPARATOR`, `ESP32S31_TOUCH` | 比较器和触摸感应 |
| `ESP32S31_WATCHDOG` | 看门狗支持 |
| `ESP32S31_LP_REMOTEPROC` | LP 核固件和邮箱 |
| `ESP32S31_RADIO_BLOBS` | 外部无线固件支持 |
| `ESP32S31_RADIO_SMODE`, `ESP32S31_RADIO_SMODE_DRIVER` | Linux S-mode 无线运行时 |
| `ESP32S31_WIFI`、`ESP32S31_WIFI_SOFTMAC` | mac80211 单 STA 前端 |
| `ESP32S31_RADIO_XIP` | 专用 Flash 分区中的预链接无线载荷 |
| `CC_OPTIMIZE_FOR_SIZE` | 原生内核体积优化（`-Os`） |
| `TRIM_UNUSED_KSYMS` | 上游未使用导出裁剪机制，保留自动生成的无线导入白名单 |
| `UNUSED_KSYMS_WHITELIST` | 顶层构建传入的 `out/generated/radio-kernel-symbols.txt` 路径 |
| `EXT4_FS`、`JBD2` | 完整配置中的内置 ext4 与日志支持 |
| `BT_ESP32S31` | 蓝牙前端 |
| `CRYPTO_DEV_ESP32S31` | 硬件加密驱动 |

外设子系统也有各自的选项，例如 `I2C_ESP32S31`、`SPI_ESP32S31` 和 `SND_SOC_ESP32S31_I2S`。
其 Kconfig 条目会声明框架依赖。I2C 和 SPI 使用 `depends on` 声明时钟、设备树
支持等要求，必须先启用这些依赖。I2S 选项还会选中通用 DMAengine PCM 辅助
组件。每 CPU 时钟事件由 RISC-V 定时器驱动实现，它会调用 S31 SYSTIMER 事件
辅助函数；`ESP32S31_SYSTEM_TIMERS` 则是独立的 Counter 接口。

顶层构建强制检查体积优化、无线 XIP、带自动生成无线白名单的上游导出裁剪、
内置 ext4 和完整开发板外设配置。关闭这些必需选项会使配置检查失败。
白名单在原生 Linux 构建前根据无线载荷的未定义符号生成，不应改为手工维护列表。

## 检查构建

运行 `make linux` 后，生成的配置位于 `out/linux/.config`。例如：

```sh
grep -E '^(CONFIG_I2C_ESP32S31=|# CONFIG_I2C_ESP32S31 is not set)' out/linux/.config
grep -E '^(CONFIG_ESP32S31_RADIO_SMODE_DRIVER=|# CONFIG_ESP32S31_RADIO_SMODE_DRIVER is not set)' out/linux/.config
```

`y` 将功能编入内核；对于支持模块化的选项，`m` 将其构建为可加载模块。
禁用的选项显示为 `# CONFIG_NAME is not set`。

`.config` 是生成的文件。如需长期保留更改，应更新源码 defconfig，以及影响
该选项的 `configs/kernel/` 片段。下次顶层构建会重新应用这些输入，
并通过 `olddefconfig` 解析依赖。要使用可选外设，还需在开发板上启用对应的
覆盖层；覆盖层无法提供构建时被省略的驱动。
