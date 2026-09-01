# Introduction

ESP32-S31 Linux is an integrated port spanning boot firmware, a 32-bit RISC-V
Linux kernel, Buildroot userspace, external radio firmware, low-power firmware,
device-tree overlays, image packaging, and hardware-in-the-loop tooling.

The main repository pins Buildroot, Linux, OpenSBI, U-Boot, and this
documentation as submodules. Build and behavior changes often cross those
boundaries, so developers should identify the owning repository before editing.

This guide is organized like the ESP-IDF programming guide:

- **Get Started** covers environment, build, flash, and boot.
- **API Reference** describes kernel, firmware, and userspace contracts.
- **Hardware Reference** records maps, routes, clocks, domains, and interrupts.
- **API Guides** explain how to extend the port safely.
- **Contribute** defines repository, HIL, documentation, and release workflows.
- **Resources** provides generated-style indexes and concise lookup tables.

The documentation intentionally omits individual test logs and private device
data. Support statements describe implemented software behavior and explicitly
identify external wiring or payload prerequisites.
