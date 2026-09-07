# Peripheral API Reference

ESP32-S31 peripherals are exposed through standard Linux frameworks. The base
device tree supplies providers and always-present blocks; named overlays select
optional instances, pins, routes, and mutually exclusive modes.

| Function | Linux interface | S31-specific constraint |
|---|---|---|
| GPIO/pinctrl | GPIO character device, pinctrl | Route ownership is checked by overlays |
| UART | TTY/serial | UART0 is normally the console; UART3 has a DMA overlay |
| I2C | `/dev/i2c-*` | I2C0/I2C1; long messages and combined transactions use FIFO continuation |
| GPSPI | SPI controller/target APIs | Exclusive per instance; target DMA up to 4096 bytes, FIFO fallback 64 bytes |
| I2S | ALSA SoC | Configurable DAI framing, TDM slots and MCLK; external machine cards supported |
| TWAI | SocketCAN | Two independently routed controller instances |
| SD/MMC | MMC block layer | Controller, bus width, voltage, and shared pins are overlay policy |
| GMAC | netdev/phylib | External PHY wiring is board-specific |
| USB | gadget/UDC | Device-mode overlay owns the selected USB route |
| GDMA | DMAengine | Internal descriptor SRAM and cache transitions are mandatory |
| GPTimer/SYSTIMER | clocksource/clockevent/counter | System timekeeping resources cannot be reassigned |
| LEDC/MCPWM/SDM | PWM/counter frameworks | Channel and output routes are finite shared resources |
| ADC/DAC/touch/comparator | IIO/input/misc subsystem as implemented | Analog pad ownership conflicts with digital routes |
| TSENS | thermal/hwmon | Uses calibrated SoC sensor behavior |
| Watchdogs | watchdog framework | HP and related watchdog blocks have separate ownership |
| eFuse/RNG/crypto | nvmem, hwrng, crypto API | Security-sensitive state is not duplicated in documentation |

## Overlay activation

Use `s31-overlay` rather than writing directly to configfs. The manager applies
resource claims atomically, validates routes and parameters, records the live
overlay ID, and can restore persistent selections during boot. See the
[overlay catalog](../../resources/overlay-catalog.md) for names and conflicts.

## Driver contract

New drivers must use clock, reset, PM-domain, pinctrl, DMA, IRQ, nvmem, and
reserved-memory providers. Direct writes to a provider-owned register block
are only valid inside that provider. A driver is not considered integrated
until its binding, base node or overlay, Kconfig/Makefile entry, resource
ownership, and userspace ABI are documented.

## Long I2C transactions

The adapter retains its short FIFO path and uses END-detected continuation for
long messages. Each continuation drains/refills at most 32 FIFO bytes while
keeping the bus owned. STOP appears only at the end of the message array;
message boundaries use repeated START, including the extra header for a
10-bit read. The last byte of each read is NACKed. Zero-length writes are
supported; zero-length reads and protocol-mangling flags are rejected.

The adapter accepts the 16-bit message length (up to 65535 bytes), subject to
the caller's own limit: Linux `i2c-dev` limits an individual userspace message
to 8192 bytes. Each hardware batch has a 100 ms timeout. ACK, arbitration and
timeout errors propagate to the caller, with bus recovery where appropriate.
Use a single `I2C_RDWR` call for a combined register write/read. Splitting it
into separate userspace calls changes the wire transaction.

Host tests check command streams, exact addresses/data, repeated START, final
NACK/STOP and error termination. Long transfers still require a physical
target to validate clock stretching, FIFO continuation and recovery timing.

## SPI target transfers

Target overlays now request DMA channels and accept up to 4096 bytes per
transfer with DMA, or 64 bytes with the FIFO fallback. Both directions use
private bounce buffers. RX EOF comes from CS deassertion; unexpected short or
overlength transactions return `-EMSGSIZE`. The target waits interruptibly for
the external host, supports target abort and terminates DMA before reuse.
Once CS completes, DMA completion has a 100 ms bound.

Word sizes are 8, 16 and 32 bits, with lengths aligned to the selected word.
Buffers contain little-endian native words; the target converts MSB-first
16/32-bit words to wire order. LSB-first, CPOL/CPHA and active-high CS are
supported. These changes do not add command/address/dummy phases, dual/quad
target data lanes or a readiness GPIO protocol. The external host must allow
the target to arm each transfer; an unbroken stream of back-to-back CS frames
is not guaranteed. DMA target behavior and electrical timing need board tests.

## Generic I2S and TDM links

The CPU DAI implements `set_fmt`, `set_tdm_slot` and `set_sysclk`. Formats are
I2S, left-justified, DSP A and DSP B; both clocks must be provided by the CPU or
both consumed from the peer. Frame-clock inversion is supported; bit-clock
inversion, mixed provider/consumer roles and external MCLK input return errors.
Sysclk ID 0 with `SND_SOC_CLOCK_OUT` requests an internal MCLK; rate zero selects
automatic MCLK. Divider error is checked before programming a stream.
In clock-consumer mode, the internal module clock must be at least eight
times the external BCLK for clock-domain synchronization. Automatic MCLK
observes this minimum; an explicit lower clock is rejected.
PCM buffers use ALSA's non-coherent DMA allocator and cache synchronization:
Sv32 cannot make a PSRAM buffer uncached through page attributes alone.

TDM accepts 1–16 slots and widths of 8–32 bits. The total frame must contain an
even number of bits. Nonzero TX/RX masks must fit the slot count and select as
many slots as the PCM channel count. Slot width cannot be smaller than the
sample width. Format, slot and MCLK changes are rejected while PCM parameters
are configured; full-duplex streams must agree on the shared MCLK. Use
`hw_free` before reconfiguring. ALSA period size remains 256–4032 bytes.

Without an external card, the existing dummy-codec card and overlay pin
profiles remain available. To connect a codec through a machine driver such
as `simple-audio-card`, add these properties to the selected I2S controller:

```dts
&i2s0 {
    #sound-dai-cells = <0>;
    espressif,external-card;
    status = "okay";
};
```

The machine card supplies its CPU/codec phandles, format, clock roles and TDM
configuration. Choose pin routes for that codec and enable matching clocks and
DMA resources. The driver does not infer external board wiring. Standalone
TX-slave and raw PDM properties remain separate options; this does not add a
PCM-to-PDM converter. Generic-codec and sustained-stream acceptance are pending.
