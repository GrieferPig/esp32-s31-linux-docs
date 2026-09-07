# Power Domains

The S31 PMU provider represents hardware power islands through generic PM
domains. Clients attach through device tree and runtime PM; they do not gate
domains directly.

The read-only `domains` sysfs attribute reports each domain's policy, software
and hardware state, force state, transition counters, and radio vote where
applicable. A software request may remain logically active while hardware is
held on by another dependency.

Radio and LP transitions cross clock, reset, memory-retention, and wake-source
boundaries. Suspend code must order prepare, quiesce, domain transition, wake,
restore, and reclaim operations and must abort safely if any prerequisite
rejects the requested state.

Linux suspend-to-idle keeps the HP side running and uses the LP protocol in
dry-run mode. Suspend-to-RAM uses a separate non-dry-run retention contract:
APPWR mode 0 gates all HP clock classes and powers down the CPU, TOP,
connection, and HP-alive logic islands, while mode 2 retains the four HP memory
banks. The LP core and RTC timer remain always-on and request the APPWR wake
transition. See the power-management API guide for the current DWC2, radio, and
wake-source restrictions.
