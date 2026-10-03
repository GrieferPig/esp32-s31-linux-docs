# 编写应用

应用运行在使用 musl libc 和 BusyBox shell 的精简 Buildroot 环境中，通过 Linux 设备文件、套接字和 sysfs 访问硬件。

## 构建、安装并运行 C 程序

先完成[从源码构建](../../get-started/build-from-source.md)的准备，包括 ESP-IDF。以下主机命令在项目根目录执行。应用打包到 rootfs 后，使用 `make image` 重新发布完整匹配集，再用 `flash-existing-all` 部署；该目标不会构建。详见[构建配置](../../get-started/build-configuration.md)。

在开发电脑上创建 `hello.c`：

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from ESP32-S31 Linux!");
    return 0;
}
```

编译程序，将二进制文件放入开发板的文件系统覆盖目录，然后构建并烧录完整匹配镜像集。将 `/dev/ttyUSB0` 替换为开发板端口，并在烧录前关闭串口监视程序：

```sh
cache/toolchains/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -march=rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs \
  -mabi=ilp32 -mtune=esp-base hello.c -o hello
install -D -m 0755 hello \
  buildroot-external/board/esp32-s31/overlay/usr/bin/hello
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

`flash-existing-all` 从 `dist/current` 验证并烧录全部匹配组件，同时保留同布局的 persist。烧录后重新打开串口，登录并在开发板上运行：

```sh
hello
```

程序会输出 `Hello from ESP32-S31 Linux!`。此流程使用已有的烧录连接；默认镜像没有 SSH 服务器。对于需要反复开发或具有依赖的应用，请使用 [Buildroot 软件包示例](../../api-guides/adding-a-userspace-tool.md)，以免在覆盖目录中手动维护预编译文件。

## 使用 libesp-simd

`libesp-simd` 通过 `esp_simd.h` 提供本移植项目的 XespV 2.2 内存和字符串操作。[库软件包](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/esp-simd/esp-simd.mk)会将头文件和库安装到 `out/buildroot/staging`，并将共享库加入镜像。

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
cache/toolchains/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -march=rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs \
  -mabi=ilp32 -mtune=esp-base -Iout/buildroot/staging/usr/include \
  simd-demo.c -Lout/buildroot/staging/usr/lib -lesp-simd -o simd-demo
install -D -m 0755 simd-demo \
  buildroot-external/board/esp32-s31/overlay/usr/bin/simd-demo
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

在开发板控制台运行 `simd-demo`。初始化成功时，程序会输出 `CPU1: SIMD copy`。

库的构造函数会在 `main()` 前尝试将初始线程绑定到 CPU1。每个调用线程首次使用 SIMD 操作时，也会执行初始化。`esp_simd_init()` 成功时返回零，绑定失败时返回负的 errno 值；初始化失败时，包装函数会使用标量实现。CPU 绑定影响整个调用线程，也包括该线程中的非 SIMD 工作。初始化后，不要将线程移到 CPU0 或扩大其 CPU 亲和性范围：库会缓存初始化成功状态，不会重新检查后续的亲和性改动。原始指令和编译器 ABI 选择见 [ISA 与 ABI](../../hw-reference/isa.md)。

更多示例可查看[库实现](https://github.com/GrieferPig/esp32-s31-linux/blob/main/rootfs/esp_simd.c)和 `rootfs/s31_string_bench.c`。使用此库的 Buildroot 软件包应选择 `BR2_PACKAGE_ESP_SIMD`，将 `esp-simd` 加入软件包依赖，并使用 `-lesp-simd` 链接。

## 访问硬件

完整配置包含原生控制器驱动；启用相应硬件和覆盖层后，才能使用以下接口。

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
