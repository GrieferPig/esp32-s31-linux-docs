# Kernel configuration

Kernel options select the drivers and system features built into Linux. The
S31 defconfig is under `linux-esp32-s31/arch/riscv/configs/`. The parent
build applies `configs/kernel/common.config` and `board.config`, plus
`debug.config` for `DEBUG=1`. See [Build configuration](../get-started/build-configuration.md).

## S31 options

Names below omit the `CONFIG_` prefix used in `.config` files.

| Option | Purpose |
|---|---|
| `ESP32S31_CLIC` | Core-local interrupt controller |
| `ESP32S31_SYSTIMER_CLOCKSOURCE` | SYSTIMER driver used by the S31 defconfig for the 16 MHz clocksource and S31 timer-event helpers |
| `ESP32S31_SYSTIMER` | Alternative Kconfig entry that builds the same SYSTIMER driver |
| `ESP32S31_SYSTEM_TIMERS` | Read-only Counter framework access to SYSTIMER and LP RTC counters |
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
| `ESP32S31_RADIO_BLOBS` | Radio firmware integration |
| `ESP32S31_RADIO_SMODE`, `ESP32S31_RADIO_SMODE_DRIVER` | Linux S-mode radio runtime |
| `ESP32S31_WIFI`, `ESP32S31_WIFI_SOFTMAC` | mac80211 single-station frontend |
| `ESP32S31_RADIO_XIP` | Prelinked radio payload in its dedicated flash slot |
| `CC_OPTIMIZE_FOR_SIZE` | Native kernel size optimization (`-Os`) |
| `TRIM_UNUSED_KSYMS` | Upstream unused-export trimming, retaining the generated radio import whitelist |
| `UNUSED_KSYMS_WHITELIST` | Generated `out/generated/radio-kernel-symbols.txt` path supplied by the parent build |
| `EXT4_FS`, `JBD2` | Built-in ext4 filesystem and journal support |
| `BT_ESP32S31` | Bluetooth frontend |
| `CRYPTO_DEV_ESP32S31` | Hardware crypto driver |

The peripheral subsystems also have their own options, such as
`I2C_ESP32S31`, `SPI_ESP32S31`, and `SND_SOC_ESP32S31_I2S`. Their Kconfig entries
declare their framework dependencies. I2C and SPI use `depends on` for
requirements such as clocks and device-tree support; those dependencies must
already be enabled. The I2S option also selects the generic DMAengine PCM
helper. Per-CPU clockevents use the RISC-V timer driver, which calls the S31
SYSTIMER event helper; `ESP32S31_SYSTEM_TIMERS` is a separate Counter interface.

The parent build enforces size optimization, radio XIP, upstream export
trimming with the generated radio whitelist, built-in ext4, and the full board
peripheral contract. Removing these required options makes configuration
validation fail. The whitelist is generated from the radio payload's undefined
symbols before the native Linux build; do not replace it with a hand-maintained
list.

## Check a build

After `make linux`, the resulting configuration is in
`out/linux/.config`. For example:

```sh
grep -E '^(CONFIG_I2C_ESP32S31=|# CONFIG_I2C_ESP32S31 is not set)' out/linux/.config
grep -E '^(CONFIG_ESP32S31_RADIO_SMODE_DRIVER=|# CONFIG_ESP32S31_RADIO_SMODE_DRIVER is not set)' out/linux/.config
```

`y` builds a feature into the kernel; `m` builds a loadable module where the
option supports it. Disabled options are shown as `# CONFIG_NAME is not set`.

`.config` is generated. For lasting changes, update the source defconfig and
the parent `configs/kernel/*.config` fragments affecting the option.
The next parent build reapplies all of these inputs and resolves dependencies
with `olddefconfig`. Enable the corresponding overlay on the board to use an
optional peripheral; an overlay cannot supply a driver omitted from the build.
