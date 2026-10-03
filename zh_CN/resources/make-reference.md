# Make 参考

以下命令在主仓库根目录执行。首次构建参见[从源码构建](../get-started/build-from-source.md)。

## 常用命令

```sh
make help                 # 默认目标；仅显示帮助
make doctor               # 检查环境
make fetch                # 获取固定版本依赖
make build                # 构建组件
make image                # 打包、验证并发布匹配镜像集
make check                # 主机、文档和设备树检查
make flash-existing-all   # 烧录已有匹配集，不构建
```

所有构建采用[完整开发板配置](../get-started/build-configuration.md)和原生 `-Os` 体积优化。
Linux 使用上游 `TRIM_UNUSED_KSYMS` 并保留自动生成的无线导入白名单；ext4 内置。
主机路径和并行任务数可写入忽略跟踪的 `local.mk`，例如 `JOBS := 4`。`DEBUG=1` 增加诊断配置。

## 构建目标

| 目标 | 说明 |
|---|---|
| `help` | 显示公共命令；这是默认目标 |
| `doctor` | 检查主机、工具链和 ESP-IDF 环境 |
| `fetch` | 初始化子模块，获取工具链、BTstack 和 rootfs 源码缓存 |
| `fetch-rootfs` | 获取所选 Buildroot 软件包源码，不构建目标软件包 |
| `download` | 单独初始化源码子模块，不与构建目标混用 |
| `toolchain-fetch` | 下载并验证固定版本 Linux 工具链 |
| `toolchain` | 检查已安装工具链，不进行下载 |
| `toolchain-source` | 使用指定 crosstool-NG 源码构建工具链 |
| `build` | 构建启动固件、Linux、rootfs 和无线镜像 |
| `image`、`all`、`flash-image` | 构建、生成合并镜像和清单，验证后发布至 `dist/` |
| `opensbi` | 为 FIT 构建并验证 `fw_dynamic.bin` |
| `uboot`、`bootloader` | 构建 SPL、`spl_app.bin` 和 `u-boot.itb` |
| `linux` | 构建 XIP 内核、DTB、DTBO 和无线模块 |
| `rootfs`、`initramfs` | 构建 SquashFS 根文件系统 `out/images/rootfs.sqfs` |
| `idf-check` | 根据依赖锁检查 ESP-IDF |
| `radio-idf-deps` | 构建 ESP-IDF 无线依赖 |
| `radio-linux-payload` | 生成无线中间载荷、导入桩及内核导出白名单 |
| `radio-module` | 检查集成无线模块和载荷输出 |
| `radio-image`、`radio-fs` | 创建预链接 `out/images/radio.bin` |
| `radio-package` | 从已验证输出打包 `out/images/esp32s31-radio-engineering-only.tar.xz`，不构建 |
| `lp-firmware` | 构建 `out/lp/` 并暂存到 `out/staging/overlay/` |
| `persist` | 创建空的 `out/images/persist.jffs2`，不烧录 |
| `coremark` | 构建基准测试，并复制到 `out/staging/coremark/coremark.exe` |
| `buildroot-menuconfig` | 打开 Buildroot 配置菜单 |
| `buildroot-clean`、`buildroot-reconfigure` | 删除 Buildroot 输出以便按新输入重建 |
| `clean` | 删除构建树、生成文件、暂存、镜像及报告；保留缓存 |
| `fullclean` | 执行 `clean`；同样保留下载和工具链缓存 |
| `check-layout` | 检查共享 Flash 和内存布局 |
| `check-host` | 检查布局并运行主机回归测试，不获取依赖 |
| `check-docs` | 使用严格 Sphinx 警告设置构建文档 |
| `check-dt` | 使用项目交叉编译器验证设备树和绑定 |
| `check`、`check-fast` | 运行主机、文档和设备树检查 |
| `check-artifacts` | 验证 `out/images/build-manifest.json` 及匹配产物 |
| `build-manifest` | 生成 `out/images/build-manifest.json` |

最终产物位于 `out/images/`；验证后发布的镜像集位于 `dist/`，由 `dist/current` 选择当前集合。
原生组件对象、生成文件、暂存和报告位于 `out/`，下载与工具链缓存位于 `cache/`。

Linux、U-Boot 和无线配置输入变化会触发原生重新配置；输入未变时保留增量构建。
Buildroot 软件包选择或工具链变化则需要先运行 `make buildroot-reconfigure`，
删除选定的 Buildroot 输出树后再构建。执行前应把菜单中的预期更改保存到受版本控制的
defconfig；需要长期保留的内核选项应写回 defconfig 或 `configs/kernel/`。

