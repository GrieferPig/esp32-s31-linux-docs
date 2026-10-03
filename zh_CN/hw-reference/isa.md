# 指令集与 ABI

本移植面向带 Sv32 虚拟内存的 32 位 RISC-V。构建时应以以下各组件的编译器配置为准。设备树声明 Linux 使用的扩展；简写的硬件功能标签不能代替受支持的 `-march` 值。

## 各组件的编译器配置

| 组件 | 指令集选择 | ABI / 环境 |
|---|---|---|
| OpenSBI | `rv32imabc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32`，固件 |
| Linux 内核 | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32f`，已修改的内核构建 |
| 应用与库 | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32`，项目 Linux/musl 工具链 |
| 无线载荷 | `rv32imafc_zicsr_zifencei_zaamo_zalrsc_xesploop_xespv2p2` | `ilp32f`，ESP ELF/picolibc 构建 |

这些配置来自[原生构建配置](https://github.com/GrieferPig/esp32-s31-linux/blob/main/mk/config.mk)、[musl 工具链配置](https://github.com/GrieferPig/esp32-s31-linux/blob/main/configs/riscv32-esp-linux-musl.config)、[应用编译标志](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/configs/esp32s31_rootfs_defconfig)、[内核 ABI 修改](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/Makefile)和[无线构建](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/radio/Makefile)。

`-march` 选择指令，`-mabi` 选择参数与返回值的调用约定。`ilp32` 应用可以在内部使用 F 指令，同时按软浮点调用约定传递浮点参数。内核的 `ilp32f` 标志不会改变 musl 应用 ABI。Linux 应用及其依赖库应统一采用 `ilp32`；无线载荷使用的独立运行时库不能替代 musl。

## 浮点与额外状态

本移植的 FPU 上下文路径通过 `fsw` / `flw` 保存和恢复**单精度 F** 寄存器；普通构建不以 D 扩展为目标。Linux 还通过平台 SBI 协处理器服务处理 Espressif 扩展状态。参见 [F 上下文实现](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/kernel/fpu.S)及 [Linux 额外状态调用](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/kernel/esp32s31-ext.c)。内核和固件代码仍需遵守其上下文与浮点使用规则；编译器 ABI 标志本身不能保证任意 FPU 操作安全。

## XespV 与 Xesploop

本移植将 **HP 核 1 视为唯一允许执行 XespV 的核**：OpenSBI 跳过 hart 0 上的 PIE 状态访问，`libesp-simd` 则在进入汇编例程前将调用线程绑定到 CPU1。参见 [OpenSBI 限制](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31_coproc.S)。

通过 `esp_simd.h` 使用 `libesp-simd`，并以 `-lesp-simd` 链接。其构造函数初始化初始线程；每个新的调用线程在首次使用时初始化。`esp_simd_init()` 返回零或负 errno；亲和性设置失败时，公开操作的包装函数使用标量回退实现。亲和性影响整个调用线程。初始化成功后，不要将该线程移到 CPU0 或扩大亲和性掩码：成功状态会被缓存，之后的亲和性变化不会重新检查。[应用指南](../api-reference/userspace/index.md)包含完整的构建、链接和运行示例；具体行为由[库实现](https://github.com/GrieferPig/esp32-s31-linux/blob/main/rootfs/esp_simd.c)定义。

普通应用编译标志不包含 XespV 和 Xesploop。SIMD 软件包显式编译手写的扩展汇编；项目不依赖自动 XespV 向量化。

Linux 和 OpenSBI 实现了 HWLoop/PIE 上下文处理，但源码支持不代表当前镜像已验证任意启用扩展的应用。应将扩展使用限制在已审查的库 / 固件路径内；普通应用的编译标志没有全局启用 Xesploop。参见[应用编译标志](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/configs/esp32s31_rootfs_defconfig)、[Linux 上下文处理](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/kernel/esp32s31-ext.c)和 [SIMD 软件包标志](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/esp-simd/esp-simd.mk)。
