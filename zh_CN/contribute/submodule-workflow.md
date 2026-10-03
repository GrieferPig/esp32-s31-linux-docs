# 使用子模块

主仓库将 Linux、OpenSBI、U-Boot、Buildroot 和文档作为子模块引入。每个子模块都有独立的提交和分支。

## 仓库默认分支

| 仓库 | 默认分支 |
|---|---|
| 主仓库与 docs | `main` |
| Linux | `v6.18-esp32-s31` |
| OpenSBI | `v1.9-esp32-s31` |
| U-Boot | `v2024.07-esp32s31` |

默认分支用于浏览与开发，不是可重复构建的版本选择。集成构建以主仓库记录的子模块 gitlink 提交为准，并配合 `configs/build-versions.mk` 中的 ESP-IDF、工具链和 BTstack 固定版本。

## 获取源码

新建检出目录时，请按照[从源码构建](../get-started/build-from-source.md)选择
文档对应的主仓库提交、子模块版本，以及匹配的 ESP-IDF/工具链版本。子模块
更新使用所选主仓库版本中记录的提交，不会将每个组件更新到各自分支的最新提交。

已有检出目录在拉取主仓库改动后，运行：

```sh
git submodule update --init --recursive
```

更新子模块前，请提交或保存本地改动。

## 进行修改

进入子模块并创建分支。例如，修改内核时：

```sh
cd linux-esp32-s31
git switch -c my-driver-change
```

编辑并测试文件，然后在该仓库内暂存相关路径并提交。准备分享改动时，将分支推送到其他人能够访问的远程仓库。

## 更新主仓库

返回主仓库，记录新的子模块版本：

```sh
cd ..
git add linux-esp32-s31
git diff --cached --submodule=log
git commit -m "Update Linux for driver change"
```

主仓库记录组件的提交，而修改后的文件仍保存在组件仓库中。发布主仓库改动前，请先推送组件提交，以便其他开发者能够检出它。

`docs/` 和启动固件子模块也使用相同流程。

## 检查工作目录

```sh
git status
git submodule status
git diff --submodule=log
```

在子模块内运行 `git status` 可以查看其文件改动。当主仓库显示某个组件已修改，但没有列出具体文件时，可以用这种方式检查。
