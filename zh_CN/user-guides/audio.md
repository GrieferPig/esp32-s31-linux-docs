# 连接外部 codec 播放音频

在标准的完整开发板镜像上，以 root 身份运行 S31 端的命令。首先完成
[通用引脚与 overlay 检查](peripheral-setup)。
明确标注为构建主机操作的命令应在 Linux 主机上执行。

## 选择时钟关系

随仓库提供的 `i2s0` 和 `i2s1` 覆盖层使用虚拟 codec，在播放和录音**两个方向**
都接收外部 BCLK 和帧时钟。I2S0 的时钟输入为 GPIO42/BCLK 和 GPIO43/WS，
播放数据使用 GPIO44，录音数据使用 GPIO45。产生时钟的 codec 或测试对端
必须在传输前启动匹配的时钟。仓库的[I2S HIL 流程](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/hil/s31_hil.py)
使用 P4 对端提供时钟。只应用默认覆盖层，无法让常见的时钟输入型 DAC 工作。

下面是一个通过 PCM5102A 播放立体声音频的完整**新开发板集成示例**，依据
S31 DAI、simple-card 和 PCM5102A 驱动编写。它不是仓库已提供的 S31 板级
配置，也没有经过 S31 硬件验证。S31 产生 BCLK 和 WS，DAC 接收这两个时钟。
该 codec 不提供录音。

## 连接 PCM5102A

使用已正确供电、数字输入兼容 3.3 V 的模块，与 S31 共地，并按下表连接信号。
将硬件配置设为 I2S 格式（FMT 为低）、SCK 为低以使用 BCK 派生的 PLL、
XSMT 为高以解除静音；DEMP 为低可禁用去加重。供电和其他配置脚应遵循模块
原理图。将线路输出连接到合适的线路输入或放大器。这些要求依据
[TI PCM5102A 数据手册的引脚功能和三线时钟说明](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf)。

| 本示例中的 S31 信号 | PCM5102A 信号 | 时钟/数据角色 |
|---|---|---|
| GPIO42 | BCK | S31 输出，DAC 输入 |
| GPIO43 | LRCK/WS | S31 输出，DAC 输入 |
| GPIO44 | DIN | S31 播放数据输出 |
| 地 | 地 | 公共参考地 |

不连接外部 MCLK。在 48 kHz 下，两个 32 位时隙对应 3.072 MHz 的 BCLK；
`mclk-fs = <256>` 为 S31 内部 MCLK 请求 12.288 MHz。这些是配置值和推导值，
不是测量结果。

## 添加声卡并构建

在构建主机上，将以下选项加入
`linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig`；统一完整配置仍需额外选择此 codec 与声卡驱动。
父仓库的构建流程会根据该源 defconfig 重新生成 `.config`，仅修改
`out/linux/.config` 不会持久生效：

```text
CONFIG_SND_SIMPLE_CARD=y
CONFIG_SND_SOC_PCM5102A=y
```

创建
`linux-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2s0-pcm5102a.dtso`，
内容如下，这是完整的覆盖层：

```dts
/dts-v1/;
/plugin/;

#include <dt-bindings/pinctrl/esp32s31-pinmux.h>

/ {
    espressif,overlay-name = "i2s0-pcm5102a";
    espressif,resource-claims = "i2s0";
};

&ahb_gdma {
    status = "okay";
};

&gpio {
    pcm5102a_pins: pcm5102a-pins {
        i2s-pins {
            pinmux = <ESP32S31_MATRIX_OUT(42, 25, 0)>,
                     <ESP32S31_MATRIX_OUT(43, 27, 0)>,
                     <ESP32S31_MATRIX_OUT(44, 28, 0)>;
            drive-strength = <20>;
        };
    };
};

&i2s0 {
    #sound-dai-cells = <0>;
    espressif,external-card;
    pinctrl-names = "default";
    pinctrl-0 = <&pcm5102a_pins>;
    status = "okay";
};

&{/} {
    pcm5102a: audio-codec {
        compatible = "ti,pcm5102a";
        #sound-dai-cells = <0>;
    };

    sound-pcm5102a {
        compatible = "simple-audio-card";
        simple-audio-card,name = "S31-PCM5102A";
        simple-audio-card,format = "i2s";
        simple-audio-card,bitclock-master = <&pcm5102a_cpu>;
        simple-audio-card,frame-master = <&pcm5102a_cpu>;
        simple-audio-card,mclk-fs = <256>;

        pcm5102a_cpu: simple-audio-card,cpu {
            sound-dai = <&i2s0>;
            dai-tdm-slot-num = <2>;
            dai-tdm-slot-width = <32>;
            system-clock-direction-out;
        };

        simple-audio-card,codec {
            sound-dai = <&pcm5102a>;
        };
    };
};
```

