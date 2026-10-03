# 无线固件开发

无线固件组合乐鑫 Wi-Fi/蓝牙库与本项目 OS 适配层。主机生成预链接的 `radio.bin`，Linux 通过公共无线模块加载其映射并执行 Flash XIP 代码。Linux 网络和蓝牙接口改动通常属于内核前端；组件关系见[无线架构](../api-reference/radio/architecture.md)。

## 构建与部署

按[从源码构建](../get-started/build-from-source.md)准备环境，在主仓库运行：

```sh
. "$IDF_PATH/export.sh"
export IDF_EXPORT="$IDF_PATH/export.sh"
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

`make image` 构建并验证完整组件集，将镜像写入 `out/images/`，再发布到 `dist/<build-id>/` 并更新 `dist/current`。烧录目标从 `dist/current` 读取已验证组件集，不重新构建，并保留 persist。替换串口路径，烧录前关闭串口监视程序。

内核、rootfs 中的模块和无线镜像具有构建关联，不能只凭 ABI 编号判断可混用。部分更新目标会拒绝执行；应部署匹配集。详见[烧录与首次启动](../get-started/flash-and-first-boot.md)。

| 目标 | 结果 |
|---|---|
| `make radio-idf-deps` | 构建 ESP-IDF 库依赖到 `out/idf-radio/` |
| `make radio-linux-payload` | 生成 `out/generated/esp32s31-radio-fw-v1.o` 及导入桩 |
| `make linux` | 使用导入桩构建内核和模块 |
| `make radio-image` | 对已构建内核/模块预链接，生成 `out/images/radio.bin` |
| `make image` | 构建、检查并发布整套匹配镜像 |

## 查找实现

| 文件或目录 | 作用 |
|---|---|
| `firmware/radio/radio_stack.c` | 调用 ESP-IDF Wi-Fi/蓝牙操作 |
| `firmware/radio/s31_rtos/` | 固件侧任务和同步适配层 |
| `firmware/radio/Makefile` | 链接输入、保留导出及导入桩生成 |
| `tools/build/radio_image.py` | 根据内核和模块生成预链接 XIP 镜像 |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-smode.c` | 公共命令队列、工作线程和 SRAM 分配 |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-loader.c` | XIP 镜像验证、导入绑定和入口包装 |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-xip.h` | XIP 地址与布局约定 |
| `linux-esp32-s31/drivers/net/wireless/espressif/esp32s31_softmac.c` | mac80211 SoftMAC 前端 |
| `linux-esp32-s31/drivers/bluetooth/hci_esp32s31.c` | 直接 HCI 和 Linux HCI 前端 |

跟踪当前 STA 行为时，从 mac80211 回调与原始帧发送/接收路径开始。不要将固件内部连接、AP 或 EAP 操作视为 Linux 当前前端的公开能力。当前支持边界见[Wi-Fi 高级用法](wifi-advanced.md)。

新增入口时，需同步更新载荷导出、加载器包装和调用方，并重新生成导入桩。不要手工编辑生成文件。共享结构或调用约定变化时，更新所有使用方及相应 ABI，重建整套镜像。内核默认裁剪未使用导出；新的模块依赖也需参与同次内核构建，参见[构建配置](../get-started/build-configuration.md)。

## 内存和回调

多数代码在 Flash 中执行，选定的 Wi-Fi 代码复制到固定 SRAM 区域。可写数据与 BSS 使用内核中的 40 KiB PSRAM arena，其地址依赖实际内核构建。无线堆不能覆盖仍在执行的 SRAM 代码；详细边界见[内存映射](../hw-reference/memory-map.md)。

无线回调可能在中断上下文执行。`receive_aux` 帧为借用数据，需要跨回调使用时必须先复制。当前接收路径使用 NAPI，并可能进行原子分配。

[无线状态](radio-status)介绍 `radio_health`，用于检查堆使用量、容量、丢包、初始化结果和工作线程活动。请同时检查 `dmesg` 中的分配失败或加载错误。

## 测试更新

启动后按[Wi-Fi 与蓝牙设置](../user-guides/networking.md)检查变更涉及的模式，再检查组合模式。覆盖启动、数据传输、队列压力、停止和重新加载，并记录实际执行的测试及结果。[HIL 指南](../contribute/testing-hil.md)包含对端测试。当前活动 Wi-Fi 接口会拒绝挂起，不能将运行时重启支持视为自动重连保证。

`make radio-package` 可创建工程用无线归档。分发含第三方库的固件前，请阅读[发布与许可](../contribute/release-and-legal.md)。
