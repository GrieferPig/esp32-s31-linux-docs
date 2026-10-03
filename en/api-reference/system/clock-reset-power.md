# Clocks, resets, and power

S31 drivers use the Linux clock, reset-controller, and power-domain APIs.
The device tree connects each peripheral to the providers it needs.

## Enable a peripheral

During probe, acquire the device's clocks, reset controls, regulators, and
power-management resources. Return a deferred-probe error when a required
provider is still starting.

A typical startup sequence powers the device, enables its clocks, releases
reset, and programs the peripheral registers. Follow the peripheral's hardware
requirements when ordering these operations.

The commonly used APIs include:

| API | Use |
|---|---|
| `devm_clk_get()` | Get a device clock |
| `clk_prepare_enable()` | Prepare and enable a clock |
| `clk_disable_unprepare()` | Release the clock when finished |
| `devm_reset_control_get_optional_exclusive()` | Get an optional reset control |
| `reset_control_reset()` | Pulse a peripheral reset |

For shared clocks and power domains, the providers track active users. Use
these APIs so another active device can keep its dependencies enabled. The
current power provider only allows `hp-connectivity` to power off, subject to
DT policy and the radio vote; the other exposed domains stay always on.

## Stop or remove a device

Stop DMA and interrupt activity before releasing buffers or turning off the
peripheral. Then release clocks and power resources in the reverse order of
startup. Apply the same cleanup to a partially completed probe.

## Inspect the providers

The clock provider's `clocks` attribute lists clock names, rates, critical
status, and common-clock-framework prepared state. Its `on`/`off` field is not
a direct hardware-gate readback. The power provider's `domains` attribute lists its domain state.

```sh
for file in /sys/bus/platform/devices/*/clocks; do
    [ -r "$file" ] && cat "$file"
done
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

For CPU frequency and system sleep, see
[Power management](../../api-guides/power-management.md).
