# Interrupts and SMP

ESP32-S31 uses a Core-Local Interrupt Controller rather than a RISC-V PLIC.
Each high-performance hart has local interrupt state; Linux programs routing,
priority, enable, and threshold through the S31 CLIC irqchip implementation.

## Interrupt classes

| Class | Linux role |
|---|---|
| Local timer interrupt | Scheduler tick and timekeeping events |
| Software interrupt | Inter-processor interrupts and hart wake-up |
| Peripheral interrupt | Device events routed through the interrupt matrix |
| Radio interrupt | Latency-sensitive notification to the radio core |

The SYSTIMER driver supplies the clocksource and per-CPU clock-event behavior.
Interrupt delivery and timekeeping are separate contracts: a registered
irqchip does not by itself imply that timer or IPI paths are operational.

## SMP rules

- Per-CPU CLIC state is initialized when each hart starts.
- Drivers must use Linux affinity and IRQ APIs instead of programming routing
  registers directly.
- Cross-hart state requires normal kernel synchronization even when the
  underlying MMIO is shared.
- Hard-IRQ callbacks must not sleep. Radio and DMA paths copy bounded state and
  defer processing to worker or NAPI context.
- CPU hotplug is constrained by platform interrupt and timer ownership; code
  must not assume that arbitrary firmware can start or stop a hart.

## DMA completion

AHB and AXI GDMA engines signal completion through normal Linux IRQ handlers.
Descriptors and shared status areas are in internal reserved SRAM. Completion
handlers must perform the cache and ownership transitions required by the DMA
API before exposing data to clients.
