# Audio with an external codec

Run the S31 commands as root on the standard full board image. Complete the
[common pin and overlay checks](peripheral-setup) first.
Commands explicitly marked for the build host run on the Linux host.

## Choose the clock arrangement

The shipped `i2s0` and `i2s1` overlays use a dummy codec and consume external
BCLK and frame clock for **both** playback and capture. For I2S0 these inputs
are GPIO42/BCLK and GPIO43/WS, with playback data on GPIO44 and capture data
on GPIO45. A clock-producing codec or test peer must start the matching clocks
before the transfer. The repository's [I2S HIL flow](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/hil/s31_hil.py)
uses a P4 peer for this purpose. Applying the stock overlay does not make an
ordinary clock-consuming DAC work.

The following is a complete **new board-integration example** for stereo
playback through a PCM5102A. It is derived from the S31 DAI, simple-card and
PCM5102A drivers; it is not a shipped or hardware-validated S31 board configuration.
The S31 produces BCLK and WS; the DAC consumes both. Capture is not provided
by this codec.

## Wire the PCM5102A

Use a powered module with 3.3 V-compatible digital inputs, common ground,
and the following signal connections. Set its hardware straps to I2S format
(FMT low), SCK low for BCK-derived PLL operation, and XSMT high to unmute;
DEMP low disables de-emphasis. Follow the module schematic for supplies and
other straps. Connect its line outputs to a suitable line input or amplifier.
These requirements come from the
[TI PCM5102A datasheet, pin functions and 3-wire clocking](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf).

| S31 signal in this example | PCM5102A signal | Clock/data role |
|---|---|---|
| GPIO42 | BCK | S31 output, DAC input |
| GPIO43 | LRCK/WS | S31 output, DAC input |
| GPIO44 | DIN | S31 playback data output |
| Ground | Ground | Common reference |

No external MCLK connection is used. At 48 kHz, two 32-bit slots give a
3.072 MHz BCLK; `mclk-fs = <256>` requests 12.288 MHz for the S31's internal
MCLK. These are configured/derived values, not measured frequencies.

## Add the card and build it

On the build host, add these options to
`linux-esp32-s31/arch/riscv/configs/esp32s31_defconfig` and use the full board configuration.
The parent build recreates its generated `.config` from this source defconfig,
so editing only `out/linux/.config` is insufficient:

```text
CONFIG_SND_SIMPLE_CARD=y
CONFIG_SND_SOC_PCM5102A=y
```

Create
`linux-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31-overlay-i2s0-pcm5102a.dtso`
with this complete overlay:

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

Add this line to the `Makefile` in the same DTS directory:

```make
dtb-$(CONFIG_ARCH_ESPRESSIF) += esp32s31-overlay-i2s0-pcm5102a.dtbo
```

The CPU endpoint's `system-clock-direction-out` matters: the S31 DAI accepts
`set_sysclk()` only with ID 0 and `SND_SOC_CLOCK_OUT`. The card's master
references make the CPU produce both BCLK and WS. The `default` pinctrl state
routes both clocks as outputs. `espressif,external-card` prevents the built-in
dummy card from claiming the DAI. Sources:
[S31 format and clock interface](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/espressif/esp32s31-i2s.c),
[simple-card clock direction](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/generic/simple-card-utils.c),
[PCM5102A driver](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/codecs/pcm5102a.c).

On the build host, rebuild and flash the matching kernel, radio bundle and
rootfs. Follow the [flash guide](../get-started/flash-and-first-boot.md) to
select the port and prepare the serial connection:

```sh
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

The rootfs packaging copies `esp32s31-overlay-*.dtbo` into its overlay
directory. On the S31, with any existing `i2s0` overlay and conflicting pin
users removed, enable the custom card:

```sh
s31-overlay apply i2s0-pcm5102a --volatile
aplay -l
```

Use the card/device numbers reported by `aplay -l`. The following assumes
`hw:0,0` and an existing raw interleaved stereo `S16_LE`, 48 kHz file at
`/mnt/media/audio.raw`; replace both with your actual values. In this format,
a 1008-frame period is 4032 bytes, and 8064 frames gives eight periods:

```sh
aplay -D hw:0,0 -t raw -f S16_LE -c 2 -r 48000 \
    --period-size=1008 --buffer-size=8064 /mnt/media/audio.raw
s31-overlay remove i2s0-pcm5102a --volatile
```

Expected observations are a PCM card listing, successful playback without
ALSA errors, and the supplied audio at the DAC's line output. If the card is
missing, check kernel options, overlay application, and probe errors in
`dmesg`. If playback runs but is silent, check the output clock routes,
FMT/XSMT/SCK straps, supplies, and amplifier path. Measure BCLK/WS to verify
the physical clock configuration. Stop all ALSA users before removing the card.

The stock external-clock card can also be used for capture with a suitable
clock/data source. For stereo 48 kHz `S16_LE`, the stock card uses two
16-bit slots: supply 48 kHz WS and 1.536 MHz BCLK with the matching I2S data.
Apply the stock `i2s0` overlay and record two seconds:

```sh
s31-overlay apply i2s0 --volatile
arecord -l
arecord -D hw:0,0 -t raw -f S16_LE -c 2 -r 48000 -d 2 \
    --period-size=1008 --buffer-size=8064 /tmp/capture.raw
s31-overlay remove i2s0 --volatile
```

Again, replace `hw:0,0` with the actual device. The PCM5102A is a playback
DAC and cannot supply this capture stream. Duplex use on one S31 DAI requires
the same sample rate and compatible shared MCLK settings.
