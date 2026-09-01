# Adding a Driver

1. Select the standard Linux subsystem and reuse its public API.
2. Define or reuse a YAML device-tree binding.
3. Model clocks, resets, IRQs, PM domains, DMA channels, pinctrl, regulators,
   and reserved memory as provider references.
4. Add Kconfig and Makefile integration with complete dependencies.
5. Implement probe deferral, bounded error unwinding, runtime PM, and removal.
6. Add the base disabled node or named overlay that represents real hardware.
7. Document userspace behavior, resource ownership, and unsupported modes.

Avoid singleton globals unless the hardware itself is singular. Do not expose
raw MMIO when a Linux subsystem exists. Hard-IRQ and DMA callbacks must obey
allocation, locking, and cache rules. A new private ABI requires a UAPI header
and an entry under Linux `Documentation/ABI` before applications depend on it.
