# 启动过程

开发板依次通过 ROM、SPL、OpenSBI 和 U-Boot 启动 Linux。本页说明各阶段的
作用，以及启动在早期停止时应检查哪些文件。

## 1. ROM 与 SPL

项目构建将 SPL 打包为 `out/images/spl_app.bin`，其原始 Flash 偏移为 `0x002000`，容量限制为 48 KiB；之前的 8 KiB 为 FlashEncryption 强制保留区。SPL 初始化内存和时钟，将完整 Flash 从原始偏移零映射到物理 `0x40000000`，再加载位于 `0x00E000` 的 U-Boot FIT。

构建入口见 `mk/boot.mk`，运行时板级初始化见 `u-boot-esp32-s31/board/espressif/esp32s31/spl.c`。

## 2. OpenSBI 和 U-Boot

SPL 在机器模式下进入 OpenSBI，并传入 U-Boot 主程序的地址。OpenSBI 初始化
平台服务，并在监管者模式下启动 U-Boot。启动完成后，OpenSBI 仍负责处理
Linux 的 SBI 调用。

U-Boot 使用 Linux 设备树启动内核。默认启动命令使用以下映射地址：

```text
booti 0x40400000 - 0x4005e000
```

第一个地址是内核，第二个是设备树，对应原始 Flash 偏移 `0x400000` 和 `0x05E000`。修改 XIP 布局时，必须保留内核起点的 4 MiB Sv32 大页对齐。OpenSBI 位于 FIT 固定外部数据偏移 `0x400`，从 `0x4000E400` XIP 执行；可写数据位于内部 SRAM。地址与分区约定见[Flash 布局](../../hw-reference/flash-layout.md)。

## 3. Linux 和根文件系统

Linux 初始化内存、中断、定时器和设备驱动，然后启动根文件系统中的 `/init`。

早期初始化脚本组建可写根文件系统，恢复保存的设备树覆盖层，加载所选无线模式，
然后启动 BusyBox init。文件系统布局和保存的设置见
[配置](../../resources/configuration.md)。

如果持久化文件系统挂载失败，脚本会打印错误，并从只读基础系统启动 BusyBox init。
恢复路径为 `/run`、`/tmp` 和 `/var/log` 挂载易失存储，持久化设置不可用，
并跳过早期覆盖层恢复和无线模块加载。当前镜像的启动与持久化路径仍需板端验收，
恢复登录不能证明持久化或正常启动已通过。检查步骤见[调试](../../api-guides/debugging.md)。

## 4. 服务和串口登录

BusyBox 启动开发板服务和串口登录。服务通过 `rcS` 运行，输出保存到
`/run/rcS.log`。服务仍在启动时，登录提示符就可能已经出现。

```sh
cat /run/rcS.log
test -e /run/rcS.done && cat /run/rcS.status
```

## 启动文件

| 文件 | 启动阶段 |
|---|---|
| `spl_app.bin` | 可由 ROM 加载的 SPL |
| `u-boot.itb` | OpenSBI 和 U-Boot |
| `esp32s31_generic.dtb` | Linux 硬件描述 |
| `xipImage` | Linux 内核 |
| `rootfs.sqfs` | 早期初始化、BusyBox 和应用 |
| `radio.bin` | 预链接无线 XIP 载荷；匹配模块位于 rootfs |

烧录命令见[烧录和首次启动](../../get-started/flash-and-first-boot.md)。
