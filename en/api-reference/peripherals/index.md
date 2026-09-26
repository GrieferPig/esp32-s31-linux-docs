# Peripherals

The port exposes peripherals through standard Linux interfaces, including
TTY, I2C, SPI, ALSA, and SocketCAN. Use a device-tree overlay to enable an
optional controller and select its pins.

> Build the [full-peripheral profile](../../get-started/build-profiles.md) for
I2C, SPI, I2S, Ethernet, SD/MMC, and the other optional drivers in this chapter.

## Enable a peripheral

For example, to enable I2C0:

```sh
s31-overlay apply i2c0
```

The selection is saved and restored at boot. Add `--volatile` for a temporary
setup. To inspect the pins and available settings, run:

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
```

Check the board schematic before connecting a device. The
[overlay catalog](../../resources/overlay-catalog.md) lists the available
controllers and their configuration options.

## Interfaces

| Peripheral | Linux interface | Overlay or setup |
|---|---|---|
| GPIO | GPIO character device; `gpioinfo`, `gpioget`, `gpioset` | Select free pins on the board |
| UART | `/dev/ttyS*` | `uart1`, `uart2`, `uart3`, or `uart3-dma` |
| I2C | `/dev/i2c-*` | `i2c0` or `i2c1` |
| SPI | SPI subsystem; `/dev/spidev*` for userspace clients | `gpspi2`, `gpspi3`, or their target variants |
| I2S/TDM | ALSA PCM | `i2s0` or `i2s1` |
| TWAI/CAN | SocketCAN | `twai0` or `twai1`; external transceiver |
| SD/MMC | MMC block devices | `sdmmc0`, `sdmmc1`, `sdmmc-dual`, or `sdmmc-uhs` |
| Ethernet | Network interface and PHY driver | `gmac`; external PHY |
| USB | DWC2 host or USB gadget | Host setup or `usb-device` |
| GDMA | Kernel DMAengine API | AHB/AXI provider selected by the client |
| General-purpose timers | Counter framework | `timers` |
| LEDC, MCPWM, SDM, and pulse counter | PWM and Counter frameworks | `pwm-counter` |
| ADC, DAC, touch, comparator | IIO, input, or device-specific interface | `analog` and suitable analog pins |
| Temperature sensor | Thermal/hwmon | Sensor driver |
| Watchdogs | Watchdog framework | `watchdogs` |
| eFuse, random numbers, crypto | NVMEM, hwrng, and kernel crypto APIs | Corresponding kernel drivers |

UART0 is the serial console. UART3's DMA overlay also uses UHCI0 and an AHB
GDMA channel. For the current feature status, see the
[support matrix](../../resources/support-matrix.md).

## I2C

Both I2C controllers support 7-bit and 10-bit addresses and combined
write/read transactions. The default bus speed is 100 kHz. To select 400 kHz
and route I2C0 to GPIO35 and GPIO36:

```sh
s31-overlay apply i2c0 i2c0.scl=35 i2c0.sda=36 clock-frequency=400000
```

Use suitable pull-up resistors on SCL and SDA. The overlay also accepts
100000 and 1000000 Hz.

List the adapters with:

```sh
i2cdetect -l
```

For a device at address `0x51` on adapter 0, a one-byte register selection
followed by a one-byte read can be sent as one transaction:

```sh
i2ctransfer -y 0 w1@0x51 0x00 r1
```

Replace the adapter, address, and register with those for your device. In C,
use `I2C_RDWR` for this combined operation so the write and read are separated
by a repeated START.

### Transfer limits and errors

Userspace `I2C_RDWR` messages can contain up to 8192 bytes each. Kernel clients
use a 16-bit message length, allowing up to 65535 bytes. Zero-length writes
are accepted; zero-length reads and protocol-mangling flags are unsupported.

Long transfers are split into batches of up to 32 TX bytes or 31 RX bytes.
The controller holds the bus between batches and sends STOP after the final
message. Each batch has a 500 ms completion timeout.

| Error | Meaning |
|---|---|
| `ENXIO` | The target did not acknowledge |
| `EAGAIN` | Arbitration was lost |
| `ETIMEDOUT` | Hardware or completion timeout |
| `EIO` | Unexpected receive FIFO count |

The driver includes bus recovery. Repeated timeouts should also be checked
against the pull-ups, wiring, bus speed, and target behavior.

## SPI

GPSPI2 and GPSPI3 can operate as a host or as a target. Choose the matching
overlay for the instance and role, for example `gpspi2` or `gpspi2-target`.

Host clients use the Linux SPI API. Applications using spidev select their
mode, clock rate, word size, and transfer buffers through its ioctls.

### Target transfers

Target mode waits for an external host to supply the clock and chip select.
It supports modes 0–3, active-high chip select, and 8-, 16-, or 32-bit words.
The transfer length must be a whole number of words.

| Setting | Limit |
|---|---|
| Transfer with DMA | 4096 bytes |
| FIFO-only transfer | 64 bytes |
| Wait for the external host | Interruptible; no fixed timeout |
| DMA completion after the transaction | 100 ms for each required direction |

The target converts little-endian Linux words to the selected wire byte order.
For 16- and 32-bit MSB-first transfers, bytes within each word are reversed on
transmit and converted back on receive.

Allow time for the target to arm each transfer before asserting chip select.
Applications needing a ready signal should implement that handshake separately.
Target mode uses a single data lane and has no separate command, address, or
dummy phases.

An interrupted or aborted wait returns `EINTR`. An unexpected transaction
length returns `EMSGSIZE`, and a DMA completion timeout returns `ETIMEDOUT`.

## I2S and TDM

I2S0 and I2S1 use ALSA SoC with GDMA-backed playback and capture. After enabling
the appropriate overlay, list the PCM devices:

```sh
aplay -l
arecord -l
```

Use the card and device numbers from that output in your application. The
board needs an appropriate digital-audio connection, such as an I2S DAC,
codec, or test peer.

### PCM settings

| Setting | Values |
|---|---|
| Sample formats | `S8`, `S16_LE`, `S24_LE`, `S32_LE` |
| Sample rates | 8–192 kHz, subject to clock and card configuration |
| Channels | 1–16 |
| Period size | 256–4032 bytes |
| Periods per buffer | 2–8 |

Playback and capture share MCLK. Configure both streams with compatible clock
settings. ALSA handles cache synchronization for the non-coherent DMA buffers.

### Framing and clocks

The CPU DAI supports I2S, left-justified, DSP A, and DSP B framing. It can
provide both BCLK and frame clock, or consume both from the other device.
Frame-clock inversion is supported. Mixed clock roles, bit-clock inversion,
and an external MCLK input are currently unsupported.

`set_sysclk()` uses ID 0 and `SND_SOC_CLOCK_OUT` for internal MCLK. A rate of
zero selects MCLK automatically. When consuming external BCLK, the internal
module clock must run at least eight times faster than BCLK.

### TDM slots

Use `set_tdm_slot()` to select 1–16 slots, each 8–32 bits wide. The slot width
must fit the sample, and the total number of bits in a frame must be even.
Nonzero TX/RX masks select the active slots and must contain one bit for each
PCM channel. Passing zero slots with zero masks clears the explicit slot setup.

Release the configured stream before changing its format, slots, or MCLK.
Reapplying an identical setting is allowed.

### Connect an external codec

Use an ASoC machine driver, such as `simple-audio-card`, for a board with an
external codec. Add the following properties to the selected controller:

```dts
&i2s0 {
    #sound-dai-cells = <0>;
    espressif,external-card;
    status = "okay";
};
```

Then describe the CPU/codec link, pins, framing, clocks, and any TDM settings
in the machine card. `espressif,external-card` disables the built-in dummy
card so the external card can use the controller. The built-in overlay keeps
its separate playback and capture clock roles.

Raw PDM options are also present in the driver; PCM-to-PDM conversion is not
provided by these options.

## Storage, networking, and other peripherals

Use the MMC block layer for SD cards, SocketCAN for TWAI, and the normal Linux
network interfaces for Ethernet. Their overlays select the controller and
pins; the carrier board supplies the socket, transceiver, or PHY.

USB host supports attached devices such as storage. The `usb-device` overlay
switches the controller to gadget mode. Unmount USB filesystems and disable
USB-backed swap before switching roles.

Timing and analog devices use their Linux subsystem interfaces. In the
`timers` overlay, timer 0 of each group is available to applications; timer 1
is reserved for CPU idle wakeups. Analog and digital routes can share physical
pads, so choose one function for each pin.

Driver sources are under `linux-esp32-s31/drivers/`, with audio under
`sound/soc/espressif/`. See [Adding a driver](../../api-guides/adding-a-driver.md)
for integration steps.
