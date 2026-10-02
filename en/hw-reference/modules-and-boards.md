# Modules and boards

The port targets ESP32-S31 platforms. The [maintainer's board report](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/README.md#L1-L5)
lists these boards and module:

- Espressif ESP32-S31 Coreboard
- Espressif ESP32-S31 Korvo
- Espressif ESP32-S31-WROOM-3 E1H16R16V module

Use the carrier's schematic to identify the connector, power input, and
download/reset buttons. The pin tables below use SoC GPIO numbers. Match them
to your board's header labels before wiring.

## Connect the console

The default console uses UART0 at 115200 baud, 8N1. Connect through the board's
USB-UART console connection. The S31 transmits on GPIO58 and receives on GPIO59.

The base configuration reserves these pins:

| GPIO | Use in the base configuration |
|---|---|
| 26–32 | Reserved as the live flash/XIP pin group |
| 33, 34 | USB Serial/JTAG |
| 41 | Excluded by the GPIO driver and overlay tools |
| 58 | UART0 TX, console output |
| 59 | UART0 RX, console input |

These reservations come from the [base GPIO configuration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L375-L403)
and [overlay pin checks](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/rootfs/s31_overlay.c#L63-L69).
GPIO29 is also excluded by the GPIO driver's valid-pin mask; it is already
inside the reserved 26–32 group.

## Connect a peripheral

The following defaults apply when you enable the named
[shipped overlay](https://github.com/GrieferPig/linux-esp32-s31/tree/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif)
without pin overrides. Optional controllers also need their drivers in the
[full-peripheral profile](../get-started/build-profiles.md).

### Matrix-routed signals

| Overlay | Default signals and GPIOs | Connection notes |
|---|---|---|
| `uart1` | TX 42, RX 43 | Connect TX to the peer's RX and RX to its TX |
| `uart2` | TX 44, RX 45 | Separate pins from the default `uart1` route |
| `uart3`, `uart3-dma` | No external pin route supplied | The HIL runner uses internal loopback for these overlays |
| `i2c0` | SCL 35, SDA 36 | Check the peripheral's pull-up requirements |
| `i2c1` | SCL 44, SDA 45 | Shares its defaults with `uart2` |
| `gpspi2`, `gpspi3` | SCLK 42, MOSI 43, MISO 45, active-low CS 44 | Host mode; both overlays use the same default GPIOs |
| `gpspi2-target` | SCLK 43, MOSI 40, MISO 42, CS0 44 | The external host drives SCLK, MOSI, and CS0 |
| `gpspi3-target` | SCLK 46, MOSI 40, MISO 42, CS0 47 | The external host drives SCLK, MOSI, and CS0 |
| `i2s0`, `i2s1` | BCLK input 42, WS input 43, data output 44, data input 45 | Both playback and capture consume external clocks in the supplied overlays |
| `twai0` | TX 46, RX 47 | Connect through a suitable CAN transceiver |
| `twai1` | TX 48, RX 49 | Connect through a suitable CAN transceiver |

Inspect the defaults packaged with your image before wiring:

```sh
s31-overlay routes i2c0
```

If you supplied pin assignments when applying an overlay, wire to those
assignments. Several overlays share default GPIOs, so select nonconflicting
pins before enabling them together. The overlay manager checks GPIO and
resource conflicts. See the [overlay catalog](../resources/overlay-catalog.md)
for route names and command syntax.

### Fixed pin groups

| Overlay | GPIO group | Use |
|---|---|---|
| `sdmmc0`, `sdmmc-uhs` | CLK 24; CMD 25; DAT0–DAT3: 20, 21, 22, 23 | Slot 0, four data lines by default |
| `sdmmc1` | CLK 39; CMD 40; DAT0–DAT3: 35, 36, 37, 38 | Slot 1, four data lines by default |
| `sdmmc-dual` | Both SDMMC groups above | Both slots |
| `gmac` | Management interface 5–6; PHY reset 7; RGMII transmit group 8–13; receive group 14–19 | See the [Ethernet signal table](ethernet-default-pins); requires a PHY and matching board wiring |
| `analog` | DAC 4–5; touch 6–19; comparator 37–40; ADC 42–57 | The overlay claims the whole group, even if the application uses one function |

The SDMMC and Ethernet signal groups are defined in the
[base pinctrl configuration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L620-L793).
The individual SDMMC signals match the pinned
[ESP-IDF slot definitions](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/components/esp_hal_sd/esp32s31/include/soc/sdmmc_pins.h#L9-L23).
The stock `analog` overlay conflicts with several bus defaults;
use a smaller custom overlay when you need only part of that group.

(ethernet-default-pins)=

### Ethernet signals

The default `gmac` route uses these SoC GPIOs. Match each signal to the PHY
connection on your carrier schematic.

| Signal | Default GPIO(s) | Direction at S31 |
|---|---|---|
| MDC | 5 | Output |
| MDIO | 6 | Bidirectional |
| PHY reset | 7 | Active-low output |
| TXD0, TXD1, TXD2, TXD3 | 8, 9, 10, 11 | Output |
| TX_CTL | 12 | Output |
| TXC | 13 | Output |
| RXC | 14 | Input |
| RX_CTL | 15 | Input |
| RXD0, RXD1, RXD2, RXD3 | 19, 18, 17, 16 | Input |

RXD0–RXD3 run in descending GPIO order. The signal names and clock directions
follow the pinned [ESP-IDF RGMII mapping](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/components/esp_hal_emac/esp32s31/emac_periph.c#L190-L401);
the Linux tree supplies the route above and
[PHY reset configuration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L866-L875).

### PWM and counter defaults

The `pwm-counter` overlay enables these routes together:

| Signals | Default GPIOs |
|---|---|
| `ledc0.out`, `ledc1.out` | 20, 21 |
| `mcpwm0.out`, `mcpwm1.out`, `mcpwm2.out`, `mcpwm3.out` | 42, 23, 24, 25 |
| `mcpwm0.capture0`, `mcpwm0.fault0`, `mcpwm0.sync0` | 40, 39, 38 |
| `sdm.out`, `pcnt0.in`, `pcnt1.in` | 35, 36, 37 |

The assignments and GPIO claims are in the
[`pwm-counter` overlay](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31-overlay-pwm-counter.dtso#L7-L135).

Connect a common ground and check the peripheral's voltage requirements,
pull-ups, transceiver, codec, or PHY before applying an overlay. For setup
examples, see [Using peripherals](../user-guides/peripherals.md).

## Use another memory configuration

The supplied images use a fixed 16 MiB flash layout and a 16 MiB PSRAM mapping.
Supporting a different capacity requires changes to the boot configuration,
device tree, and image layout before flashing.

See [Flash layout](flash-layout.md) and [Memory map](memory-map.md).
