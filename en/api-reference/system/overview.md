# System Architecture

The port runs a 32-bit RISC-V Linux system on the ESP32-S31 high-performance
cores. Linux uses Sv32 virtual memory, executes the kernel image directly from
mapped NOR flash, and places writable kernel state and userspace in external
PSRAM. Internal high-performance SRAM remains reserved for firmware state,
DMA-visible buffers, interrupt-time stacks, and latency-sensitive services.

## Component ownership

| Component | Primary responsibility |
|---|---|
| ROM | Reset entry, immutable chip initialization, serial download mode |
| U-Boot SPL | Early clocks, pinmux, PSRAM, and loading the U-Boot FIT |
| OpenSBI | M-mode runtime, hart startup, SBI services, and Linux handoff |
| U-Boot proper | FIT selection, base DTB, kernel command line, and boot policy |
| Linux | MMU, SMP, drivers, filesystems, networking, and userspace ABI |
| Radio payload | Closed radio implementation loaded behind typed Linux APIs |
| LP firmware | Low-power core mailbox service and sleep coordination |

## Address spaces

The kernel must distinguish cached PSRAM, uncached or device mappings, NOR XIP
addresses, and internal SRAM aliases. A buffer is not DMA-safe merely because
its virtual address is accessible to the CPU. Drivers use the DMA API and the
reserved SRAM pools declared by device tree.

## Resource ownership

The base device tree contains always-present system blocks. Optional peripheral
routes are activated through named overlays. The overlay manager rejects
resource and GPIO conflicts before modifying the live tree. Clock, reset, PMU,
DMA, interrupt, and pinctrl providers remain the single owners of their
hardware resources; client drivers request them through Linux frameworks.

## Stable boundaries

Developer-facing contracts are:

- standard Linux subsystems and userspace APIs;
- documented misc-device, sysfs, and module-parameter interfaces;
- device-tree bindings and overlay metadata;
- radio core ABI version 4 (payload ABI version 2); and
- LP mailbox ABI version 2.

Addresses, private payload symbols, diagnostic counters, and implementation
details are not stable unless explicitly identified as a contract.
