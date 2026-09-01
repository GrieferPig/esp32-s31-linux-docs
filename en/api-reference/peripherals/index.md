# Peripherals

## Runtime overlay manager

The base device tree contains only core devices that do not conflict. Variable
peripherals are enabled at runtime by applying DTBOs through
`/dev/s31-overlay`. Multiple non-conflicting overlays may remain active at the
same time.

Before applying an overlay, the manager checks:

- physical GPIO ownership;
- GPIO-matrix input-signal ownership;
- exclusive resources such as SDMMC hosts;
- shared INTMTX sources; and
- dedicated IO-MUX selections.

A conflict returns `EBUSY` and leaves the current instance unchanged. When an
active overlay is replaced, the manager temporarily removes the old instance.
If the new instance fails, the old instance is restored atomically. After a
device is unbound, pinctrl returns its pads to a high-impedance safe state and
releases matrix and dedicated-pinmux ownership.

The persistent overlay set is stored in
`/etc/esp32-conf/overlays.conf` and restored during early boot. A volatile
overlay affects only the current boot.

## GPIO and routing constraints

- An overlay may export allow-listed scalar parameters and GPIO routes. The
  manager rejects values not declared by that DTBO instead of permitting
  arbitrary live-tree changes.
- Routes not explicitly specified retain their DTBO defaults.
- A physical output pad has exactly one owner. A hardware output signal may fan
  out to multiple distinct pads.
- Two active owners cannot claim the same GPIO-matrix input signal.
- GPIO26 through GPIO32 carry the XIP Flash bus and cannot be assigned to normal
  peripherals.
- GPIO33, GPIO34, and GPIO41 are invalid pads.
- GPIO58 and GPIO59 are owned by the Linux UART0 console.
- GMAC RGMII, SDMMC, ADC, touch, and comparator functions use dedicated IO-MUX
  pads and cannot be moved freely like GPIO-matrix signals.

## Overlay catalog

| Overlay | Exposed hardware or interface | Primary constraint |
| --- | --- | --- |
| `timers` | SYSTIMER and RTC timer | Uses kernel clock and event ABIs |
| `pwm-counter` | LEDC, MCPWM, PCNT, and Sigma-Delta | PWM and counter routes share GPIO ownership |
| `gdma` | AHB-GDMA | Shares INTMTX source 22 with the comparator |
| `analog` | ADC, temperature, touch, and comparator | Dedicated analog pads |
| `gmac` | DWMAC/GMAC and PTP clock | Requires an external PHY and RGMII pin group |
| `sdmmc0`, `sdmmc1` | Corresponding SDMMC host | `bus-width=1` or `bus-width=4`; dedicated SDMMC IO-MUX |
| `sdmmc-dual` | Both SDMMC hosts | `bus-width=1` or `bus-width=4`; claims both host and pad groups |
| `sdmmc-uhs` | UHS-I timing path | Configurable bus width; requires a 1.8 V-capable card and power path |
| `uart1`, `uart2`, `uart3` | `/dev/ttyS1..3` | TX/RX use the GPIO matrix |
| `uart3-dma` | UART3 with UHCI/AHB-GDMA | Uses an internal-SRAM DMA buffer |
| `gpspi2`, `gpspi3` | SPI master and `spidev` endpoint | Does not control the MSPI Flash/PSRAM instances |
| `gpspi2-target`, `gpspi3-target` | SPI target controller | Mutually exclusive with the corresponding master role |
| `i2c0`, `i2c1` | `/dev/i2c-N` adapter | SCL/SDA routing and pad ownership |
| `i2s0`, `i2s1` | ALSA ASoC card and PCM | MCLK/BCLK/WS/data routing |
| `twai0`, `twai1` | SocketCAN `canN` | A normal bus requires a transceiver |
| `usb-device` | DWC2 device mode and ConfigFS ACM/ECM | Mutually exclusive with DWC2 host mode |

## Serial buses

### I2C0 and I2C1

- Each controller registers as a Linux I2C adapter and supports 7-bit and
  10-bit master addresses.
- The controller supports repeated starts, NACK handling, arbitration-loss
  handling, timeouts, and controller recovery.
- An interrupt-driven state machine performs data transfers.
- GPIO-matrix routes, clocks, resets, and INTMTX sources are acquired and
  released with the overlay lifecycle.

### TWAI0 and TWAI1

- The controllers expose Classical CAN and CAN-FD/BRS through SocketCAN.
- Supported behavior includes bit timing, RX/TX, error frames, listen-only,
  loopback, and bus-off recovery.
- Hardware filters and RX timestamps are exposed through driver and
  device-tree capabilities.
- Controller-only loopback covers only the internal path. A production CAN bus
  requires an external transceiver and termination.

### GPSPI2 and GPSPI3

- Master mode supports SPI modes 0 through 3, chip select, interrupt-driven
  PIO, and DMA/PIO segmented transfers.
- The PIO FIFO holds 64 bytes. The driver segments larger transfers or routes
  them through the DMA backend.
- Target mode uses a separate overlay and is mutually exclusive with master
  mode on the same controller.
- GPSPI must not claim the MSPI instances that serve XIP Flash and PSRAM.

### UART

- UART0 is the Linux console.
- UART1, UART2, and UART3 expose standard TTY devices through overlays.
- UART3 can use the UHCI/AHB-GDMA backend. Descriptor and payload placement
  follows the [DMA rules](memory-and-dma.md#dma-placement-rules).
- Native USB Serial/JTAG, UART, and DWC2 belong to separate controller domains.

## USB

- Native USB Serial/JTAG registers a fixed serial endpoint and retains a
  separate JTAG interface.
- DWC2 supports host/device role switching.
- Device mode uses ConfigFS ACM and ECM functions. If an existing native serial
  endpoint occupies the preferred index, ACM selects the next available TTY
  index.
- Removing the device overlay returns DWC2 to host mode.

## Audio

- I2S0 and I2S1 are exposed through ALSA ASoC CPU DAIs and cyclic AHB-DMA PCM.
- The driver supports standard I2S data paths, configurable sample widths,
  TDM/PDM-related formats, and playback/capture channels.
- The clock tree provides MCLK/BCLK dividers. Available rate families depend on
  the current clock source and divider combinations.
- An external codec's electrical levels, clock tolerance, and data format must
  match the active overlay.

## Analog, counter, and timing devices

- ADC is exposed through IIO with direct samples, buffered samples, and
  adjacent-channel differential measurements.
- The temperature sensor exposes readings, thresholds, alarms, and events
  through hwmon.
- PCNT exposes counts, steps, and threshold events through the Counter ABI.
- LEDC exposes PWM duty, hardware fade, and gamma-correction configuration.
- MCPWM exposes PWM, capture, fault braking, and timer synchronization.
- GPTimer, SYSTIMER, RTC timers, and watchdogs follow their respective kernel
  timing and reset models.

## Storage, networking, and power

- SDMMC supports two hosts, runtime-selected 1-bit or 4-bit width,
  sampling-window tuning, and an opt-in UHS-I path. Use
  `s31-overlay parameters sdmmc0` to inspect the allowed values and apply a
  width with, for example, `s31-overlay apply sdmmc0 bus-width=1`. The
  interactive `esp32-config` menu presents the same choice.
- GMAC uses the DWMAC networking stack and exposes a PTP hardware clock and
  timestamp path.
- The GP LDO is exposed through the regulator framework, with voltage selection
  limited to hardware-supported values.
- Linux providers centrally manage clock, reset, power-domain, and regulator
  enable/disable ordering. Peripheral drivers do not bypass those providers to
  manipulate shared registers directly.
