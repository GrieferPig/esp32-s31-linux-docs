# Debugging

Debug by boundary rather than by banner:

- ROM/SPL/U-Boot/OpenSBI output identifies the last boot stage reached.
- `/proc/iomem`, MTD partition names, and ELF symbols identify XIP/layout state.
- `/proc/interrupts` and per-driver counters identify IRQ progress.
- clock and PMU sysfs snapshots identify provider state.
- overlay status identifies live route and resource ownership.
- radio health identifies internal progress and drops, but not RF association.
- remoteproc and LP sysfs identify firmware and mailbox state.

Retained `dmesg` is not a durable API. Capture diagnostics externally when
needed, redact credentials and identifiers, and keep one-off logs out of this
reference repository. Reproduce failures with bounded tools and always restore
outputs, serial ownership, and energized fixtures to a safe state.
