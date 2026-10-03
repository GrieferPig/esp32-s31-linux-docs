# 从源码构建

发布工作流使用 x86-64 Ubuntu 24.04 LTS 作为参考主机。预构建 Linux 工具链也是 x86-64 Linux 程序；其他主机架构需要合适的源码构建工具链。Buildroot 需要 Linux；
这里不涵盖原生 Windows 和 macOS 构建。请为源码树、工具链、下载的软件包
和构建产物预留空间。磁盘与内存用量取决于所选软件包及构建并行度；
这里不提供未经测量的最低配置。

## 1. 安装主机工具

在 Ubuntu 24.04 上安装构建依赖及下文使用的工具：

```sh
sudo apt-get update
sudo apt-get install -y \
  git curl wget file python3 python3-pip python3-venv cmake \
  bison bc build-essential ccache cpio device-tree-compiler flex gperf \
  libffi-dev libssl-dev libncurses-dev ninja-build \
  python3-pkg-resources python3-pyelftools python3-dev swig rsync unzip xz-utils mtd-utils squashfs-tools
```

`libncurses-dev` 用于 Buildroot 配置菜单。`mtd-utils` 提供可选目标
`make persist` 所需的 `mkfs.jffs2`。

## 2. 检出源码

检出项目与其固定的子模块版本：

```sh
git clone --recurse-submodules https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
git submodule update --init --recursive
```

后续构建命令均在此目录执行。如果要基于其他版本开发，应同时使用该版本的
`configs/build-versions.mk` 和所记录的子模块提交；参见
[子模块工作流程](../contribute/submodule-workflow.md)。

## 3. 安装 ESP-IDF 和 Linux 工具链

### ESP-IDF

LP 和无线固件构建会使用 ESP-IDF 的组件、库和 ESP 工具链。主构建流程会检查
`configs/build-versions.mk` 中指定的 ESP-IDF 精确版本；随意检出默认分支无法
满足这项检查。

新安装时，请将 `IDF_PATH` 指向尚未使用的目录：

```sh
export IDF_PATH="$HOME/esp-idf"
git clone https://github.com/espressif/esp-idf.git "$IDF_PATH"
ESP_IDF_REF=$(sed -n 's/^ESP_IDF_REF := //p' configs/build-versions.mk)
git -C "$IDF_PATH" checkout "$ESP_IDF_REF"
git -C "$IDF_PATH" submodule update --init --recursive
"$IDF_PATH/install.sh" esp32s31
. "$IDF_PATH/export.sh"
```

如果其他项目已在使用该目录，请修改 `IDF_PATH`。每次打开新终端后，都需要
导出相同的 `IDF_PATH` 并再次加载其 `export.sh`。构建和烧录目标使用该
ESP-IDF 环境中的 `esptool`。仅烧录发布镜像时所需的独立安装步骤见
[烧录与首次启动](flash-and-first-boot.md)。

### Linux 工具链

项目使用 [crosstool-NG-s31](https://github.com/GrieferPig/crosstool-NG-s31)
提供的定制工具链，其中包含本移植所需的编译器修改。下载
`configs/build-versions.mk` 选定的版本：

```sh
make toolchain-fetch
```

在本源码版本中，选定的发布版本为 `esp32s31-linux-gcc-15.2.0-5`。
该目标会核对下载文件的校验和，并将工具链安装到
`cache/toolchains/riscv32-esp-linux-musl`。修改编译器或 ABI 参数前，请先阅读
[指令集与工具链](../hw-reference/isa.md)。

## 4. 构建与烧录

使用同一套[完整开发板配置](build-configuration.md)，在主机上依次检查环境、获取固定依赖并生成镜像：

```sh
make doctor
make fetch
make image
```

`make image` 生成组件镜像、合并安装镜像、清单及校验和，验证匹配关系后发布到 `dist/<build-id>/`，并更新 `dist/current`。`make all` 是它的别名，不会访问串口或写入开发板。可设置 `JOBS` 限制并行度，例如 `make JOBS=4 image`。

也可以构建单个组件及其依赖：

```sh
make uboot
make linux
make rootfs
```

完成 `make image` 后，要更新已使用当前紧凑布局的开发板并保留 persist，可执行：

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-existing-all
```

此目标验证并写入 `dist/current` 的已有匹配集，不重新构建；`flash-all` 是其别名。部分更新目标会拒绝执行，因为无法确认板上其他组件的标识。`make build-flash` 显式组合构建和烧录。更换布局时必须先备份并重新安装；参见[烧录与首次启动](flash-and-first-boot.md)。

## 5. 构建产物

常规 `make all` 构建会生成以下产物：

| `out/images/` 下的路径 | 内容 |
|---|---|
| `u-boot-spl-dtb.bin` | 包含 DTB 的 SPL；用于生成 ROM 镜像封装的中间产物 |
| `spl_app.bin` | 以 ESP ROM 镜像格式封装的 SPL |
| `u-boot.itb` | 包含 OpenSBI、U-Boot 主程序及相关数据的 FIT |
| `esp32s31_generic.dtb` | Linux 设备树 |
| `xipImage` | 在 Flash 中就地执行的 Linux 内核 |
| `rootfs.sqfs` | SquashFS 根文件系统 |
| `radio.bin` | 根据当前内核与模块预链接的无线 XIP 载荷 |
| `radio.json` | 内核、模块、载荷、导入及无线镜像的构建绑定与哈希 |
| `s31_full_flash.bin` | 合并安装镜像；烧录时会覆盖 persist 区域 |
| `build-manifest.json` | 构建来源与产物元数据 |
| `SHA256SUMS` | 发布镜像文件及清单的校验和 |

`make persist` 单独生成空的 `out/images/persist.jffs2`，不属于常规构建。擦除持久化数据需要独立、明确的维护流程；集成固件更新目标不会执行该操作。

完整目标列表见 [Make 命令参考](../resources/make-reference.md)。

原生组件输出位于 `out/linux/`、`out/opensbi/`、`out/u-boot/`、`out/idf-radio/`、`out/radio/`、`out/lp/` 和 `out/buildroot/`。共享下载与工具链位于 `cache/`；`make clean` 仅清理构建输出。

主机路径和任务数可以写入被忽略的 `local.mk`：

```make
IDF_EXPORT := /opt/esp-idf/export.sh
JOBS := 4
```

显式指定 `ROOTFS_BASELINE=/absolute/path/to/rootfs.sqfs` 时，可用当前无线模块重新打包已验证的 rootfs。清单记录继承来源，并检查完整运行文件及模块清单；缺少必要用户空间文件会被拒绝。明确提供 `ROOTFS_BUSYBOX_BUILD` 证据时，只能从固定源码恢复缺失的标准日志/cron 初始化脚本。继承二进制的优化状态未经此次构建验证，这不是干净的 Buildroot 重建，也不能验证无关的 rootfs 源码更改。
