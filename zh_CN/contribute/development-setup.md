# 开发环境

先按照[从源码构建](../get-started/build-from-source.md)安装工具并构建镜像。所有构建使用完整开发板配置。

## 查找源码

| 目录 | 内容 |
|---|---|
| `linux-esp32-s31/` | Linux 内核、驱动、设备树和内核配置 |
| `opensbi-esp32-s31/` | M 模式固件和平台服务 |
| `u-boot-esp32-s31/` | SPL 和 U-Boot |
| `buildroot/` | Buildroot |
| `buildroot-external/` | 开发板文件、软件包和根文件系统配置 |
| `firmware/` | 无线和 LP 固件 |
| `rootfs/` | 项目用户空间工具的源码 |
| `tools/` | 主机构建工具和测试 |
| `docs/` | 本文档 |

内核、启动固件、Buildroot 和文档都是 Git 子模块。编辑前，请在相应子模块中创建分支。[子模块指南](submodule-workflow.md)介绍了如何提交这些改动。

## 修改后重新构建

使用主项目的 Makefile 进行集成构建：

```sh
make linux
make rootfs
```

修改驱动或设备树后，通常需要运行 `make linux`。更新目标程序、启动脚本或打包的覆盖层后，还需要运行 `make rootfs`。启动固件的改动使用 `make uboot`，无线固件的改动则使用[无线构建流程](../api-guides/radio-payload-development.md)。

组件构建树位于 `out/`，LP 固件在 `out/lp/` 构建并暂存到 `out/staging/overlay/`。生成的 PIE 测试数据位于 `out/generated/`，不会写入源码覆盖目录。持久配置输入见[构建配置](../get-started/build-configuration.md)。完成修改后运行 `make image`，再用 `make flash-existing-all` 部署完整匹配集。

## 测试改动

烧录前，在主仓库根目录运行主机回归测试：

```sh
make check-host
```

该目标检查布局并运行 `tools/tests`、`tests` 和 GPIO shell 回归测试，不获取依赖。先运行 `make btstack-source` 准备固定的 BTstack 源码；若还需完整固件构建，则用 `make fetch` 准备全部固定依赖。
它需要 Python、源码子模块、主机 C 编译器，以及源码构建指南中安装的构建工具。

激活下文的文档虚拟环境后，安装 CI 使用的设备树 schema 依赖。项目工具链
安装完成后，可运行包含主机测试、严格文档构建和设备树验证的组合检查：

```sh
python -m pip install dtschema==2026.6
make check-fast
```

`check-dt` 使用项目交叉编译器。快速检查工作流则安装
`gcc-riscv64-linux-gnu`，并调用
`python3 tools/checks/devicetree.py --cross-compile riscv64-linux-gnu-`。两种方式
都会检查 schema、编译后的设备树和合并后的覆盖层。

随后在开发板上检查该功能，包括错误情况和使用后的清理。主机检查无法证明
电气或无线行为正确。[HIL 指南](testing-hil.md)介绍了自动化开发板和对端测试。

提交改动时，请说明问题、修复方法和测试方式。如果开发板和接线会影响结果，也应一并说明。

## 编辑文档

文档仓库有独立的 Python 依赖和构建命令：

```sh
cd docs
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
make html
```

按照[编写文档](writing-documentation.md)中的本地 HTTP 预览步骤检查结果和搜索功能；该指南还介绍了页面结构和语言风格。运行主仓库的 Make 目标前，请通过 `cd ..` 返回主仓库。
