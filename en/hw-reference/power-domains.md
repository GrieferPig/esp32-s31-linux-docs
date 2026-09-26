# Power domains

The ESP32-S31 separates high-performance logic, memory, clocks, and low-power
hardware into groups that can be managed independently. Linux drivers use the
power-domain and clock providers to keep the resources they need active.

## Peripheral power

A device-tree node can refer to a power domain through its `power-domains`
property. The provider tracks users of that domain, including radio activity.
A driver releases its request after stopping the device.

To view the provider's state, run:

```sh
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

## System sleep

The firmware's APPWR retention profile selects memory-retention mode for the
four HP memory banks, switches off HP logic groups, and gates the HP clocks.
The configured power value is `0x0000aa00`, with clock value `0x00000000`.
The low-power side supplies the wakeup request.

The Linux integration and current suspend limitation are described in
[Power management](../api-guides/power-management.md). That guide also covers
CPU idle, shutdown, and timed deep sleep.

## Measure power use

Measure current at the board's power input when comparing power states. USB
bridges, regulators, LEDs, and connected peripherals can affect the total.

TODO: measure power use data on the core board as ref
