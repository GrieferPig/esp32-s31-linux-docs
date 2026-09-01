# Radio Core ABI Version 3

ABI version 3 presents bounded typed Wi-Fi and HCI operations plus the stable
health snapshot. Frontends must register callback tables, copy interrupt-time
data into Linux ownership, and use queue-capacity helpers for backpressure.

Code that called private payload symbols or retained payload-owned frame
pointers must migrate to the typed API. Payload format compatibility remains a
loader/core concern and is not exposed as a userspace ABI.
