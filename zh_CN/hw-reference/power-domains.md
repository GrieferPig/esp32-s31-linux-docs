# 电源域

Linux PMU 提供者公开七个通用电源域。Linux 显式控制 HP 连接域（`HPCNNT`）的状态切换；其他域用于描述拓扑和设备归属，并按提供者策略保持开启。无线活动状态所需的 PMU 初始化仍由已链接的载荷执行。

## 已注册的拓扑与策略

| 域名称 | 绑定标识符 | 已注册的父域 | Linux 策略 |
|---|---|---|---|
| `top` | `ESP32S31_PD_TOP` | 无 | 始终开启 |
| `hp-alive` | `ESP32S31_PD_HPALIVE` | `top` | 始终开启 |
| `modem-power` | `ESP32S31_PD_MODEMPWR` | `top` | 始终开启 |
| `hp-cpu` | `ESP32S31_PD_HPCPU` | `top` | 始终开启 |
| `hp-connectivity` | `ESP32S31_PD_HPCNNT` | `top` | 仅在存在 `espressif,allow-hpcnnt-power-off` 时自动管理 |
| `modem` | `ESP32S31_PD_MODEM` | `modem-power` | 始终开启 |
| `lp-peripheral` | `ESP32S31_PD_LP_PERI` | 未注册父域 | 始终开启 |

项目提供的设备树包含 HPCNNT 自动管理的启用属性。载荷会在普通设备归属机制之外访问该域，因此无线模块活动时会额外持有一项投票。无线投票有效时禁止关闭 HPCNNT。载荷完成 PMU 初始化后，reclaim 钩子会重新应用 Linux 的 HPCNNT 强制状态。参见[域策略与拓扑](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/pmdomain/esp32s31-pmu.c)、[DTS 启用属性](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)及[投票与 reclaim 实现](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/pmdomain/esp32s31-pmu.c)。

## 读取电源域诊断信息

```sh
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

| 字段 | 含义 |
|---|---|
| 开头的名称 | 上表中的域名称 |
| `policy=` | 根据 genpd 策略标志显示 `always-on` 或 `automatic` |
| `software=` | 提供者跟踪的 `on` / `off` 状态 |
| `hardware=` | 强制控制寄存器的解释：FORCE_PD 置位时为 `off`，否则 FORCE_PU 置位时为 `on`，否则为 `firmware-auto` |
| `force=` | 低六位强制控制位：复位、隔离、上电、不复位、不隔离、下电 |
| `on=`、`off=` | 成功的 genpd 开启 / 关闭回调计数；`on` 还包含探测时首次取得 HPCNNT 控制权 |
| `reclaim=` | 载荷初始化 PMU 后尝试重新应用状态的次数 |
| `errors=` | 状态切换期间强制控制寄存器回读失败的次数 |
| `radio-vote=` | `hp-connectivity` 的当前无线否决投票；其他电源域也显示该字段，但值为零 |

尽管字段名为 `hardware=`，它解释的是强制控制寄存器，并非独立的电源就绪信号、电流读数或保持状态的证明。输出格式定义于 [`domains_show()`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/pmdomain/esp32s31-pmu.c)。

## 系统保持配置

OpenSBI 的 APPWR 配置写入电源值 `0x0000aa00` 和时钟值 `0x00000000`。源码将它们定义为：四个 HP 内存块进入保持模式、HP 逻辑组进入下电模式，并关闭 HP 各类时钟。LP 固件提供唤醒请求。参见[配置常量](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)和[进入流程](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)。

当前挂起状态、CPU 空闲、关机与定时深度睡眠见[电源管理](../api-guides/power-management.md)。

## 功耗测量

仍需补充可重复的板级电流参考数据。每次测量应同时记录板卡版本、供电点与电压、USB 连接、启用的外设、无线状态、CPU 频率及仪器和采样间隔。板卡输入电流包含稳压器、USB 桥接器和 LED 的消耗，不应将其标为 CPU 电源域电流。
