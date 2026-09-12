# Kconfig Reference

The current kernel tree defines the following S31-specific configuration
symbols. Dependencies and exact prompts remain authoritative in their Kconfig
files.

| Symbol | Area |
|---|---|
| `ESP32S31_CLIC` | Core-local interrupt controller |
| `ESP32S31_SYSTIMER`, `ESP32S31_SYSTIMER_CLOCKSOURCE`, `ESP32S31_SYSTEM_TIMERS` | Timekeeping and per-CPU events |
| `ESP32S31_CPUIDLE` | SMP-aware platform idle state |
| `ESP32S31_COPROC_CONTEXT` | Coprocessor context management |
| `ESP32S31_CACHE` | Cache/MMU platform support |
| `SOC_ESP32S31` | SoC selection |
| `ESP32S31_CLOCK` | Clock and reset provider |
| `ESP32S31_PMU` | Power-domain provider |
| `ESP32S31_DT_OVERLAY` | Named overlay manager |
| `ESP32S31_AHB_GDMA`, `ESP32S31_AXI_GDMA` | DMAengine providers |
| `ESP32S31_GPTIMER`, `ESP32S31_PCNT` | Timer and pulse counter |
| `I2C_ESP32S31`, `SPI_ESP32S31`, `SND_SOC_ESP32S31_I2S` | I2C, SPI, and I2S controllers |
| `PINCTRL_ESP32S31` | Pin controller and GPIO matrix |
| `PWM_ESP32S31_LEDC`, `PWM_ESP32S31_MCPWM`, `PWM_ESP32S31_SDM` | PWM providers |
| `ESP32S31_ADC`, `ESP32S31_DAC` | Analog conversion |
| `ESP32S31_COMPARATOR`, `ESP32S31_TOUCH` | Analog comparator and touch sensing |
| `SENSORS_ESP32S31_TSENS` | Temperature sensor |
| `ESP32S31_WATCHDOG` | Watchdog support |
| `MTD_ESP32S31_FLASH` | Integrated NOR flash MTD |
| `NVMEM_ESP32S31_EFUSE`, `HW_RANDOM_ESP32S31` | eFuse and hardware random-number providers |
| `PHY_ESP32S31_USB` | USB PHY |
| `REGULATOR_ESP32S31_ANA_I2C`, `REGULATOR_ESP32S31_GP_LDO` | Analog transport and GP-LDO regulators |
| `ESP32S31_LP_REMOTEPROC` | LP-core remoteproc and mailbox |
| `ESP32S31_RADIO_BLOBS` | External radio payload support |
| `ESP32S31_RADIO_SMODE`, `ESP32S31_RADIO_SMODE_DRIVER` | S-mode radio core |
| `ESP32S31_WIFI` | Linux Wi-Fi frontend |
| `BT_ESP32S31` | Linux Bluetooth frontend |
| `CRYPTO_DEV_ESP32S31` | Hardware crypto provider |

Enabling a client without its clock, reset, IRQ, PMU, DMA, or device-tree
provider does not make the device usable. Defconfig changes must be reviewed
together with image-size and rootfs-module consequences.
