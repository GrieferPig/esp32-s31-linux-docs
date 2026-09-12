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

## Loader format and compatibility

The loader accepts ELF32 little-endian RISC-V relocatable objects with one
symbol table, bounded NUL-terminated names, RELA records and at most 16 MiB
of allocated section content including alignment. Executable/data sections,
relocation symbol indices and write widths are checked before relocation.
Runtime exports must point inside loaded sections, with executable functions
and writable ISR-depth state. Unsupported relocation types or malformed
metadata are rejected before execution; this is structural validation, not
firmware authentication.

`tools/tests/test_s31_radio_elf.py` exercises the actual validation code with
malformed ELF fixtures and, when present, the generated payload. Set
`S31_TEST_SANITIZERS=1` for ASan/UBSan host checks. These tests do not execute
radio firmware or prove Wi-Fi/Bluetooth behavior.

The no-op `s31_rtos_hard_tick` export remains part of payload ABI v1. Its lack
of work does not make it removable dead code. The obsolete M-mode branches
and unused private timer helpers are outside this retained ABI.

The radio Makefile tracks the resolved archive set, generated header depfiles,
compiler identity, flags and IDF revision. Changing `S31_WIFI_ONLY` or an IDF
header must invalidate affected objects; archive changes must relink the
payload. An unchanged invocation preserves object and payload timestamps.
