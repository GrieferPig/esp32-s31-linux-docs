# Instruction set and ABI

The S31 HP cores implement 32-bit RISC-V with integer, atomic, single-precision
floating-point, compressed, bit-manipulation, and Espressif-specific extensions.
Privilege modes and compiler extension strings are separate concepts; use the
component-specific settings below rather than treating a hardware shorthand
as a `-march` argument. The custom musl toolchain supports the port's `ilp32`
and `ilp32f` calling conventions.

In this port, the Linux kernel and OpenSBI are patched with additional state saves, to support the use of single-precision FPU, the `XespV` and `Xesploop` extensions.

## Compiler settings

The component ABIs intentionally differ in the current build. Do not link
application objects built with `ilp32f` against the `ilp32` rootfs libraries.

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
The library initializer pins the calling thread to HP core 1. Each new thread
checks affinity on its first public API call. `esp_simd_init()` returns zero
on success or a negative error; `esp_simd_active()` reports the calling
thread's initialized state. The public wrappers use scalar fallback paths
if affinity initialization fails. Do not change a successfully initialized
thread's affinity afterwards: its cached state does not revalidate an
external affinity change.

To use it, include `esp_simd.h` and link with `-lesp-simd`. The `esp-simd`
Buildroot package installs the header and libraries in the staging tree, and
the shared library in the target rootfs. After a rootfs build, compile a
program from the project root using the ordinary scalar application flags:

```sh
cache/toolchains/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -march=rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs \
  -mabi=ilp32 -mtune=esp-base \
  -Iout/buildroot/staging/usr/include simd-demo.c \
  -Lout/buildroot/staging/usr/lib -lesp-simd -o simd-demo
```

For example, `esp_simd_memcpy(dst, src, size)` provides the explicit copy
wrapper; the header also exposes string operations and selected byte-vector
helpers. This does not replace musl functions globally. Use the package's
specialized assembly rather than compiling arbitrary application code with
vendor-extension flags.

> Both `XespV` and `Xesploop` execute only on HP core 1. `Xesploop` state is
> preserved for explicit tests, but is not safe to leave live across every
> S-mode return path used by arbitrary libraries. Keep ordinary userspace on
> the scalar/FPU/bit-manipulation settings above; do not enable vendor
> extensions globally.

XespV autovectorization is not enabled by the supplied application build flags.

The supplied ordinary build flags do not enable automatic use of `XespV` or
`Xesploop`. Explicit assembly and specialized library/test code must observe
the hart-affinity and context restrictions above.
