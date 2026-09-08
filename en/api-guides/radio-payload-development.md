# Radio Payload Development

The payload is an external implementation behind the Linux radio core. Build it
with the pinned ESP-IDF dependency environment and the repository's generator;
do not link new host symbols by hand.

When changing the payload:

1. update the payload source and exported entry contract;
2. regenerate and review the import allowlist;
3. confirm link regions fit the reserved radio SRAM layout;
4. update loader relocation and validation only when the format changes;
5. preserve typed radio ABI v1 and payload ABI v1, incrementing them together
   when an incompatible contract is introduced;
6. update the radio SquashFS package and legal manifest; and
7. verify Wi-Fi, HCI, coexistence, queue backpressure, and unload/error paths.

Payload functions invoked from IRQ context must be bounded. Linux frontends
must not retain pointers into payload-owned transient storage.
