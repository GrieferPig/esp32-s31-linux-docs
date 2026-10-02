# Interrupt routing

The interrupt matrix routes a peripheral source to a CLIC input on an HP
core. Three numbers appear in this path: the device-tree **matrix source**,
the allocated **CLIC slot**, and the **Linux IRQ number** returned to a driver.
They are different namespaces; do not use a matrix source as a Linux IRQ.

## Reserved system assignments

| Owner / use | HP core | Matrix source | CLIC slot | Assignment |
|---|---:|---:|---:|---|
| Linux IPI doorbell | 0 | 65 | 40 | Per-core software interrupt |
| Linux IPI doorbell | 1 | 66 | 40 | Per-core software interrupt |
| Linux SYSTIMER event | 0 | 33 | 41 | Per-core timer event |
| Linux SYSTIMER event | 1 | 34 | 41 | Per-core timer event |
| OpenSBI TIMERG0 timer 1 | 0 | 26 | 48 | Private M-mode idle-wakeup guard |
| OpenSBI TIMERG1 timer 1 | 1 | 29 | 48 | Private M-mode idle-wakeup guard |

The generic Linux peripheral allocator uses CLIC slots **16–47**, reserving
40 and 41 for local IPI/timer routes. OpenSBI's slot 48 is outside that pool.
The same slot number on two cores refers to two different core-local inputs.
See [slot constants](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp32s31-internal.h#L9-L12),
[local sources and setup](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp32s31-smp.c#L34-L42),
[allocator reservations](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp-intmtx.c#L298-L301) and
[OpenSBI guard definitions](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L47-L85).

Both GPTimer device-tree nodes set `espressif,reserved-timer-mask = <2>`.
Bit 1 reserves timer 1; the Linux counter driver skips that channel.
The guard uses the 40 MHz crystal divided by 40 and an alarm of 10,000 ticks.
See the [DTS reservation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L1236-L1252)
and its [GPTimer consumer](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/counter/esp32s31-gptimer.c#L199-L211).

Radio interrupt sources remain owned by the radio runtime while loaded; their
Linux IRQs are requested through the platform interrupt path. They are not
additional fixed CLIC-slot reservations in the table above.

## Peripheral and GPIO routing

A peripheral's `interrupts` property supplies its matrix source and trigger
type. Linux selects the CLIC slot and returns the Linux IRQ to the driver.
Generic peripheral routes currently target HP core 0; the precise affinity
restriction and handler rules are in
[Interrupts and SMP](../api-reference/system/interrupts-smp.md).

GPIO signal routing is configured separately through pinctrl and overlay
route settings. See the [overlay catalog](../resources/overlay-catalog.md).
