# Flash 布局

随项目提供的镜像使用 16 MiB NOR flash。下表中的地址均为烧录时使用的 flash 原始偏移。

| 偏移 | 容量 | 内容 |
|---:|---:|---|
| `0x000000` | 8 KiB | SPL 前的保留区域 |
| `0x002000` | 1016 KiB | `spl_app.bin` |
| `0x100000` | 2 MiB | `u-boot.itb` |
| `0x300000` | 64 KiB | `esp32s31_generic.dtb` |
| `0x310000` | 1984 KiB | `radio.sqfs` |
| `0x500000` | 6336 KiB | `xipImage` |
| `0xB30000` | 576 KiB | 持久化 JFFS2 文件系统 |
| `0xBC0000` | 64 KiB | HIL 测试临时分区 |
| `0xBD0000` | 4288 KiB | `rootfs.sqfs` |

HIL 测试临时分区与持久化存储相互独立。保存文件和可写根文件系统的说明见
[配置](../resources/configuration.md)。

## 原始偏移与映射地址

SPL 将 flash 原始偏移 `0x100000` 映射到 CPU 地址 `0x40000000`。
对于这个窗口内的分区：

- CPU 地址 = `0x40000000` + flash 原始偏移 − `0x100000`。
- Linux 的 flash 节点起始地址为 `0x40000000`，因此节点内的分区偏移以
  flash 原始偏移 `0x100000` 为基准。

| 内容 | Flash 原始偏移 | CPU 地址 | Linux 分区偏移 |
|---|---:|---:|---:|
| 设备树 | `0x300000` | `0x40200000` | `0x200000` |
| 内核 | `0x500000` | `0x40400000` | `0x400000` |
| 持久化存储 | `0xB30000` | `0x40A30000` | `0xA30000` |

U-Boot 的 `booti` 命令使用 CPU 地址，烧录命令使用原始偏移。参见
[启动过程](../api-reference/system/boot-chain.md)。

## 修改布局

偏移和文件名定义在
[`configs/esp32s31-layout.cfg`](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/configs/esp32s31-layout.cfg#L14-L39)。
镜像合并脚本会检查各镜像是否超出对应区域。布局检查工具还会核对配置、Linux
分区和共享内存定义：

```sh
make check-layout
```

移动分区时，还要更新使用该分区的定义，包括设备树、启动地址和内核 XIP 设置。
[布局检查工具](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/check_s31_layout.py#L27-L64)
列出了需要保持一致的定义。