在同一 DTS 目录下的 `Makefile` 中加入这一行：

```make
dtb-$(CONFIG_ARCH_ESPRESSIF) += esp32s31-overlay-i2s0-pcm5102a.dtbo
```

CPU 端点的 `system-clock-direction-out` 不能省略：S31 DAI 的 `set_sysclk()`
只接受 ID 0 和 `SND_SOC_CLOCK_OUT`。声卡中的 master 引用使 CPU 同时产生
BCLK 和 WS，`default` pinctrl 状态将两个时钟路由为输出。
`espressif,external-card` 防止内置虚拟声卡占用 DAI。来源：
[S31 格式和时钟接口](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/espressif/esp32s31-i2s.c)、
[simple-card 时钟方向](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/generic/simple-card-utils.c)、
[PCM5102A 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/codecs/pcm5102a.c)。

在构建主机上重新构建并烧录匹配的内核、无线组件和根文件系统。
按[烧录指南](../get-started/flash-and-first-boot.md)选择端口并准备串口连接：

```sh
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

rootfs 打包步骤会将 `esp32s31-overlay-*.dtbo` 复制到覆盖层目录。在 S31 上
移除已有的 `i2s0` 覆盖层并停止占用冲突引脚的程序后，启用自定义声卡：

```sh
s31-overlay apply i2s0-pcm5102a --volatile
aplay -l
```

使用 `aplay -l` 报告的声卡和设备编号。以下命令假设设备为 `hw:0,0`，并且
`/mnt/media/audio.raw` 已有一份交错立体声、`S16_LE`、48 kHz 的原始音频文件；
请将两者替换为实际值。在此格式下，1008 帧的周期等于 4032 字节，8064 帧的
缓冲区包含八个周期：

```sh
aplay -D hw:0,0 -t raw -f S16_LE -c 2 -r 48000 \
    --period-size=1008 --buffer-size=8064 /mnt/media/audio.raw
s31-overlay remove i2s0-pcm5102a --volatile
```

预期现象是能够列出 PCM 声卡、播放时没有 ALSA 错误，并且 DAC 线路输出端
能够输出所提供的音频。若没有声卡，检查内核选项、覆盖层应用结果及 `dmesg`
中的探测错误。若播放正常但无声，检查输出时钟路由、FMT/XSMT/SCK 配置脚、
供电和放大器路径。测量 BCLK/WS 可验证实际时钟配置。移除声卡前应停止所有
ALSA 使用者。

默认的外部时钟声卡也可接入合适的时钟/数据源进行录音。对于立体声 48 kHz
`S16_LE`，默认声卡使用两个 16 位时隙，需要提供 48 kHz WS、1.536 MHz BCLK
及匹配的 I2S 数据。应用默认 `i2s0` 覆盖层并录制两秒：

```sh
s31-overlay apply i2s0 --volatile
arecord -l
arecord -D hw:0,0 -t raw -f S16_LE -c 2 -r 48000 -d 2 \
    --period-size=1008 --buffer-size=8064 /tmp/capture.raw
s31-overlay remove i2s0 --volatile
```

同样需要将 `hw:0,0` 替换为实际设备。PCM5102A 是播放 DAC，不能提供此录音
数据流。在同一个 S31 DAI 上进行全双工传输时，两个方向必须使用相同的采样率，
并满足共享 MCLK 的兼容性要求。
