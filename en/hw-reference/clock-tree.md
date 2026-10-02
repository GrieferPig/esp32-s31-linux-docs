# Clock tree

The Linux clock provider exposes roots, selected parent relationships, dividers
and peripheral controls through the common clock framework (CCF). The tables
below describe this provider's registrations and rate calculations.

## Registered parents and dividers

| Clock | Registered parent(s) | Rate relationship in the provider |
|---|---|---|
| `xtal` | None | Crystal frequency read from configuration; 40 MHz fallback |
| `rc-fast`, `rc-slow`, `xtal32k` | None | Fixed model rates: 17.5 MHz, 136 kHz, 32.768 kHz |
| `cpll`, `mpll`, `apll` | `xtal` | PLL rate calculated from divider registers; APLL includes its fractional setting |
| `bbpll` | `xtal` | Fixed model rate of 480 MHz |
| `pll-f20`, `pll-f60`, `pll-f80`, `pll-f120`, `pll-f160`, `pll-f240` | `bbpll` | Parent rate divided by the programmed divider |
| `pll-f25` | `mpll` | Parent rate divided by the programmed divider |
| `pll-f50` | `cpll` or `mpll` | Selected parent divided by the programmed divider |
| `xtal-d2` | `xtal` | Fixed model rate of 20 MHz |
| `cpu` | `xtal`, `cpll`, `rc-fast` or `pll-f240` | Selected parent divided by the CPU divider |
| `mem` | `cpu` | CPU rate divided by 1 or 2 |
| `sys` | `cpu` | CPU rate divided by the system divider |
| `apb` | `sys` | System rate divided by the APB divider |
| `emac-rgmii-txc` | `mpll` | Programmable transmit-clock divider |

See the [registered parents](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1382-L1390),
[clock registrations](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1485-L1632), and
[rate calculations](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L910-L962).
Peripheral clock entries are often registered separately with a fixed or
initial bus rate, without a CCF parent edge.

## CPU operating points

Both HP cores use the same `cpu` clock and a shared OPP table. The supplied
device tree exposes 80, 160, 240 and 320 MHz. The clock driver programs these
source/divider combinations; `mem` and `sys` divide the CPU clock, and `apb`
divides `sys`:

| CPU rate | Source | CPU divider | Memory divider | System divider | APB divider |
|---|---|---:|---:|---:|---:|
| 80 MHz | `cpll` | 4 | 1 | 1 | 2 |
| 160 MHz | `cpll` | 2 | 1 | 2 | 2 |
| 240 MHz | `pll-f240` | 1 | 2 | 3 | 2 |
| 320 MHz | `cpll` | 1 | 2 | 3 | 2 |

The driver also has a 40 MHz XTAL configuration for the power-off handoff; it
is not an OPP exposed by the supplied CPU table. Source/mux and divider updates
are latched together. See the [divider table and update sequence](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L982-L1060)
and [shared OPPs](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L103-L125).
For frequency controls, see [Power management](../api-guides/power-management.md).

## Timer and peripheral inputs

| Provider entry / timer | Rate used by this port | Consumer |
|---|---|---|
| `systimer` | 16 MHz | Linux timekeeping and per-CPU events |
| Timer 1 in each timer group | 40 MHz XTAL / 40 = 1 MHz | OpenSBI idle-wakeup guard; reserved from the Linux GPTimer driver |
| `uart0`–`uart3`, `i2c0`, `i2c1`, `ledc0`, `ledc1` | 40 MHz provider input | Peripheral drivers apply their own baud, bus or output dividers |
| `gpspi2`, `gpspi3` | 80 MHz provider input | SPI transfer-clock divider |

The peripheral input rates are not the resulting UART baud rate, I2C/SPI bus
speed or PWM frequency. See [peripheral registrations](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1635-L1747)
and the [reserved interrupt routes](interrupt-routing.md).

Driver acquisition and the `clocks` diagnostic attribute are documented once
in [Clocks, resets, and power](../api-reference/system/clock-reset-power.md).
