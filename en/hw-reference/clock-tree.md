# Clock Tree

The S31 clock provider exposes SoC clock gates and derived rates through the
Linux common clock framework. Device drivers obtain named clocks from device
tree and must use prepare/enable and disable/unprepare APIs.

The provider's read-only `clocks` sysfs attribute reports clock ID, name,
enable/critical state, and current rate for diagnostics. It is observational;
writing provider registers through `/dev/mem` or a client driver is unsupported.

Critical clocks remain enabled across normal client transitions. Rate changes
must respect parent selection, divider limits, shared consumers, radio/LP
ownership, and timing dependencies. A new binding must name every required
clock and document whether the consumer tolerates rate changes while active.
