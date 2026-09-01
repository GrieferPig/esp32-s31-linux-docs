# Clock, Reset, and Power APIs

S31 providers integrate with Linux common-clock, reset-controller, and generic
PM-domain frameworks. Client probe ordering is dependency-driven by device
tree; drivers should return deferred probe when a provider is not ready.

The normal activation sequence is:

1. attach the PM domain;
2. acquire clocks and resets;
3. enable regulators or analog dependencies;
4. power the device through runtime PM;
5. prepare and enable clocks;
6. deassert reset; and
7. configure the peripheral.

Shutdown reverses the dependency order after quiescing DMA and interrupts.
Shared clock and domain state is reference counted. Provider diagnostics such
as `clocks` and `domains` are read-only snapshots and do not replace framework
APIs.
