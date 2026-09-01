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
