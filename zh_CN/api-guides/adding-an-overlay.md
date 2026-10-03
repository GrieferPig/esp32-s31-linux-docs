# 添加覆盖层

设备树覆盖层用于启用外设，并选择其引脚和设置。`s31-overlay` 工具可以在 Linux 运行时加载这些描述，也可以保存选择，在下次启动时恢复。

## 1. 创建覆盖层

创建 `esp32s31-overlay-NAME.dtso`，放在 `linux-esp32-s31/arch/riscv/boot/dts/espressif/` 下。
可以从类似设备的现有覆盖层开始修改。
[完整的 I2C0 覆盖层](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2c0.dtso)
包含头部、资源声明、pinctrl 节点和控制器设置。

覆盖层需要设备树插件头部和 `espressif,overlay-name`。
新覆盖层应使用新名称。如果它使用的控制器、DMA 通道或其他资源不能与别的覆盖层共享，
应添加 `espressif,resource-claims`。例如，I2C0 覆盖层的开头如下：

```dts
/dts-v1/;
/plugin/;

/ {
    espressif,overlay-name = "i2c0";
    espressif,resource-claims = "i2c0";
};
```

资源列表是可选的。需要同一独占资源的覆盖层应使用相同的资源声明名称，让管理器能够检测冲突。
对于 pinmux 条目尚未描述的固定引脚，使用 `espressif,gpio-claims` 声明。

## 2. 添加设备和引脚设置

用 `status = "okay"` 启用控制器，并提供其 pinctrl 状态。按需添加时钟、复位、DMA 通道、稳压器、PHY 或子设备。

要允许用户选择 GPIO，在引脚节点上设置 `espressif,route-name` 和 `espressif,route-kind`。
支持的类型为 `matrix-input`、`matrix-output` 和 `matrix-bidirectional`。
如果一个节点有多条分别命名的路由，则使用对应的 `espressif,route-names` 和 `espressif,route-kinds` 列表。

例如，I2C0 覆盖层导出 `i2c0.scl` 和 `i2c0.sda`。用户可以运行 `s31-overlay routes i2c0` 查看它们，并在应用覆盖层时选择引脚。

要开放数值设置，需声明属性名及允许值：

```dts
&i2c0 {
    espressif,param-name = "clock-frequency";
    espressif,param-values = <100000 400000 1000000>;
    clock-frequency = <100000>;
    status = "okay";
};
```

这样，工具就会接受 `clock-frequency=400000`，并拒绝列表之外的值。完整的覆盖层还需要包含控制器的 pinctrl 配置。

## 3. 构建并安装

将覆盖层的 `.dtbo` 目标添加到内核目录下的 `arch/riscv/boot/dts/espressif/Makefile`，
并将 `NAME` 替换为你的覆盖层名称：

```make
dtb-$(CONFIG_ARCH_ESPRESSIF) += esp32s31-overlay-NAME.dtbo
```

然后在主项目中构建并烧录完整匹配镜像集。按[烧录指南](../get-started/flash-and-first-boot.md)
选择端口并准备串口连接：

```sh
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

DTBO 生成在 `out/linux/arch/riscv/boot/dts/espressif/` 中，并安装到根文件系统的 `/usr/lib/s31-overlays`。
开发时直接复制到运行中开发板的文件，是否能在重启后继续使用，需遵循
[部署规则](deploy-files-that-must-survive-reboot)。

## 4. 在开发板上测试

更新镜像后，查看覆盖层设置，并尝试临时应用它。将 `i2c0` 替换为你的覆盖层名称：

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
s31-overlay apply i2c0 --volatile
s31-overlay status
dmesg
```

测试外设，关闭使用它的程序，再移除覆盖层：

```sh
s31-overlay remove i2c0 --volatile
```

还应尝试有冲突的引脚选择和无效参数值。正常流程通过后，省略 `--volatile` 再次应用，并重启检查是否恢复。
测试失败情况时，保存选择和回滚的行为见[使用覆盖层](../resources/overlay-catalog.md)。
