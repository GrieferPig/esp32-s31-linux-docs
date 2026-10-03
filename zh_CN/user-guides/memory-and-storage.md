# 内存与存储

在 `esp32-config` 的 **Memory & storage** 中选择 swap，或挂载已有的 SD、USB 存储卷。
以下命令均在开发板上以 root 身份运行。

## 使用 swap 分区

接入已有 swap 分区的存储设备，选择 **Swap settings → Select device and enable**。
菜单只列出带有 swap 签名的设备。选中后立即启用，并保存为启动时使用的设备。

也可以使用命令行：

```sh
esp32-config storage swap enable /dev/sda1
esp32-config storage status
```

将 `/dev/sda1` 替换为实际的 swap 设备。也支持 `UUID=<uuid>`；设备提供 UUID 时，
菜单会保存 UUID，以便设备编号变化后仍能找到它。查看设备名称和当前使用情况：

```sh
cat /proc/partitions
cat /proc/swaps
```

停用配置工具启用的 swap，并取消下次启动时使用：

```sh
esp32-config storage swap disable
```

工具不会停用其他服务管理的 swap。如果 `swapoff` 失败，先关闭应用释放内存，
然后重试；成功后再移除设备。配置工具不会格式化存储设备。

## 挂载 SD 或 USB 存储卷

完整[构建配置](../get-started/build-configuration.md)包含 FAT/VFAT 和内置 ext4。挂载功能仍会核对运行镜像是否提供所需文件系统驱动。
使用 SD 卡前，先启用相应的 SDMMC 接口，并按[使用外设](peripherals.md)连接卡座。

选择 **Removable storage → Select volume and mount**，依次设置：

1. 已有的存储卷。
2. `/mnt` 或 `/media` 下的空目录。
3. 读写或只读访问。
4. 是否开机挂载。

提交后立即挂载。例如，将已有存储卷以读写方式挂载到 `/mnt/media`，并在启动时恢复：

```sh
esp32-config storage configure /dev/sda1 /mnt/media 1 0
```

最后两个参数分别是 `AUTOSTART`（开机挂载）和 `READONLY`（只读），均接受 `0` 或 `1`。
将设备名替换为实际的文件系统分区。工具管理一个可移动存储卷，设备提供 UUID 时会保存 UUID。
启动时设备不在场会跳过挂载；之后接入设备，可选择 **Mount saved volume**，或运行：

```sh
esp32-config storage mount
```

## 卸载或修改启动行为

先关闭文件，并停止正在使用存储卷的应用，再选择 **Safely unmount** 或运行：

```sh
esp32-config storage unmount
```

卸载成功后即可断开该存储卷。拔出整块设备前，检查 `/proc/mounts` 和 `/proc/swaps`，
确认同一设备没有其他使用者。卸载会保留开机挂载设置。若要保留当前挂载，只取消开机挂载：

```sh
esp32-config storage autostart 0
```

选择 **Current usage**，或运行 `esp32-config storage status`，可以查看保存的选择、
当前挂载和 swap 使用情况。配置文件及其保存规则见 [esp32-config](../resources/esp32-config.md)。
