# Power management

The port exposes CPU frequency control, firmware-assisted idle, diagnostic
suspend-to-idle, an experimental retention path, and shutdown/deep-sleep
requests. This guide covers their controls and current limitations.

## CPU frequency

Both HP cores share one policy with 80, 160, 240 and 320 MHz operating points.
Read the available frequencies and governor:

```sh
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

Select the userspace governor and request 160 MHz, expressed in kHz:

```sh
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 160000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
```

Return to the supplied default governor:

```sh
echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

Linux timekeeping uses the separate 16 MHz SYSTIMER. See the
[clock relationships](../hw-reference/clock-tree.md) and
[configured governors](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/configs/esp32s31_defconfig#L72-L82).

## CPU idle

The supplied command line selects `esp32s31_idle=wfi`. Linux enables the
firmware-assisted WFI path only when the required SBI extension is present;
if the option is disabled or that capability is absent, polling remains the
fallback. This is a capability check, not a test of firmware age. See the
[activation code](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp32s31-smp.c#L52-L92).

OpenSBI reserves timer 1 in each timer group for a guard configured as 10,000
ticks at 1 MHz (10 ms). The `timers` overlay leaves those channels reserved and
exposes timer 0 to applications. Exact assignments are in
[Interrupt routing](../hw-reference/interrupt-routing.md).

## Test LP wake handling while Linux is awake

```sh
s31-lpctl ping
s31-lpctl sleep-test 1000
```

These commands check the mailbox and LP timer with Linux running. The
[LP reference](../api-reference/lp-core/index.md) gives GPIO transition examples,
argument ranges and result fields. Start there before testing system sleep.

## Suspend-to-idle (`freeze`)

With LP firmware ready, enable a one-second diagnostic timer and enter freeze:

```sh
echo 1000 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
echo freeze > /sys/power/state
dmesg | tail -n 80
```

The range is 10–600000 ms; zero (the default) disables the automatic timer.
Validation happens while preparing suspend, so accepting a parameter write
does not itself establish that the requested interval is valid. Clear the
explicit test timer when finished:

```sh
echo 0 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
```

This path exercises Linux device suspend/resume and LP transactions. The HP
side polls for LP completion during the noirq phase; it is not evidence of an
HP low-power state. See the [polling implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/remoteproc/esp32s31_lp.c#L238-L274).

The S31 DWC2 suspend callback disables its IRQ, global interrupts and low-level
hardware, and sets `phy_off_for_suspend`. There is no freeze-specific exception
that keeps the controller/PHY active. The resume path re-enables and restores
the controller as needed; USB devices may reconnect. See
[DWC2 suspend/resume](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/usb/dwc2/platform.c#L721-L795).

## Suspend-to-RAM (`mem` / `deep`)

Treat retention suspend as **experimental**. The current Linux/LP/OpenSBI
sources agree on ABI 1 and the 28-word control layout. The existing checks cover ABI-version agreement and the LP timer's start condition;
they do not validate device recovery or the complete physical sleep cycle.
See the [source contract tests](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/tests/test_s31_feature_contracts.py#L155-L174)
and [LP development guide](lp-firmware-development.md).

Parameters under `/sys/module/esp32s31_lp/parameters/` are:

| Parameter | Accepted values | Default |
|---|---|---|
| `mem_wake_ms` | Timer interval, 10–600000 ms | 2000 |
| `mem_wake_gpio` | LP GPIO0–7, or `-1` to disable GPIO wake | `-1` |
| `mem_gpio_active_high` | `Y` for high, `N` for low | `Y` |
| `mem_gpio_pull` | `0` none, `1` pull-up, `2` pull-down | `0` |

The timer remains required as a recovery source even when GPIO wake is added.
A selected GPIO must be inactive when ARM runs, as in the awake GPIO test.
LP starts the retention timer after OpenSBI publishes `HP_ASLEEP`. The profile
and memory reservations are in [Power domains](../hw-reference/power-domains.md)
and [Memory map](../hw-reference/memory-map.md).

For a development test, first inspect the states exposed by the running
kernel. Only proceed with the following retention request if `deep` is listed:

```sh
cat /sys/power/state
cat /sys/power/mem_sleep
```

```sh
echo 2000 > /sys/module/esp32s31_lp/parameters/mem_wake_ms
echo -1 > /sys/module/esp32s31_lp/parameters/mem_wake_gpio
echo deep > /sys/power/mem_sleep
echo mem > /sys/power/state
dmesg | tail -n 100
```

`mem_sleep` selects what `mem` means; `deep` selects the platform retention
path. See the [Linux suspend registration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/kernel/suspend.c#L173-L199)
and [MEM request validation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/remoteproc/esp32s31_lp.c#L816-L864).

Record the complete serial log, image/source revisions, selected wake source,
resume result and post-resume peripheral operation. Radio and USB recovery
paths exist, but successful reconnection must be checked on the tested image.
A board trace identifying a current failure, or a repeatable successful cycle
with measured current, is still needed to replace this experimental status.

## Shut down

```sh
poweroff
```

Linux stops services and synchronizes filesystems before requesting firmware
shutdown. The clock provider prepares the 40 MHz XTAL handoff before the
secondary hart is stopped; OpenSBI verifies that state before entering the
PMU sequence. If untimed shutdown cannot complete, firmware halts instead of
rebooting. Reset/EN or a power cycle starts Linux again. This command does not
remove the board's external supply. See the [clock handoff](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1776-L1807)
and [firmware fallback](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L909-L933).

## Timed deep sleep

Timed deep sleep requests an orderly Linux shutdown followed by a **fresh cold
boot**, without preserving the running application. Save application state
first. With LP firmware ready, request a four-second interval:

```sh
for attr in /sys/bus/platform/devices/*/deep_sleep; do
    [ -w "$attr" ] || continue
    echo 4000 > "$attr"
    break
done
```

The public control accepts 1000–600000 ms and a timer wake source. Linux latches
the request and starts orderly power-off; OpenSBI programs the RTC and selects
the cold-boot path.
See the [request handler](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/remoteproc/esp32s31_lp.c#L1265-L1307) and [RTC setup](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L976-L1015).

The RTC conversion uses a fixed **155386 Hz** slow-clock value, so the actual
delay can differ between boards. `previous` and `wake_reason` are software
markers for the requested operation, not proof that physical sleep succeeded.
A failed timed transition can fall back to a reset; inspect the serial log
before treating a reboot as a successful sleep cycle.

GPIO wake is implemented for the awake test and retention request, not the
public cold-boot deep-sleep control. LP-UART and WoWLAN packet wake are not
implemented wake paths here. A repeatable board-current reference remains
undocumented; the required measurement context is listed in
[Power domains](../hw-reference/power-domains.md).
