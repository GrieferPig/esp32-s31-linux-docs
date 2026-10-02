# 启动过程

开发板依次通过 ROM、SPL、OpenSBI 和 U-Boot 启动 Linux。本页说明各阶段的
作用，以及启动在早期停止时应检查哪些文件。

## 1. ROM 与 SPL

项目提供的镜像按 ROM 的常规 Flash 启动路径准备。父项目构建通过 `esptool --chip esp32s31 elf2image` 将 SPL 打包为 `build/spl_app.bin`，烧录规则通过下载连接写入它。参见[镜像打包](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L193-L199)及[烧录规则](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L494-L499)。

SPL 初始化启动所需的内存和时钟，并加载 U-Boot FIT 镜像 `build/u-boot.itb`。其[板级初始化](https://github.com/GrieferPig/u-boot-esp32-s31/blob/06fe89c93ed52349f60120c77efe3018c1e6b29f/board/espressif/esp32s31/spl.c#L59-L90)选择 NOR 作为启动设备。

## 2. OpenSBI 和 U-Boot

SPL 在机器模式下进入 OpenSBI，并传入 U-Boot 主程序的地址。OpenSBI 初始化
平台服务，并在监管者模式下启动 U-Boot。启动完成后，OpenSBI 仍负责处理
Linux 的 SBI 调用。

U-Boot 使用 Linux 设备树启动内核。默认启动命令使用以下映射地址：

```text
booti 0x40400000 - 0x40200000
```

第一个地址是内核地址，第二个地址是设备树地址。SPL 将 flash 原始偏移
`0x100000` 映射到 CPU 地址 `0x40000000`，因此这两个地址分别对应原始偏移
`0x500000` 和 `0x300000`。地址换算和分区表见
[Flash 布局](../../hw-reference/flash-layout.md)。

## 3. Linux 和根文件系统

Linux 初始化内存、中断、定时器和设备驱动，然后启动根文件系统中的 `/init`。

早期初始化脚本组建可写根文件系统，恢复保存的设备树覆盖层，加载所选无线模式，
然后启动 BusyBox init。文件系统布局和保存的设置见
[配置](../../resources/configuration.md)。

如果持久化文件系统挂载失败，脚本会打印错误，并从只读基础系统启动 BusyBox init。
这会跳过早期覆盖层恢复和无线模块加载，因此相应设备可能不可用。检查步骤见
[调试](../../api-guides/debugging.md)。

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
| `radio.sqfs` | 无线模块和外部固件 |

烧录命令见[烧录和首次启动](../../get-started/flash-and-first-boot.md)。
