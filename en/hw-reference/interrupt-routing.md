# Interrupt routing

The interrupt matrix connects peripheral interrupt sources to a CLIC input on
an HP core:

```text
Peripheral → Interrupt matrix → Per-core CLIC → Linux IRQ handler
```

The device tree supplies the interrupt source number and trigger type. The
Linux interrupt drivers select and configure the CLIC input.

## Peripheral interrupts

A peripheral driver obtains its IRQ with `platform_get_irq()` and registers a
handler through the Linux IRQ API. For a level-triggered source, the handler
acknowledges the peripheral status so the interrupt can be cleared.

If several events share an interrupt, the driver reads the peripheral status
to find which event needs service. Longer processing can then run in a worker
or threaded handler.

## Reserved sources

System timers, inter-processor interrupts, and radio interrupts are managed by
the platform drivers. OpenSBI also uses timer 1 in each timer group for CPU
idle wakeup. Optional devices should keep these assignments available.

GPIO signal routing is configured separately through pinctrl and overlay
route settings. See the [overlay catalog](../resources/overlay-catalog.md).

TODO: list reserved interrupt sources and their assignments.

---

See [Interrupts and SMP](../api-reference/system/interrupts-smp.md) for Linux
handler and multicore details.
