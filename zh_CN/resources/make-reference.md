# Make 参考

在 `esp32-s31-linux` 仓库根目录运行这些目标。
首次构建请参照[从源码构建](../get-started/build-from-source.md)。

## 常用命令

```sh
make all             # Build the complete image
make linux           # Rebuild Linux and device trees
make rootfs          # Rebuild the root filesystem
make flash-all       # Build and flash the component images
```

设置 `JOBS` 可指定并行构建任务数，例如 `make JOBS=4 all`。
使用 `S31_LEAN_RADIO=0` 构建完整外设版本。

## 构建目标

| 目标 | 说明 |
|---|---|
| `all` | 构建工具链依赖、启动固件、Linux、rootfs 和合并镜像 |
| `download` | 初始化源码子模块 |
| `toolchain` | 下载 Linux 工具链，或复用已安装的副本 |
| `toolchain-source` | 使用配置的 crosstool-NG 源码构建工具链 |
| `opensbi` | 为 U-Boot FIT 构建 `fw_dynamic.bin` |
| `uboot`, `bootloader` | 构建 SPL、`spl_app.bin` 和 `u-boot.itb` |
| `linux` | 构建 XIP 内核、设备树、覆盖层和无线模块 |
| `rootfs`, `initramfs` | 构建 `rootfs.sqfs`；两个名称均选择 SquashFS 目标 |
| `radio-idf-deps` | 构建 ESP-IDF 无线依赖 |
| `radio-linux-payload` | 构建外部无线固件并生成导入桩 |
| `radio-module` | 构建并检查集成无线模块和固件输出 |
| `radio-fs` | 创建 `build/radio.sqfs` |
| `radio-package` | 在 `build/radio-package/` 下创建工程用无线归档包 |
| `lp-firmware` | 构建并暂存 LP remoteproc 固件 |
| `persist` | 创建空的 `build/persist.jffs2` |
| `flash-image` | 创建合并后的 `build/s31_full_flash.bin` 文件 |
| `coremark` | 构建基准测试，并复制到 `build/coremark/coremark.exe` |
| `buildroot-menuconfig` | 打开 Buildroot 配置 |
| `buildroot-clean` | 清理 Buildroot 构建 |
| `clean` | 删除 `build/`、无线构建产物及无线 ESP-IDF 依赖的构建目录 |
| `fullclean` | 执行 `clean`，并删除已安装的项目工具链 |
| `check-layout` | 检查共享的 Flash 和内存布局 |
| `check-host` | 检查布局并运行主机回归测试；依赖步骤会获取 BTstack 源码 |
| `check-docs` | 以严格 Sphinx 警告设置构建文档 |
| `check-dt` | 使用项目交叉编译器检查设备树和绑定 |
| `check-fast` | 运行 `check-host`、`check-docs` 和 `check-dt` |
| `build-manifest` | 写入 `build/build-manifest.json` |

`clean` 不会调用 LP 固件的清理目标，也不会删除暂存到源码根文件系统覆盖目录
中的 LP 文件。这些产物位于 `firmware/lp/build/` 和
`buildroot-external/board/esp32-s31/overlay/lib/firmware/esp32s31/`。

顶层构建会重新应用内核和 rootfs 的 defconfig，再强制应用其 Linux 选项及
构建配置覆盖项。需要长期保留的更改应保存到相关源码配置及主 Makefile 中；
见[构建配置](../get-started/build-profiles.md)。验证所需的依赖和 CI 命令见
[开发环境](../contribute/development-setup.md)。

## 烧录目标

这些目标默认使用 `/dev/ttyUSB0`，波特率为 2000000。请根据连接情况覆盖
`PORT` 和 `BAUD`，同时保持相同的构建配置：

```sh
make PORT=/dev/ttyUSB1 BAUD=921600 flash-all
```

`esptool` 安装、连接准备和打开控制台的步骤见
[烧录与首次启动](../get-started/flash-and-first-boot.md)。

| 目标 | 写入内容 |
|---|---|
| `flash-all` | SPL、FIT、DTB、无线、内核和 rootfs；保留 persist |
| `flash-bootloader` | SPL 和 FIT |
| `flash-opensbi` | 包含 OpenSBI 和 U-Boot 的 FIT |
| `flash-linux` | Linux DTB 和内核 |
| `flash-dtb` | Linux DTB |
| `flash-radio` | 无线文件系统 |
| `flash-rootfs` | 根文件系统 |
| `flash-existing-radio` | 已有的 `build/radio.sqfs`，不重新构建 |
| `flash-existing-rootfs` | 已有的 `build/rootfs.sqfs`，不重新构建 |
| `flash-persist` | 空的持久化文件系统；擦除已保存的文件和设置 |
| `erase` | 整个 flash 芯片 |

常规烧录目标会先构建依赖。`existing` 变体使用磁盘上已有的文件，因此应在构建完成后使用。
`flash-image` 属于上方构建表中的目标：它在主机上生成文件。

## 构建变量

| 变量 | 用途 |
|---|---|
| `PORT` | 烧录串口设备；默认为 `/dev/ttyUSB0` |
| `BAUD` | 烧录波特率；默认为 `2000000` |
| `JOBS` | 并行任务数；默认为主机 CPU 数量 |
| `S31_LEAN_RADIO` | `1` 为精简无线配置（默认值），`0` 为完整外设配置 |
| `DEFCONFIG` | 内核配置；默认为 `esp32s31_defconfig` |
| `LINUX_TARGET` | 内核镜像目标；默认为 `xipImage` |
| `IDF_EXPORT` | 要使用的 ESP-IDF `export.sh` 路径 |
| `IDF_PATH`, `IDF_ROOT` | ESP-IDF 的安装和查找路径 |
| `TOOLCHAIN_RELEASE_TAG` | `configs/build-versions.mk` 选定的版本；当前为 `esp32s31-linux-gcc-15.2.0-5` |
| `TOOLCHAIN_RELEASE_REPOSITORY` | 提供工具链发行版的仓库 |
| `CROSSTOOL_NG_DIR` | `toolchain-source` 使用的源码目录 |

集成无线固件构建选择 Wi-Fi/蓝牙组合 payload。
运行时使用 `esp32-config` 选择生效的无线模式。

OpenSBI 使用主仓库变量 `FW_TEXT_START`（默认 `0x40000400`）和
`FW_RW_START`（默认 `0x2F00F000`）。Linux 使用 Kconfig 选项
`CONFIG_XIP_PHYS_ADDR`，S31 defconfig 将其设为 `0x40400000`；这是 CPU 可见的
XIP 地址，并非 Flash 原始偏移。
修改布局时需要同步调整链接脚本、Flash 映射和设备树；见[内存映射](../hw-reference/memory-map.md)和
[flash 布局](../hw-reference/flash-layout.md)。
