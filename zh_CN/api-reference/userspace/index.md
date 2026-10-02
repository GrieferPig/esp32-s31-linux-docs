# 编写应用

应用运行在使用 musl libc 和 BusyBox shell 的精简 Buildroot 环境中，通过 Linux 设备文件、套接字和 sysfs 访问硬件。

## 构建、安装并运行 C 程序

先完成[从源码构建](../../get-started/build-from-source.md)中的准备工作，包括 ESP-IDF 环境。以下主机命令均在项目根目录运行。以下流程只更新根文件系统，开发板应已运行所选内核配置和构建配置。如需修改其中任何一项，请先按[构建配置](../../get-started/build-profiles.md)更新镜像。构建这些应用时，请在环境中保留相同的配置。

在开发电脑上创建 `hello.c`：

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from ESP32-S31 Linux!");
    return 0;
}
```

编译程序，将二进制文件放入开发板的文件系统覆盖目录，然后构建并烧录更新后的根文件系统。将 `/dev/ttyUSB0` 替换为开发板端口，并在烧录前关闭串口监视程序：

```sh
toolchain/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -mabi=ilp32 hello.c -o hello
install -D -m 0755 hello \
  buildroot-external/board/esp32-s31/overlay/usr/bin/hello
make rootfs
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

[flash-existing-rootfs 目标](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L532-L536)直接写入 `make rootfs` 生成的镜像，不会再次构建。烧录后重新打开串口控制台，登录并在开发板上运行：

```sh
hello
```

程序会输出 `Hello from ESP32-S31 Linux!`。此流程使用已有的烧录连接；默认镜像没有 SSH 服务器。对于需要反复开发或具有依赖的应用，请使用 [Buildroot 软件包示例](../../api-guides/adding-a-userspace-tool.md)，以免在覆盖目录中手动维护预编译文件。

## 使用 libesp-simd

`libesp-simd` 通过 `esp_simd.h` 提供本移植项目的 XespV 2.2 内存和字符串操作。[库软件包](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/package/esp-simd/esp-simd.mk#L26-L42)会将头文件和库安装到 `build/buildroot/staging`，并将共享库加入镜像。

在主机上创建 `simd-demo.c`：

```c
#include <stdio.h>
#include <string.h>
#include <esp_simd.h>

int main(void)
{
    const char message[] = "SIMD copy";
    char copy[sizeof(message)];
    int rc = esp_simd_init();

    if (rc) {
        fprintf(stderr, "esp_simd_init: %s\n", strerror(-rc));
        return 1;
    }
    esp_simd_memcpy(copy, message, sizeof(message));
    printf("CPU%d: %s\n", esp_simd_cpu(), copy);
    return strcmp(copy, message) != 0;
}
```

成功运行 `make rootfs` 后，编译并安装：

```sh
toolchain/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -mabi=ilp32 -Ibuild/buildroot/staging/usr/include \
  simd-demo.c -Lbuild/buildroot/staging/usr/lib -lesp-simd -o simd-demo
install -D -m 0755 simd-demo \
  buildroot-external/board/esp32-s31/overlay/usr/bin/simd-demo
make rootfs
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

在开发板控制台运行 `simd-demo`。初始化成功时，程序会输出 `CPU1: SIMD copy`。

库的构造函数会在 `main()` 前尝试将初始线程绑定到 CPU1。每个调用线程首次使用 SIMD 操作时，也会执行初始化。`esp_simd_init()` 成功时返回零，绑定失败时返回负的 errno 值；初始化失败时，包装函数会使用标量实现。CPU 绑定影响整个调用线程，也包括该线程中的非 SIMD 工作。初始化后，不要将线程移到 CPU0 或扩大其 CPU 亲和性范围：库会缓存初始化成功状态，不会重新检查后续的亲和性改动。原始指令和编译器 ABI 选择见 [ISA 与 ABI](../../hw-reference/isa.md)。

更多示例可查看[库实现](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/rootfs/esp_simd.c)和 `rootfs/s31_string_bench.c`。使用此库的 Buildroot 软件包应选择 `BR2_PACKAGE_ESP_SIMD`，将 `esp-simd` 加入软件包依赖，并使用 `-lesp-simd` 链接。

## 访问硬件

启用相应内核驱动和硬件后，才能使用以下接口。精简配置不包含部分可选外设驱动。

| 硬件 | 应用接口 |
|---|---|
| UART | TTY 和 termios |
| GPIO | GPIO 字符设备和 libgpiod |
| I2C | `/dev/i2c-*` |
| SPI | `/dev/spidev*` |
| 音频 | ALSA PCM |
| CAN | SocketCAN |
| Wi-Fi 和以太网 | 网络套接字 |
| 模拟输入和输出 | IIO |
| 看门狗 | Linux 看门狗设备 |
| LP 核心 | `s31-lpctl` 和 `/dev/s31-lp` |
| 蓝牙，默认配置 | BTstack 和 `/dev/s31-hci` |

打开可选外设前，先启用对应的[覆盖层](../../resources/overlay-catalog.md)。[外设参考](../peripherals/index.md)中提供了命令行示例。

## 文件、设置和其他工具

持久化与临时存储见[配置](../../resources/configuration.md)。软件包自带文件的部署例外见[添加用户空间工具](deploy-files-that-must-survive-reboot)。[命令参考](../../resources/cli-reference.md)介绍了镜像中的开发板配置、覆盖层、LP 和测试工具。