`ROOTFS_BASELINE=/absolute/path/to/rootfs.sqfs` 显式选择增量重新打包，并记录来源。
它检查必需的完整用户空间运行文件及精确模块列表，不完整的基础镜像会被拒绝；
这不是干净的 Buildroot 重建，也不代表继承的用户空间二进制已经按 `-Os` 重新编译。
只有缺少标准日志/cron 启动脚本时，才可通过
`ROOTFS_BUSYBOX_BUILD=/path/to/busybox-build` 显式允许从固定版本的 Buildroot 源码恢复它们。
重新打包工具核对继承二进制中的 applet/帮助字节，记录新增脚本，并保留现有文件系统元数据。

## 烧录目标

默认串口为 `/dev/ttyUSB0`，波特率 2000000：

```sh
make PORT=/dev/ttyUSB1 BAUD=921600 flash-existing-all
```

| 目标 | 行为 |
|---|---|
| `flash-existing-all`、`flash-all` | 验证并烧录 `dist/current` 中的六个匹配组件，不重新构建 |
| `build-flash` | 先执行 `image`，再烧录已验证匹配集 |
| `flash-bootloader`、`flash-opensbi`、`flash-linux`、`flash-dtb` | 拒绝部分更新，因为无法确认已安装的配套组件 |
| `flash-radio`、`flash-existing-radio`、`flash-rootfs`、`flash-existing-rootfs` | 同样拒绝部分更新 |
| `flash-persist`、`erase` | 拒绝执行；破坏性维护需要独立、明确的流程 |

烧录工具只解析一次 `dist/current`，随后验证并使用该不可变镜像集。清单核对组件和
合并镜像哈希、无线的内核/模块/载荷/导入绑定及配置身份；这些主机检查不能证明硬件启动成功。

同布局的匹配组件更新保留 persist；合并镜像烧录会覆盖 persist。改变布局前应备份并全新安装。环境安装、连接与控制台步骤见[烧录与首次启动](../get-started/flash-and-first-boot.md)。

## 构建变量

| 变量 | 用途 |
|---|---|
| `PORT`、`BAUD` | 烧录连接 |
| `JOBS` | 并行编译数，默认主机 CPU 数量 |
| `DEBUG` | `1` 启用额外诊断配置 |
| `OUT_ROOT` | 构建输出根目录，默认 `out/` |
| `CACHE_DIR` | 共享缓存根目录，默认 `cache/` |
| `DEFCONFIG` | 原生内核 defconfig，默认 `esp32s31_defconfig` |
| `LINUX_TARGET` | 内核镜像目标，默认 `xipImage` |
| `IDF_EXPORT` | ESP-IDF `export.sh` 路径 |
| `IDF_PATH`、`IDF_ROOT` | ESP-IDF 安装及查找路径 |
| `HOST_PYTHON` | U-Boot 主机解释器，包含 env-shebang 工具；默认取当前 `python3`，激活 ESP-IDF 时应显式选择已准备依赖的主机解释器 |
| `UBOOT_PYTHONPATH` | 该 U-Boot 主机解释器可选的额外模块搜索路径 |
| `TOOLCHAIN_PREFIX` | 已安装 Linux 工具链目录 |
| `TOOLCHAIN_RELEASE_TAG` | `configs/build-versions.mk` 选择的版本 |
| `CROSSTOOL_NG_DIR` | `toolchain-source` 使用的源码目录 |
| `S31_ALLOW_UNPINNED` | 显式启用实验性的非固定 ESP-IDF 版本 |
| `ROOTFS_BASELINE` | 显式请求从已有 rootfs 增量重新打包，保留来源记录 |
| `ROOTFS_BUSYBOX_BUILD` | 用于验证缺失标准服务脚本能否恢复的现有 BusyBox 构建目录 |

集成构建始终包含 Wi-Fi/蓝牙组合载荷；运行模式由板端 `esp32-config` 选择。OpenSBI 的 `FW_TEXT_START` 为 `0x4000E400`，`FW_RW_START` 为 `0x2F00F000`。Linux `CONFIG_XIP_PHYS_ADDR` 为 `0x40400000`，是 CPU 物理地址；对应原始 Flash 偏移 `0x400000`。更改布局必须同步验证链接、映射及设备树，见[Flash 布局](../hw-reference/flash-layout.md)。
