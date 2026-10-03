# Clocks, resets, and power

Device-tree references connect S31 peripherals to the Linux clock, reset and
power-domain providers. [Clock tree](../../hw-reference/clock-tree.md) describes
the registered clock relationships; [Power domains](../../hw-reference/power-domains.md)
describes the domain policies.

## Acquire and release driver resources

Use the provider APIs for the resources declared by a device's binding.
Preserve acquisition errors, including `-EPROBE_DEFER`, so probe can be retried
when a required provider becomes available.

| API | Role |
|---|---|
| `devm_clk_get()` | Acquire a clock reference; does not enable it |
| `clk_prepare_enable()` | Prepare and enable the acquired clock |
| `clk_get_rate()` | Read the clock rate used to calculate peripheral timing |
| `clk_disable_unprepare()` | Balance a successful prepare/enable |
| `devm_reset_control_get_optional_exclusive()` | Acquire an optional reset control; an absent optional control may be `NULL` |
| `reset_control_reset()` | Request a reset pulse through that control |

The S31 I2C probe is a concrete example: map registers, acquire and enable the
clock, register `clk_disable_unprepare()` with `devm_add_action_or_reset()`,
acquire and pulse the optional reset, then configure the controller and request
its IRQ. Its error path preserves provider errors. This ordering belongs to
that controller; follow the binding and hardware requirements for another
device. See [I2C probe and cleanup](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/i2c-esp32s31.c).

Before releasing a clock or buffer, stop the device's transfers and interrupt
activity. DMA cleanup has additional synchronization requirements described in
[DMA and cache coherency](../../api-guides/dma-and-cache.md). Do not bypass a
provider with direct clock or PMU register writes from a client driver.

## Inspect provider state

```sh
for file in /sys/bus/platform/devices/*/clocks; do
    [ -r "$file" ] && cat "$file"
done
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

Each `clocks` line has these fields:

| Field | Meaning |
|---|---|
| Leading integer | Clock ID from the S31 clock binding |
| Name | Registered CCF clock name |
| `state=on` / `state=off` | Result of `clk_hw_is_prepared()`; CCF preparation state |
| `critical=0` / `critical=1` | Whether CCF marks the clock critical |
| `rate=` | Rate reported by the provider, in Hz |

`state=on` does not independently read back an electrical clock signal or prove
that a peripheral is operational. Interpret it together with the rate, probe
messages and device state. The precise output comes from
[`clocks_show()`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/clk/clk-esp32s31.c).

The `domains` output separates policy, software state and force-register
settings; see its [field definitions](../../hw-reference/power-domains.md).
For CPU frequency and system sleep controls, see
[Power management](../../api-guides/power-management.md).
