# 发布与许可

每次推送到 `main` 都会启动发布工作流中的快速检查。检查通过后，只有最新
提交的信息以 `release:` 开头时，才会运行镜像构建和发布任务。该任务使用
`S31_LEAN_RADIO=0`，并检查预期的完整外设驱动选项。

发布列表由 `tools/release_assets.py` 生成，包括六个组件镜像（`spl_app.bin`、
`u-boot.itb`、`esp32s31_generic.dtb`、`radio.sqfs`、`xipImage` 和 `rootfs.sqfs`）、
合并镜像 `s31_full_flash.bin`、`build-manifest.json` 及 `SHA256SUMS`。
工作流在发布前核对这些校验和。这是文档对应源码版本的工作流行为；
各次发布的实际输入应以其清单为准。

## 准备发布

构建并测试改动，更新功能状态和安装说明，并确认镜像符合 Flash 布局的容量限制。在发布说明中列出构建版本和迁移说明。

合并安装镜像会覆盖已保存的设置。为现有用户提供更新时，也应说明如何通过分镜像烧录保留数据。

## 打包无线文件

要生成单独的工程用无线归档，运行：

```sh
make radio-package
```

产物位于 `build/radio-package/` 下。打包工具还提供发布模式，将再分发授权和对应源码归档一起打包：

```sh
tools/build_radio_bundle.sh --release \
  --grant GRANT_FILE --source-archive SOURCE_ARCHIVE
```

将两个路径替换为此次发布已审核的文件。工具会检查文件是否存在，并将其复制到包中，但不会验证授权范围，也不会确认
源码归档是否对应每个二进制输入。选择发布模式前，请根据实际载荷审核这些
文件。合并镜像工作流单独发布镜像，不会调用此工具的发布模式。

## 附带声明和源码

检查镜像所含组件的条款，包括乐鑫无线库和 BTstack。按要求随发布包附带相关声明、许可证文本和源码材料。

可先查看主仓库的[第三方声明](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/THIRD_PARTY_NOTICES.md)和无线目录的[软件包许可](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/RADIO_BUNDLE_LICENSES.md)。打包命令不会改变这些条款。

## 记录测试结果

随发布附上相关构建和开发板测试结果，或在发布说明中提供链接。列出开发板型号、构建配置、测试命令和未解决的问题。分享日志前，请移除凭据和私钥。
