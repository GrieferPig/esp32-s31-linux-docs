# 无线固件开发

无线固件将乐鑫的 Wi-Fi 和蓝牙库与本移植项目的 OS 适配层结合起来。Linux 通过公共无线模块从 `radio.sqfs` 加载它。修改 `firmware/radio/` 中的代码时可参考本指南；Linux 网络和蓝牙接口的改动通常属于内核前端。[无线架构](../api-reference/radio/architecture.md)介绍了它们之间的关系。

## 构建与部署

按照[从源码构建](../get-started/build-from-source.md)准备环境，保持所选构建配置已导出，并在主机上的主项目目录运行：

```sh
. "$IDF_PATH/export.sh"
export IDF_EXPORT="$IDF_PATH/export.sh"
make radio-fs
make flash-existing-radio PORT=/dev/ttyUSB0
```

替换串口路径，并在烧录前关闭串口监视程序。`radio-fs` 会构建 ESP-IDF 依赖、载荷、Linux 模块和根文件系统依赖，然后打包 `build/radio.sqfs`。烧录命令会写入已有无线镜像，不会重新构建。

仅更新无线镜像时，开发板上必须已有匹配的内核。如果修改了内核代码、配置或模块使用的接口，应改用 `make flash-all` 更新对应内核和其他镜像。镜像更新方法见[烧录与首次启动](../get-started/flash-and-first-boot.md)。

[主项目 Makefile](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L202-L284) 还提供各构建阶段的独立目标：

| 目标 | 结果 |
|---|---|
| `make radio-idf-deps` | 构建 ESP-IDF 库依赖 |
| `make radio-linux-payload` | 构建 `build/esp32s31-radio-fw-v1.o`，并重新生成内核导入桩代码 |
| `make radio-fs` | 重新构建依赖并打包 `build/radio.sqfs` |

## 查找实现

| 文件或目录 | 作用 |
|---|---|
| `firmware/radio/radio_stack.c` | 调用 ESP-IDF 库的 Wi-Fi/蓝牙操作 |
| `firmware/radio/s31_rtos/` | 固件侧任务和同步适配层 |
| `firmware/radio/Makefile` | 载荷链接输入、保留的导出符号和导入桩生成 |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-smode.c` | Linux 无线命令队列、工作线程和 SRAM 分配 |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-loader.c` | ELF 加载、导出符号解析和入口包装函数 |
| `linux-esp32-s31/drivers/net/wireless/espressif/esp32s31_wifi.c` | cfg80211/netdev 前端 |
| `linux-esp32-s31/drivers/bluetooth/hci_esp32s31.c` | 直接 HCI 和 Linux HCI 前端 |

### 示例：跟踪 STA 连接

从 [Wi-Fi 前端](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c#L636-L689)的 `s31_cfg_connect()` 开始。它验证 cfg80211 请求，然后通过 CPU0 上的工作调用 `esp32s31_radio_wifi_connect()`。无线核心将连接命令入队，把参数复制到 SRAM，并启动 `s31_radio_wifi_connect_task()`。

加载器包装函数将该函数解析为 [radio_stack.c](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/radio_stack.c#L1246-L1303) 中同名的载荷入口。该函数准备 ESP-IDF STA 配置并提交连接。结果通过 `s31_radio_wifi_connected()` 和前端注册的回调返回。

添加新入口时，可沿用这条调用链：在载荷链接时保留导出符号，在加载器中添加导出查找和包装函数，并更新调用代码。使用 `make radio-linux-payload` 重新生成 `esp32s31-radio-imports.S`，不要手工维护生成的桩代码。修改共享结构或调用约定时，需要同步修改所有使用方；兼容性发生变化时，还应更新相应 ABI 版本。

无线回调可能在中断上下文中运行。此类工作应尽量简短；如果数据需要在回调结束后继续使用，应复制到使用方拥有的存储空间。公共回调约定定义在内核的 `include/linux/esp32s31-radio.h` 中。

## 检查内存和运行状态

无线缓冲区和 OS 适配层分配使用预留的内部 SRAM 池。ELF 加载器会另行分配已加载固件所需的内存，包括可变数据段；固定 SRAM 池并不涵盖全部固件内存。参见[内存映射](../hw-reference/memory-map.md)。

[无线参考](radio-status)介绍了如何读取 `radio_health`。[属性实现](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c#L27-L63)报告堆使用量、峰值、总容量、丢包、初始化结果和工作线程活动。分配失败还会出现在内核诊断信息中；`radio_health` 没有独立的分配失败计数。请同时检查 `dmesg`。

## 测试更新

启动后，按照 [Wi-Fi 与蓝牙设置](../user-guides/networking.md)测试改动涉及的模式，再测试两个服务同时运行。检查启动、数据传输、队列压力、关闭和重新加载。[HIL 指南](../contribute/testing-hil.md)包含对端测试；请记录实际运行的测试及结果。

要单独生成无线归档，运行 `make radio-package`。分发包含第三方库的固件前，请参阅[发布与许可](../contribute/release-and-legal.md)。
