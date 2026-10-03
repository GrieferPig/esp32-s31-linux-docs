# Kernel configuration

Kernel options select the drivers and system features built into Linux. The
S31 defconfig is under `linux-esp32-s31/arch/riscv/configs/`. The parent
Makefile applies the selected [build configuration](../get-started/build-configuration.md)
when building the kernel.

## S31 options

Names below omit the `CONFIG_` prefix used in `.config` files.

| Option | Purpose |
|---|---|
| `ESP32S31_CLIC` | Core-local interrupt controller |
| `ESP32S31_SYSTIMER`, `ESP32S31_SYSTIMER_CLOCKSOURCE` | System timekeeping and per-CPU timer events |
| `ESP32S31_SYSTEM_TIMERS` | Read-only Counter access to SYSTIMER and LP RTC counters |
| `ESP32S31_CPUIDLE` | Firmware-assisted S31 CPU idle |
| `ESP32S31_COPROC_CONTEXT` | Save and restore coprocessor state |
| `ESP32S31_CACHE` | Cache support |
| `ESP32S31_CLOCK` | Clock and reset provider |
| `ESP32S31_PMU` | Power-domain provider |
| `ESP32S31_DT_OVERLAY` | Runtime overlay manager |
| `ESP32S31_AHB_GDMA`, `ESP32S31_AXI_GDMA` | DMAengine providers |
| `ESP32S31_GPTIMER`, `ESP32S31_PCNT` | General-purpose timers and pulse counters |
| `ESP32S31_ADC`, `ESP32S31_DAC` | Analog conversion |
| `ESP32S31_COMPARATOR`, `ESP32S31_TOUCH` | Comparator and touch sensing |
| `ESP32S31_WATCHDOG` | Watchdog support |
| `ESP32S31_LP_REMOTEPROC` | LP-core firmware and mailbox |
| `ESP32S31_RADIO_BLOBS` | External radio firmware support |
| `ESP32S31_RADIO_SMODE`, `ESP32S31_RADIO_SMODE_DRIVER` | Linux S-mode radio runtime |
| `ESP32S31_RADIO_XIP` | Prelinked flash-XIP radio payload; requires matching `radio.bin`, kernel, and module |
| `ESP32S31_WIFI` | Wi-Fi frontend |
| `ESP32S31_WIFI_SOFTMAC` | Current mac80211 single-station frontend |
| `BT_ESP32S31` | Bluetooth frontend |
| `CRYPTO_DEV_ESP32S31` | Hardware crypto driver |

The peripheral subsystems also have their own options, such as
`I2C_ESP32S31`, `SPI_ESP32S31`, and `SND_SOC_ESP32S31_I2S`. Their Kconfig entries
select the related framework dependencies.

## Check a build

After `make linux`, the resulting configuration is in
`out/linux/.config`. For example:

```sh
grep '^CONFIG_I2C_ESP32S31=' out/linux/.config
grep '^CONFIG_ESP32S31_RADIO_SMODE_DRIVER=' out/linux/.config
```

`y` builds a feature into the kernel; `m` builds a loadable module where the
option supports it. Disabled options are shown as `# CONFIG_NAME is not set`.

`.config` is ephemeral. For lasting changes, update the source defconfig and any relevant board
settings. The next parent build reapplies the source defconfig to `.config`. Enable the corresponding
overlay on the board to use an optional peripheral.
