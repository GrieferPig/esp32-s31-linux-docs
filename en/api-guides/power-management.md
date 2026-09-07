# Power Management

The S31 power-management implementation deliberately separates frequency
scaling, Linux idle accounting, suspend-to-idle validation, and destructive
power states. An interface being visible does not imply that the corresponding
hardware domain is powered down.

## CPU frequency

The CPU clock provider and OPP table expose one shared policy for both HP
harts. The available rates are 80, 160, 240, and 320 MHz. Clock transitions are
serialized and update the common HP clock; users must not assign independent
rates to the two CPUs.

The 16 MHz SYSTIMER driver explicitly enables its HP clock gate, selects XTAL,
disables stale comparators, and acknowledges pending levels during early boot.
It preserves the running counter and does not depend on ROM, SPL, or a
previously loaded IDF image to leave the timer configured.

The `performance` and `userspace` governors are enabled. A fixed rate can be
selected through the normal cpufreq policy interface:

```sh
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 160000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
```

Return the system to its default policy with:

```sh
echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

## CPU idle

The standard configuration selects the S31 `SMP-WFI` cpuidle state with the
`esp32s31_idle=wfi` command-line option. The driver probes the vendor OpenSBI
extension before registering and falls back to IRQ-enabled polling when paired
with an older firmware image. Boot stays in polling mode until the cpuidle
device initcall, after runtime clockevents are available.

Delegated S-mode timer and doorbell interrupts do not by themselves wake a hart
from an M-mode WFI on this silicon. The CLINT comparator is also exposed through
a shared hart-relative alias, so it cannot safely provide two concurrent wake
deadlines. OpenSBI instead reserves timer 1 in TIMERG0 for hart 0 and timer 1 in
TIMERG1 for hart 1. Each comparator runs from the 40 MHz crystal through a
divide-by-40 prescaler and routes to a private M-level CLIC slot while its hart
is in WFI. A 10 ms one-shot guard bounds every idle entry; OpenSBI clears and
disarms the timer before returning to Linux. Normal Linux clockevents and
timekeeping remain on the per-hart 16 MHz SYSTIMER targets.

The GPTimer Counter binding carries an `espressif,reserved-timer-mask` property.
The base S31 device tree reserves channel 1 in both timer groups, so an enabled
GPTimer overlay exposes only `timer0` to Linux and cannot overwrite the idle
guards. Board validation covers both harts idling concurrently, pinned timer
wakeups, CPU1 hotplug cycles, cross-hart load, a 40-second unattended idle
interval, and GDMA interrupt progress without an RCU stall or lockup.

## LP firmware and sleep protocol

The LP core is managed by remoteproc and uses mailbox ABI version 2. Before
starting it, the driver grants REE access to the LP system-register,
peripheral-clock/reset, IOMUX, and mailbox PMS windows used by the firmware.
The last KiB of LP SRAM contains a CRC-protected sleep-control structure. Linux
performs the following transaction:

1. `PREPARE` validates ABI, sequence, CRC, wake mask, and deadline.
2. `ARM` records the LP cycle counter and starts the selected wake source.
3. `QUERY` returns state, result, wake reason, and timestamps.
4. `RECLAIM` returns ownership to Linux; failures use `ABORT`.

Linux retries a bounded control-block snapshot when an immediately active wake
level changes the record while it is being copied. The CRC still rejects a
record that never reaches a stable state.

The powered-suspend timer uses RTC target 1 and converts microseconds with the
current RTC slow-clock calibration. The target and interrupt remain in the
always-on LP domain while the HP clock classes are gated.

Handshake, timer wake, GPIO wake, wake-log, and retention-descriptor
capabilities are advertised.
GPIO0 through GPIO7 can be sampled by the running LP core after it takes RTCIO
ownership. LP-UART wake remains reserved in the ABI.

The timer and GPIO transactions can be tested without suspending Linux:

```sh
s31-lpctl sleep-test 100
s31-lpctl gpio-test 3 high up 500
s31-lpctl gpio-test 3 low down 500
```

The GPIO command accepts a pin from 0 through 7, a `low` or `high` target, an
optional `none`, `up`, or `down` pull, and a 10 through 5000 ms timeout. The
internal-pull form verifies RTCIO ownership, LP sampling, wake logging,
mailbox delivery, and pad release. It does not prove that the same pin wakes a
powered-down HP domain. Board straps or connected fixtures can override a weak
internal pull, so an externally driven test should use a pin selected for that
board.

## Suspend-to-idle diagnostic path

Linux s2idle can exercise device suspend/resume and the complete LP
prepare/arm/query/reclaim transaction. Set a bounded timer before requesting
`freeze`:

```sh
echo 1000 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
echo freeze > /sys/power/state
```

The accepted range is 10 through 600000 ms; zero disables the automatic timer.
The transaction uses `DRY_RUN`. During `noirq`, Linux polls the shared LP state
because the mailbox interrupt cannot yet wake the HP CPUs through CLIC. The
timeout uses calibrated atomic delays because normal Linux timekeeping is
suspended in this phase. Both the LP wake and timeout paths report a hard wake
event, so a missing LP response cannot leave the s2idle wait blocked. This
keeps suspend testing recoverable, but the polling HP CPU consumes power and
must not be described as a low-power state.

The S31 DWC2 host keeps its controller and UTMI PHY context live across this
diagnostic. The wrapper does not retain forced-host state through either DWC2
partial power-down or PCGCCTL clock gating, and resetting the PHY during resume
can assert the shared level interrupt before host state is restored. A connected
high-speed mass-storage device therefore remains enumerated while s2idle tests
the LP transaction. This is a functional system-PM path, not USB or HP-domain
power retention, and it does not reduce the polling power cost described above.

## Suspend-to-RAM retention path

`mem` uses the SBI system-suspend extension and a non-dry-run LP transaction.
Before entering APPWR sleep, OpenSBI writes back Linux PSRAM, copies its RW/BSS
and hart scratch state into LP SRAM, installs a retained warmboot trampoline,
and saves the normal APPWR profile. The sleep profile sets mode 0 for the CPU,
TOP, connection, and HP-alive logic islands, mode 2 for all four HP memory
banks, and mode 0 for all HP clock classes. LP RTC target 1 publishes the wake
record and asserts `APPWR_SW_WAKEUP_REQ`; the trampoline restores OpenSBI state
before generic HSM resume returns to Linux. The normal APPWR profile is then
restored.

Select a bounded timer and enter suspend with:

```sh
echo 2000 > /sys/module/esp32s31_lp/parameters/mem_wake_ms
echo mem > /sys/power/state
```

The timer accepts 10 through 600000 ms. Board validation currently covers a
10-second cycle, ten repeated 1-second cycles with both CPUs returning online,
and a 128 KiB tmpfs buffer retaining its checksum over a 5-second cycle. The
always-on RTC persistent clock advances suspend time. These tests demonstrate
logical clock/power transitions and memory integrity; they are not a current
measurement.

The S31 DWC2 platform path masks its level interrupt and powers off the
controller/UTMI PHY before APPWR removes the HP logic domains. Resume treats the
lost context as a cold controller recovery and lets USB reset the connected
port. Board validation covers ten repeated 1-second cycles with a connected
high-speed mass-storage device; `/dev/sda` remained available and its first
4 KiB checksum was unchanged after every cycle. This validates read-side
recovery, not mounted-filesystem writes or every USB device class.

An optional LP GPIO0-7 level can be armed alongside the mandatory timeout:

```sh
echo 0 > /sys/module/esp32s31_lp/parameters/mem_wake_gpio
echo Y > /sys/module/esp32s31_lp/parameters/mem_gpio_active_high
echo 2 > /sys/module/esp32s31_lp/parameters/mem_gpio_pull
echo 10000 > /sys/module/esp32s31_lp/parameters/mem_wake_ms
echo mem > /sys/power/state
```

`mem_gpio_pull` is 0 for none, 1 for pull-up, or 2 for pull-down. The LP
firmware rejects a level that is already active while arming, and begins
powered GPIO polling only after OpenSBI publishes `HP_ASLEEP`. The timer remains
mandatory as a recovery bound. A combined inactive-GPIO/timer descriptor has
completed powered suspend with a timer-only wake reason; an external transition
still requires fixture validation.

This path remains experimental. With radio core ABI v4 and payload ABI v2,
the PM callback detaches the frontends, shuts down the firmware runtime and
releases its power vote. Resume restores pristine firmware data, restarts the
runtime and replays retained monitor and committed enterprise configuration. The
direct HCI endpoint emits a Hardware Error event to restart the host state
machine. Wireless connections must be established again by userspace; they
are not retained through sleep. This removes the unconditional loaded-radio
`-EBUSY` restriction. Three Wi-Fi-only timer-wake cycles have preserved RAM,
the boot identity and both harts, followed by reassociation and exact UDP data
checks. AP service needs an explicit userspace restart because cfg80211 stops
it during suspend. BTstack now discards stale connections, recomputes
advertising eligibility and re-enters HCI initialization after the controller
reset event. Three connected BLE suspend cycles preserved Linux, both harts
and the original BTstack process; the C6 peer rediscovered GATT, read its
characteristic and reconnected after every wake. The old over-air connection
is lost during sleep. Combo recovery remains unverified.
A failed restart leaves interfaces detached. LP-UART and WoWLAN
packet wake remain unimplemented.

## Normal shutdown

Use the normal init shutdown sequence, for example `poweroff`, to stop services
and synchronize filesystems. The clock provider's poweroff-prepare handler
switches both HP harts to the 40 MHz crystal. An SBI shutdown without an armed
deep-sleep timer then enters the PMU deep profile with RTC timer targets and
wake sources disabled. This path does not require the LP overlay and does not
schedule an automatic reboot. Reset/EN or a power cycle is required to boot
again. It does not disconnect the board's external power supply.

If an untimed shutdown cannot satisfy the PMU prerequisites, OpenSBI halts
instead of intentionally rebooting. This fallback does not prove low current.
Board validation reached the untimed PMU request, observed 50 seconds without
an automatic boot, and recovered through external reset. Board current has
not been measured. Deploy the matching
OpenSBI/U-Boot image as well as Linux to use this behavior.

## Deep sleep

Deep sleep is a distinct, destructive sysfs operation rather than another
Linux suspend state. Read its current state at the LP remoteproc device and arm
a timer in milliseconds by writing the same attribute:

```sh
lpdev=$(dirname "$(find /sys/bus/platform/devices -name deep_sleep | head -n1)")
cat "$lpdev/deep_sleep"
echo 4000 > "$lpdev/deep_sleep"
```

The accepted interval is 1000 through 600000 ms. Writing it prepares and arms
an LP timer descriptor, latches the authorization in always-on LP_SYS storage,
and starts an orderly poweroff. The reboot notifier moves the shared HP clock
tree to the 40 MHz crystal while both harts can still complete the handshake.
OpenSBI then stops the LP hart, programs RTC target 0, installs the IDF-derived
deep-sleep PMU profile, switches the transition clock to RC_FAST, and asserts
the terminal PMU request from SRAM. A failed clock or PMU prerequisite falls
closed to an ordinary reset.

Timer expiry produces `PMU_SYS_PWR_DOWN_RESET`; ROM takes the normal verified
boot path rather than a retained wake stub. LP_SYS reports the previous deep
cycle and timer wake reason after Linux returns:

```text
armed=0 previous=1 wake_reason=0x1
```

Board validation covers 3, 4, and 5 second cycles and confirms both HP harts
online after the cold boot. This is non-retentive: kernel and userspace state is
lost, unlike suspend-to-RAM. GPIO wake, selective retained memory, and power
measurements remain outside the implemented boundary. Existing NOR
program/JFFS2 failures can independently delay or prevent userspace startup
after any reset; deep-reset and early SMP logs may still have completed in that
case.
