# Flash 布局

项目镜像使用 16 MiB NOR Flash。下表是烧录使用的原始偏移，容量均为二进制单位。除 ROM 的 8 KiB FlashEncryption 元数据保留区外，其余空间连续分配，不留空隙。

| 原始偏移 | 大小 | 内容 |
|---|---:|---|
| `0x000000` | 8 KiB | ROM 元数据保留区 |
| `0x002000` | 48 KiB | `spl_app.bin` |
| `0x00E000` | 320 KiB | `u-boot.itb`，包含 OpenSBI/U-Boot |
| `0x05E000` | 64 KiB | `esp32s31_generic.dtb` |
| `0x06E000` | 1536 KiB | `radio.bin`，预链接无线 XIP 载荷 |
| `0x1EE000` | 2120 KiB | persist，JFFS2 可写存储 |
| `0x400000` | 6144 KiB | `xipImage` |
| `0xA00000` | 6144 KiB | `rootfs.sqfs` |

布局来源为主仓库的 `configs/esp32s31-layout.cfg`，镜像打包、大小检查与烧录共用该文件。所有分区以 8 KiB NOR 擦除粒度对齐，Linux 起点还满足 Sv32 的 4 MiB 大页对齐要求。

## Flash 地址换算

SPL 将原始 Flash `[0, 16 MiB)` 线性映射到物理地址 `0x40000000`：

- CPU 物理地址 = `0x40000000` + Flash 原始偏移
- Linux Flash 节点内的分区偏移与原始偏移一致

| 内容 | 原始偏移 | CPU 物理地址 |
|---|---|---|
| FIT | `0x00E000` | `0x4000E000` |
| 设备树 | `0x05E000` | `0x4005E000` |
| 无线 | `0x06E000` | `0x4006E000` |
| persist | `0x1EE000` | `0x401EE000` |
| 内核 | `0x400000` | `0x40400000` |
| rootfs | `0xA00000` | `0x40A00000` |

FIT 的 OpenSBI 数据固定在 FIT 偏移 `0x400`，因此 OpenSBI 从 `0x4000E400` 执行。无线镜像另有 Linux 虚拟映射，见[内存映射](memory-map.md)。

## 更新与持久化数据

`make flash-existing-all` 使用 `dist/current` 中已验证的匹配组件集，写入 SPL、FIT、DTB、无线、内核和 rootfs，保留 persist。`make flash-all` 是其别名，同样不会构建。更改源码后先运行 `make image`，或使用显式的 `make build-flash`。

合并安装镜像 `s31_full_flash.bin` 包含分区间的填充，烧录它会覆盖 persist。整片擦除也会清除设置。更换布局时，不能假设旧位置的数据会自动迁移；先在实际运行的旧系统中备份，再按目标发布说明迁移。

当前布局没有专用 HIL 临时分区。Flash 破坏性测试不得借用 persist、内核或其他有效分区；测试必须检查安全范围并在没有可用测试区域时拒绝运行。

## 修改布局

修改 `configs/esp32s31-layout.cfg` 时，必须同步更新 U-Boot 映射与启动地址、Linux 设备树、XIP 内核地址、无线预链接约定及有关测试。运行 `make check-layout`，并重新验证所有镜像体积和完整匹配集。不得绕过容量检查或让分区重叠。

烧录与控制台步骤见[烧录与首次启动](../get-started/flash-and-first-boot.md)。
