# Peripheral API Reference

ESP32-S31 peripherals are exposed through standard Linux frameworks. The base
device tree supplies providers and always-present blocks; named overlays select
optional instances, pins, routes, and mutually exclusive modes.

| Function | Linux interface | S31-specific constraint |
|---|---|---|
| GPIO/pinctrl | GPIO character device, pinctrl | Route ownership is checked by overlays |
| UART | TTY/serial | UART0 is normally the console; UART3 has a DMA overlay |
| I2C | `/dev/i2c-*` | I2C0 and I2C1 routes are independently selectable |
| GPSPI | SPI controller/target APIs | Controller and target overlays are exclusive per instance |
| I2S | ALSA SoC | Clock, pin, and DMA resources must be enabled together |
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
