# 添加用户空间工具

使用 Buildroot 外部树将应用加入镜像。[编写应用](../api-reference/userspace/index.md)提供了首个 C 程序及构建到开发板运行的示例。除明确标为开发板命令的部分外，本页命令均在主项目根目录运行。

## 添加 shell 脚本

将用户命令放在 `buildroot-external/board/esp32-s31/overlay/usr/bin/`；管理命令使用 `usr/sbin/`。在脚本开头指定解释器，例如 `#!/bin/sh`，并赋予执行权限。Buildroot 在构建根文件系统时，会将此文件系统覆盖目录复制到镜像中。

## 添加 Buildroot 软件包

本示例添加一个小型 `s31-hello` 程序，使用与 [s31-tools](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/package/s31-tools/s31-tools.mk) 相同的本地源码软件包机制。

### 1. 添加源码

创建 `rootfs/s31-hello/hello.c`：

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from the s31-hello package!");
    return 0;
}
```

### 2. 添加软件包定义

创建 `buildroot-external/package/s31-hello/Config.in`：

```kconfig
config BR2_PACKAGE_S31_HELLO
    bool "s31-hello"
    help
      Small example application for ESP32-S31 Linux.
```

创建 `buildroot-external/package/s31-hello/s31-hello.mk`。`define` 块中的命令行以制表符开头：

```make
S31_HELLO_VERSION = 1.0
S31_HELLO_SITE = $(BR2_EXTERNAL_ESP32_S31_PATH)/../rootfs/s31-hello
S31_HELLO_SITE_METHOD = local

define S31_HELLO_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_LDFLAGS) \
		$(@D)/hello.c -o $(@D)/s31-hello
endef

define S31_HELLO_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/s31-hello \
		$(TARGET_DIR)/usr/bin/s31-hello
endef

$(eval $(generic-package))
```

在 `buildroot-external/Config.in` 的现有菜单中添加以下一行：

```kconfig
source "$BR2_EXTERNAL_ESP32_S31_PATH/package/s31-hello/Config.in"
```

`buildroot-external/external.mk` 已包含 `package/*/*.mk`，会自动找到新 Makefile。对于较大的应用，还需添加构建依赖，以及相应的 Kconfig 依赖或选择项。准备分发时，在软件包元数据中填写实际许可证及许可证文件。`s31-tools` 和 `esp-simd` 可用作本地示例。

### 3. 选择并保存软件包

打开 Buildroot 菜单：

```sh
make buildroot-menuconfig
```

在外部 ESP32-S31 软件包菜单中找到并启用 `s31-hello`。保存配置并退出，然后使用 [Buildroot 的 savedefconfig 目标](https://github.com/buildroot/buildroot/blob/cb857ba4c87a93e5265a9e4a3f32071abf39e14a/Makefile#L1064-L1068) 将选择写回源码中的 defconfig：

```sh
make -C buildroot O="$PWD/build/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" \
  savedefconfig \
  DEFCONFIG="$PWD/buildroot-external/configs/esp32s31_rootfs_defconfig"
```

请在再次运行 `make rootfs` 前完成这一步：主项目构建会重新加载 `esp32s31_rootfs_defconfig`，覆盖仅存在于输出目录中的配置改动。源码 defconfig 中此时应包含 `BR2_PACKAGE_S31_HELLO=y`。

### 4. 构建、烧录并运行

以下命令只更新根文件系统。开发板应已运行所选内核配置和[构建配置](../get-started/build-profiles.md)；如需修改其中任何一项，请先按该指南更新镜像。执行以下命令时保持相同的配置。激活 ESP-IDF 环境后，在主机上运行：

```sh
make rootfs
ls -l build/buildroot/target/usr/bin/s31-hello
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

将 `/dev/ttyUSB0` 替换为开发板端口，并在烧录前关闭串口监视程序。重启后，通过串口控制台登录，在开发板上运行：

```sh
s31-hello
```

程序会输出 `Hello from the s31-hello package!`。此流程不需要开发板安装 SSH 服务器。

### 5. 修改本地源码后重新构建

主项目 Makefile 会显式重新构建已有的本地工具软件包，但新软件包不在该列表中。修改 `rootfs/s31-hello/hello.c` 后，先移除该软件包的构建目录，再重新生成镜像：

```sh
make -C buildroot O="$PWD/build/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" s31-hello-dirclean
make rootfs
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

这样 Buildroot 会重新复制并编译更新后的本地源码。烧录后，再次在开发板上运行程序。

(runtime-pruning)=
## 在镜像中保留应用及其依赖

[构建后处理脚本](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/post-build.sh)会在软件包安装后精简部分程序和共享库。运行 `make rootfs` 后，检查 `build/buildroot/target`，包括程序依赖的库。软件包构建成功，并不代表运行所需文件仍保留在镜像中。

例如，脚本会移除 `libstdc++`、`libatomic`、BlueZ 工具和守护进程，以及 D-Bus/GLib/BlueALSA 文件。因此，添加 C++ 应用或基于 BlueZ 的系统时，也需检查相关移除规则。当前脚本还要求 `s31-btstack-a2dp` 和 `s31-ext-test` 保持可执行；替换 BTstack 时，需同时修改该检查和服务启动流程。主项目构建会检查最终根文件系统是否超出 Flash 分区。

(deploy-files-that-must-survive-reboot)=
## 部署重启后需要保留的文件

一般的持久化行为见[配置](../resources/configuration.md)。上传文件以替换软件包自带文件时，需要注意两条启动清理规则。挂载可写根文件系统层之前，[init 脚本](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/overlay/init#L84-L107)会删除以下路径的可写副本：

```text
/usr/sbin/s31-btstack-a2dp
/etc/init.d/S40btstack
/etc/init.d/S40bluetoothd
/etc/init.d/S42s31-a2dp
/usr/sbin/bluetoothd
/usr/bin/bluealsa
/usr/sbin/s31-bt-agent
/etc/bluetooth/main.conf
```

它还会删除当前根文件系统在 `/usr/lib/s31-overlays` 中自带的同名 `.dtbo` 文件的可写副本。上传到这些路径的替换文件可能在当前会话中有效，但下次启动时会消失。要保留这些软件包文件的改动，请重新构建并烧录根文件系统。临时实验可使用单独的文件名，并显式调用。配对密钥和 `/etc/esp32-conf` 不受这些清理规则影响。
