# 无线架构

Wi-Fi 和蓝牙共享 `esp32s31-radio` Linux 模块，其中包含 Linux 前端、XIP 固件加载器和乐鑫无线代码所需的运行时。

| 应用路径 | 公共模块中的前端 |
|---|---|
| Wi-Fi 套接字应用 | mac80211/cfg80211，单 STA 接口 |
| 内置 BTstack 应用 | `/dev/s31-hci` 直接 H4 设备 |
| 替代的 Linux 蓝牙主机 | `direct_hci=0` 选择 Linux HCI 控制器 |

三条路径连接同一无线运行时和预链接 Flash XIP 载荷。AP 和 AP+STA 不由当前前端公开。mac80211 软件监听仍受 STA 接收过滤限制，参见[Wi-Fi 高级用法](../../api-guides/wifi-advanced.md)。帧格式与模块设置见[无线接口参考](index.md)。

## 固件加载

无线固件组合 ESP-IDF 库与本项目的兼容代码。主机预链接工具根据已构建的内核解析代码和常量重定位，生成 `out/images/radio.bin`。多数无线代码从专用 Flash 分区就地执行，选定的 Wi-Fi 热点代码复制到内部 SRAM。压缩后的 Linux 模块位于 rootfs 的 `/usr/lib/s31-radio`；可重定位文件 `esp32s31-radio-fw-v1.o` 仅为中间构建产物。

启动时，加载器验证映射镜像的 ABI、内存布局及头部/内容 CRC，复制 SRAM 代码和初始可写数据，清零 BSS，绑定模块导入并读取固定导出。检查能发现不兼容布局与损坏，但不能证明组件来自同次构建。内核、rootfs/模块和无线镜像必须作为匹配集一起构建和部署。

固定 SRAM 保留区见[内存映射](../../hw-reference/memory-map.md)，原始 Flash 分区见[Flash 布局](../../hw-reference/flash-layout.md)。

## 运行时与 CPU 分配

无线设备中断和公共工作线程使用 HP 核 0。兼容任务保留其请求的亲和性，无亲和性任务可以迁移。SoftMAC 在可用时也使用 HP 核 1。仅 Wi-Fi 的 SoftMAC 模式使用原生任务服务，不启动公共无线工作线程。

兼容层为无线库提供任务、队列、定时器与同步。Wi-Fi 前端接收借用的辅助帧，在回调返回前复制需要保留的数据，再通过 NAPI 交给 mac80211。此路径可能使用原子分配，并非完全依靠预分配缓冲区。

## 挂起与恢复

公共运行时具备停止、复位和重启支持，包括还原固件初始可变数据，但不代表每个前端已实现恢复。当前 SoftMAC 在接口运行时拒绝挂起；无线模块会先返回该错误，而不是继续停止蓝牙或共享载荷。SoftMAC 没有活动连接重放逻辑，不应依赖系统睡眠后自动恢复 Wi-Fi、蓝牙或组合连接。Wi-Fi 挂起 HIL 是诊断序列。

服务控制见[Wi-Fi 与蓝牙设置](../../user-guides/networking.md)，系统睡眠限制见[电源管理](../../api-guides/power-management.md)，代码修改和匹配集部署见[无线固件开发](../../api-guides/radio-payload-development.md)。
