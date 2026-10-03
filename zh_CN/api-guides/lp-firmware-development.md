# LP 固件开发

LP 固件使用[从源码构建](../get-started/build-from-source.md)中介绍的 ESP-IDF 环境。根文件系统可用后，Linux 通过 remoteproc 加载 ELF。

## 构建与安装

在父项目根目录执行：

```sh
make lp-firmware
make rootfs
```

LP 构建生成 `out/lp/esp-idf/main/s31_lp_main/s31_lp_main.elf`，并暂存为 `out/staging/overlay/lib/firmware/esp32s31/s31-lp-core.elf`。rootfs 构建会打包该文件。参见 [LP Makefile](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/Makefile)。

如需在板上替换固件，先将新的 ELF 传输到 `/tmp/s31-lp-core.elf`，再停止 LP 并替换已安装的固件：

```sh
/etc/init.d/S02s31-lp stop
cp /tmp/s31-lp-core.elf /lib/firmware/esp32s31/s31-lp-core.elf
/etc/init.d/S02s31-lp start
s31-lpctl status
s31-lpctl ping
```

该服务按名称 `esp32s31-lp` 查找 remoteproc，启动它并等待 READY。`status` 应包含 `ready=1`，`ping` 会报告以微秒为单位的往返时间。启动失败时，先查看 `dmesg` 和服务报错，再尝试睡眠。参见 [S02s31-lp](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/overlay/etc/init.d/S02s31-lp)。

## 遵守固件内存预算

当前 ESP-IDF 配置为 LP 固件保留 **8192 字节（8 KiB）**。LP SRAM 地址范围为 `0x2E000000`–`0x2E008000`，但不能将全部 32 KiB 都用于代码、数据和栈：

| 区域 | 地址范围，结束地址不包含在内 | 用途 |
|---|---|---|
| LP 固件分配区 | `0x2E000000`–`0x2E002000` | 当前 8 KiB 构建预算 |
| OpenSBI 挂起快照 | `0x2E002000`–`0x2E007000` | 20 KiB 运行时快照保留区 |
| 睡眠控制保留区 | `0x2E007C00`–`0x2E008000` | 最后 1 KiB；当前结构体占用 112 字节 |

增加代码、数据或栈大小时，应检查 ELF 加载段和链接映射文件。不得扩展进入上述共享保留区。参见[构建分配](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/sdkconfig.defaults)、[OpenSBI 快照](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)及[内存映射](../hw-reference/memory-map.md)。

## 协同修改协议

`shared/s31_lp_protocol.h` 包含 Linux 的 `include/linux/soc/espressif/esp32s31-lp-protocol.h`。LP 在启动时发布 READY，验证请求，并先写入响应字段、再写入响应 CRC。当前 Linux、LP 和 OpenSBI 源码在 ABI 1 与 28 字布局上保持一致。

修改消息码、字段、状态或 CRC 覆盖范围时，应同步更新三个使用者，并从父项目根目录运行现有检查：

```sh
python -m unittest tools.tests.test_s31_feature_contracts.DriverContracts.test_lp_sleep_abi_matches_opensbi tools.tests.test_s31_feature_contracts.DriverContracts.test_lp_mem_timer_starts_after_hp_asleep -v
```

这些检查比较源码约定，不会执行挂起周期。[LP 参考](../api-reference/lp-core/index.md)统一说明传输格式和字段细节；[电源管理](power-management.md)介绍实验性的保持路径与尚需完成的验证。

## 添加 LP 外设

使用新的寄存器窗口前，应在 remoteproc 驱动中添加所需的 LP 外设 PMS 访问权限。现有授权函数会检查已锁定的权限，并回读验证写入的访问位；失败时返回 `-EACCES`。参见[权限配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)。

GPIO 唤醒使用 RTCIO 所有权、电平采样及配置好的 LP GPIO 唤醒中断 / ISR。轮询路径覆盖状态切换窗口；ISR 在 `HP_ASLEEP` 后记录 GPIO 原因并请求 APPWR 唤醒。保留 ARM 时检查非有效电平的逻辑，以及在交还所有权前禁用上下拉、唤醒和输入的清理流程。参见 [GPIO 处理](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c)及 [ARM 配置](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c)。
