# Instruction set and ABI

S31 uses `RV32IMAFBCNSUX` ISA. This project uses a custom `musl` toolchain that targets the `ilp32/ilp32f` ABI.

In this port, the Linux kernel and OpenSBI are patched with additional state saves, to support the use of single-precision FPU, the `XespV` and `Xesploop` extensions.

## Compiler settings

TODO: unify component ABI

| Component | Instruction set selection | ABI |
|---|---|---|
| OpenSBI | `rv32imabc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32` |
| Linux build | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32f` |
| Applications | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32` |
| Radio firmware | ESP-IDF toolchain and radio build settings | `ilp32f` |

`-march` selects the instructions the compiler can generate. `-mabi` selects
how functions pass arguments and return values. For example, an `ilp32`
application can still use floating-point instructions internally.

Use the project's Linux toolchain for applications and libraries. See
[Writing applications](../api-reference/userspace/index.md).

## Espressif extensions

Espressif's XespV instructions are available through `libesp-simd`.
The library initializer sets CPU affinity to HP core 1 before using those
instructions. Usage guidance for `libesp-simd` is not yet documented.

> Note: On the S31, only HP core 1 can execute `XespV` instructions.

Compiler autovectorization is not available.

For ordinary builds, `XespV` and `Xesploop` extensions are available in assembly form, but not used automatically.
