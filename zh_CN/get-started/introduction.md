# 简介

`esp32-s31-linux` 将嵌入式 Linux 系统移植到 ESP32-S31，在两个高性能 CPU 核心
上运行 32 位 RISC-V 内核，并提供 BusyBox shell、Wi-Fi 和蓝牙支持，以及片上
外设驱动。本移植使用 Linux 6.18、U-Boot、OpenSBI 和 Buildroot。

## 功能支持

镜像中包含哪些驱动取决于[构建配置](build-profiles.md)。本地构建默认为精简
无线配置，发布工作流选择完整外设配置。可用接口、测试证据和当前限制见
[功能支持](../resources/support-matrix.md)。

## 快速开始

安装预编译镜像并登录系统，请参照[烧录与首次启动](flash-and-first-boot.md)。

基于文档对应的源码版本构建定制镜像，请参照[从源码构建](build-from-source.md)。

启动后，运行 `esp32-config` 配置开发板。接下来可以阅读
[叠加层目录](../resources/overlay-catalog.md)和
[外设示例](../api-reference/peripherals/index.md)。
