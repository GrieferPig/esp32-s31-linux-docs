# Interrupt routing

The interrupt matrix connects peripheral interrupt sources to a CLIC input on
an HP core:

```text
Peripheral → Interrupt matrix → Per-core CLIC → Linux IRQ handler
```

The device tree supplies the interrupt source number and trigger type. The
Linux interrupt drivers select and configure the CLIC input. Generic peripheral
interrupts are currently routed only to HP core 0; changing their affinity to
HP core 1 is unsupported. Per-core timer and IPI routes are separate.

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

| Purpose | HP core | Matrix source | CLIC slot / privilege |
|---|---|---:|---|
| Inter-processor interrupt | 0 | 65 | 40 / S-mode |
| Inter-processor interrupt | 1 | 66 | 40 / S-mode |
| SYSTIMER event | 0 | 33 | 41 / S-mode |
| SYSTIMER event | 1 | 34 | 41 / S-mode |
| TIMERG0 timer 1 idle guard | 0 | 26 | 48 / M-mode |
| TIMERG1 timer 1 idle guard | 1 | 29 | 48 / M-mode |

The generic allocator uses CLIC slots 16–47 except reserved slots 40 and 41,
leaving 30 slots. Radio device IRQs use this allocator; their CLIC slot numbers
are not fixed. These assignments come from the Linux irqchip drivers and
OpenSBI's S31 services implementation.

---

See [Interrupts and SMP](../api-reference/system/interrupts-smp.md) for Linux
handler and multicore details.
