# 发布与许可

推送到主仓库 `main` 时运行发布工作流的快速检查。检查通过且最新提交信息以 `release:` 开头时，才运行镜像构建和发布任务。构建使用同一套完整开发板配置，并验证驱动、布局、工具链与匹配镜像来源。

## 镜像集与发布文件

`make image` 生成并验证六个组件：`spl_app.bin`、`u-boot.itb`、`esp32s31_generic.dtb`、`radio.bin`、`xipImage` 和 `rootfs.sqfs`，以及合并镜像、`radio.json`、`build-manifest.json`、校验和文件。通过验证后，完整匹配集位于 `dist/<build-id>/`，`dist/current` 指向该集合。

本地镜像清单由 `tools/release/assets.py` 管理。当前 GitHub Release 工作流验证完整集合后，只上传 `s31_full_flash.bin`，并使用仓库的 `configs/release-notes.md` 作为说明正文，只包含 `root` 用户名、`esp32-config` 提示和 Linux/Windows 烧录命令。发布标签对应主仓库源码提交。参见[发布工作流](https://github.com/GrieferPig/esp32-s31-linux/blob/main/.github/workflows/release-images.yml)和[发布正文](https://github.com/GrieferPig/esp32-s31-linux/blob/main/configs/release-notes.md)。不能假设 GitHub Release 提供全部本地组件或校验文件；以该次发布的实际附件为准。

## 准备发布

构建并测试改动，更新当前功能状态和安装说明，确认镜像符合 Flash 容量及匹配关系。清单应记录来源、工具链、配置、哈希及继承产物的来源；无法验证的优化或硬件能力应明确标注。迁移与验证细节保存在文档及测试记录中。

合并镜像会覆盖 persist。向现有用户提供保留数据的更新时，应提供并验证完整匹配组件集，而且用户已安装的布局必须相同。更换布局必须先备份并全新安装；参见[Flash 布局](../hw-reference/flash-layout.md)。

## 打包无线文件

完成 `make image` 后，可以单独打包工程用无线归档：

```sh
make radio-package
```

输出为 `out/images/esp32s31-radio-engineering-only.tar.xz`。该命令只打包已有、通过验证的输出，不重新构建或重新链接模块。包内的模块、无线镜像、元数据和覆盖层必须与对应内核配套。

发布模式需要再分发授权及对应源码归档：

```sh
tools/release/radio_bundle.sh --release \
  --grant GRANT_FILE --source-archive SOURCE_ARCHIVE
```

请使用本次发布审核后的文件。工具验证文件存在并复制入包，但不会判断授权范围，也不能证明源码归档涵盖每个二进制输入。输出为 `out/images/esp32s31-radio-release.tar.xz`。合并镜像发布工作流不会调用该发布模式。

## 声明与源码

检查镜像内每个组件的条款，包括乐鑫无线库和 BTstack，按要求提供声明、许可证及源码材料。参考主仓库的[第三方声明](https://github.com/GrieferPig/esp32-s31-linux/blob/main/THIRD_PARTY_NOTICES.md)和[无线软件包许可](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/radio/RADIO_BUNDLE_LICENSES.md)。打包命令不会改变许可条款。

## 测试记录

提供相关主机、构建、模拟器或物理开发板结果，并明确各自证据范围。记录开发板型号、构建标识、命令和未解决问题。没有当前物理运行记录时，不应把源码检查写成硬件通过。分享日志前移除凭据及私钥。
