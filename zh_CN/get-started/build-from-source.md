# 从源码构建

发布工作流使用 Ubuntu 24.04 LTS 作为参考主机。Buildroot 需要 Linux；
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
  python3-pkg-resources python3-pyelftools rsync unzip xz-utils mtd-utils
```

`libncurses-dev` 用于 Buildroot 配置菜单。`mtd-utils` 提供可选目标
`make persist` 所需的 `mkfs.jffs2`。

## 2. 检出源码

本指南对应主仓库版本
`a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104`。先检出该提交，再初始化它所记录的
各组件版本：

```sh
git clone https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
git checkout a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104
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
git -C "$IDF_PATH" checkout a602e67b0bf9ee0806dc4e1df7afc9affedf5c33
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
make toolchain
```

在本源码版本中，选定的发布版本为 `esp32s31-linux-gcc-15.2.0-5`。
该目标会核对下载文件的校验和，并将工具链安装到
`toolchain/riscv32-esp-linux-musl`。修改编译器或 ABI 参数前，请先阅读
[指令集与工具链](../hw-reference/isa.md)。

## 4. 构建与烧录

选择一个[构建配置](build-profiles.md)。本地构建默认为精简无线配置；若要与
发布工作流保持一致并启用可选外设驱动，请使用完整外设配置：

```sh
export S31_LEAN_RADIO=0
make all
```

`make all` 在主机上生成各组件镜像、合并安装镜像、清单及校验和，不会写入
开发板。如需限制并行编译任务数，可设置 `JOBS`，例如 `make JOBS=4 all`。

也可以使用组件目标：

```sh
make uboot
make linux
make rootfs
```

这些集成目标还会构建各自的依赖。例如，`make rootfs` 依赖 Linux、无线固件
和 LP 固件的构建步骤。

要更新已连接的开发板并保留 persist 分区，请保持相同的构建配置，然后执行：

```sh
make PORT=/dev/ttyUSB0 BAUD=2000000 flash-all
```

此目标会在烧录前再次构建其依赖。请将 `PORT` 替换为开发板的串口设备。
安装、串口设置和首次登录步骤见[烧录与首次启动](flash-and-first-boot.md)。

## 5. 构建产物

常规 `make all` 构建会生成以下产物：

| `build/` 下的路径 | 内容 |
|---|---|
| `u-boot-spl-dtb.bin` | 包含 DTB 的 SPL；用于生成 ROM 镜像封装的中间产物 |
| `spl_app.bin` | 以 ESP ROM 镜像格式封装的 SPL |
| `u-boot.itb` | 包含 OpenSBI、U-Boot 主程序及相关数据的 FIT |
| `esp32s31_generic.dtb` | Linux 设备树 |
| `xipImage` | 在 Flash 中就地执行的 Linux 内核 |
| `rootfs.sqfs` | SquashFS 根文件系统 |
| `radio.sqfs` | 无线模块和固件文件系统 |
| `s31_full_flash.bin` | 合并安装镜像；烧录时会覆盖 persist 区域 |
| `build-manifest.json` | 构建来源与产物元数据 |
| `SHA256SUMS` | 发布镜像文件及清单的校验和 |

`make persist` 单独生成空的 `build/persist.jffs2`；它不是 `make all` 的产物。
`make flash-persist` 会写入这个空文件系统，清除已有的持久化文件和设置。

完整目标列表见 [Make 命令参考](../resources/make-reference.md)。
