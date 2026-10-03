# Power management

You can change the CPU frequency, use automatic CPU idle, shut down the board,
and test LP timer and GPIO wakeup. This guide covers the commands for each
operation.

## CPU frequency

Both HP cores share a single CPU-frequency policy. The available frequencies
are 80, 160, 240, and 320 MHz.

Read the available frequencies and current governor:

```sh
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

To run at 160 MHz, select the userspace governor and set the frequency in kHz:

```sh
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 160000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
```

To return to the default performance governor:

```sh
echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

Linux timekeeping continues to use the 16 MHz SYSTIMER.

## CPU idle

The standard configuration selects firmware-assisted WFI idle with
`esp32s31_idle=wfi`. Linux enters this state automatically when there is no
work to run.

OpenSBI uses timer 1 in each timer group as a 10 ms wakeup guard. The `timers`
overlay leaves these channels reserved and exposes timer 0 to applications.

## LP wakeup tests

With LP firmware running, test the mailbox and timer:

```sh
s31-lpctl ping
s31-lpctl sleep-test 1000
```

Linux stays awake during these tests. GPIO examples and accepted arguments are
in the [LP reference](../api-reference/lp-core/index.md).

## Suspend-to-idle

The `freeze` path exercises Linux device suspend/resume and LP wakeup handling.
Stop Wi-Fi activity and disable its interface before experimenting; current
SoftMAC cannot suspend an active interface, and automatic radio recovery is
not established. Set a timer before entering it:

```sh
echo 1000 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
echo freeze > /sys/power/state
```

The timer accepts 10–600000 ms. A value of zero disables the automatic timer.
After returning, check `dmesg` for the LP wake result.

This is a diagnostic suspend path: the HP side polls for LP completion during
the noirq phase, so it still consumes power. The S31 DWC2 suspend callback
disables its IRQ and low-level hardware. Resume reinitializes the PHY/controller,
and attached USB devices may reconnect. Unmount storage and disable USB-backed
swap before a suspend experiment.

## Suspend-to-RAM

The source implements an experimental APPWR retention path with a mandatory
recovery timer and optional LP GPIO wake. Linux, OpenSBI, and LP firmware now
agree on the 112-byte ABI-v1 control block; rebuild all three together.
This implementation-level check does not establish successful retention or
peripheral recovery on a board.

The Linux-side options are available under
`/sys/module/esp32s31_lp/parameters/` for developers working on this support:

| Parameter | Values |
|---|---|
| `mem_wake_ms` | Timer interval, 10–600000 ms; default 2000 |
| `mem_wake_gpio` | LP GPIO0–7, or `-1` to disable GPIO wake |
| `mem_gpio_active_high` | `Y` for high-level wake, `N` for low-level wake |
| `mem_gpio_pull` | `0` for none, `1` for pull-up, `2` for pull-down |

The intended retention path keeps RAM and always arms a recovery timer.
Suspend with an active SoftMAC interface is unsupported; bring the interface
down before testing and verify the complete system-suspend result. Active
Wi-Fi replay and automatic reassociation are not established. Bluetooth and combo
recovery also need separate validation. The HIL Wi-Fi suspend sequence is a
diagnostic, not evidence that these recovery paths pass. See
[LP firmware development](lp-firmware-development.md) for the shared protocol
and memory layout.

## Shut down

Use the normal Linux shutdown command:

```sh
poweroff
```

This stops services and synchronizes filesystems before requesting the firmware
shutdown state. Press Reset/EN or cycle power to start the board again.
If the firmware cannot complete the power transition, it halts the CPU.

## Timed deep sleep

Timed deep sleep shuts down Linux and starts a fresh boot when its timer
expires. Save application state before entering it.

With LP firmware running, this example requests a four-second interval:

```sh
for attr in /sys/bus/platform/devices/*/deep_sleep; do
    [ -w "$attr" ] || continue
    echo 4000 > "$attr"
    break
done
```

The accepted interval is 1000–600000 ms. Linux records the request and starts
an orderly shutdown; OpenSBI then programs the RTC wakeup timer.

This path uses a fixed 155386 Hz RTC slow-clock value, so the delay can vary
between boards. Its `previous` and `wake_reason` fields are software markers
for the requested operation. Check the reset log when diagnosing a failed
sleep transition.

GPIO deep-sleep wake, LP-UART wake, and WoWLAN packet wake are not implemented
by this documented path. No measured board-current figures are provided.
