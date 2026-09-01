# System Architecture

## Processors and execution domains

- ESP32-S31 contains two high-performance RISC-V harts and one low-power CPU
  domain.
- The HP harts implement the `RV32IMAFBCNSUX` architecture baseline. Linux
  userspace uses the `ilp32` soft-float ABI.
- Linux runs in S-mode. OpenSBI runs in M-mode and provides boot, HSM, reset,
  and other services that must remain in M-mode.
- Runtime Linux SMP IPIs, TLB shootdowns, clock events, and device interrupts
  use native S-mode paths and are not forwarded through OpenSBI.

## Boot chain

```text
ROM -> U-Boot SPL -> FIT(OpenSBI fw_dynamic + U-Boot proper + DTB) -> Linux
```

- SPL initializes early on-chip resources and external memory, then loads the
  FIT image.
- OpenSBI establishes the M-mode runtime and provides SBI services to
  U-Boot/Linux.
- U-Boot proper obtains the device tree and kernel entry point from the FIT.
- Linux takes ownership of runtime clocks, resets, pin control, interrupt
  domains, and peripheral drivers.
- Runtime device-tree overlays enable variable peripherals without rebuilding
  the base DTB.

## Resource ownership

| Resource | Owner | Behavior |
| --- | --- | --- |
| Boot, HSM, and reset | OpenSBI | Remains within the M-mode service boundary |
| SMP IPIs and RFENCE | Linux | Native S-mode CLIC doorbells |
| Per-hart clock events | Linux | SYSTIMER counter1 and targets |
| Peripheral clocks, resets, and pinmux | Linux | Coordinated by providers, pinctrl, and overlays |
| Wi-Fi and Bluetooth closures | Linux radio subsystem | Serialized through a controlled S-mode execution path |
| Persistent configuration | Merged OverlayFS root | Managed under `/etc/esp32-conf` |

## Base device tree and dynamic devices

- The base device tree is `esp32s31_generic.dtb`.
- DTBO files for potentially conflicting peripherals are installed under
  `/usr/lib/s31-overlays`.
- `/dev/s31-overlay` manages runtime application, conflict detection,
  replacement, and rollback.
- Concurrent overlays must not conflict over GPIOs, GPIO-matrix inputs,
  exclusive controllers, or shared interrupt sources.

See [Memory and DMA](memory-and-dma.md) and
[Interrupts and SMP](interrupts-and-smp.md) for the detailed address, DMA, and
interrupt contracts.
