# Clock tree

The S31 clock driver manages clock sources, dividers, and peripheral gates
through the Linux common clock framework. Drivers request clocks from the
device tree and enable them while their hardware is in use.

## CPU and timer clocks

Both HP cores share the CPU clock. Linux exposes CPU frequencies of 80, 160,
240, and 320 MHz through a single cpufreq policy.

Linux timekeeping uses SYSTIMER at 16 MHz. OpenSBI's idle-wakeup guards use
timer 1 in each timer group, clocked from the 40 MHz crystal with a divide-by-40
prescaler.

To change CPU frequency, follow
[Power management](../api-guides/power-management.md).

## Peripheral clocks

A device-tree node identifies the clock inputs required by the peripheral.
The driver uses the clock API to obtain the current rate and to prepare,
enable, and release those inputs. The provider keeps critical clocks running
and tracks shared users.

Use [Clock, reset, and power APIs](../api-reference/system/clock-reset-power.md)
when adding a driver.

## View clock settings

Read the provider's clock list on the board:

```sh
for file in /sys/bus/platform/devices/*/clocks; do
    [ -r "$file" ] && cat "$file"
done
```

The list includes the clock ID, name, rate, and enable state. It is useful for
checking that a peripheral has the expected clock before investigating its
register settings.
