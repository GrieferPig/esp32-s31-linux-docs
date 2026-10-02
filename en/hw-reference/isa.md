# Instruction set and ABI

This port targets 32-bit RISC-V with Sv32 virtual memory. Use the component
compiler settings below as the build contract. The device tree advertises
the extensions Linux consumes; a compact hardware feature label is not a
substitute for a supported `-march` value.

## Component compiler settings

| Component | Instruction set selection | ABI / environment |
|---|---|---|
| OpenSBI | `rv32imabc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32`, firmware |
| Linux kernel | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32f`, patched kernel build |
| Applications and libraries | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` | `ilp32`, project Linux/musl toolchain |
| Radio payload | `rv32imafc_zicsr_zifencei_zaamo_zalrsc_xesploop_xespv2p2` | `ilp32f`, ESP ELF/picolibc build |

These choices come from the [parent Makefile](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L26-L33),
[musl toolchain configuration](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/configs/riscv32-esp-linux-musl.config#L8-L11),
[application flags](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/configs/esp32s31_rootfs_defconfig#L20),
[patched kernel ABI](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/Makefile#L45-L50), and
[radio build](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/Makefile#L176-L177).

`-march` selects instructions; `-mabi` selects argument and return-value calling
conventions. An `ilp32` application may use F instructions internally while
passing floating-point arguments according to the soft-float calling
convention. The kernel's `ilp32f` flags do not change the musl application ABI.
Build Linux applications and their libraries consistently with `ilp32`; the
radio payload's separate runtime libraries are not substitutes for musl.

## Floating-point and extra state

The port's FPU context path saves and restores **single-precision F** registers
with `fsw`/`flw`; ordinary builds do not target the D extension. Linux also
uses the platform SBI coprocessor services for Espressif extension state.
See the [F-only context implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/kernel/fpu.S#L22-L63)
and [Linux extra-state calls](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/kernel/esp32s31-ext.c#L79-L145).
Kernel or firmware code still has to respect its context and floating-point
usage rules; a compiler ABI flag alone does not make arbitrary FPU use safe.

## XespV and Xesploop

The port treats **HP core 1 as the only valid core for XespV execution**:
OpenSBI skips PIE state access on hart 0, and `libesp-simd` pins calling threads
to CPU1 before entering its assembly routines. See the
[OpenSBI restriction](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31_coproc.S#L79-L83).

Use `libesp-simd` through `esp_simd.h` and link with `-lesp-simd`. Its constructor
initializes the initial thread; each new calling thread initializes on first
use. `esp_simd_init()` returns zero or a negative errno, and public operation
wrappers use scalar fallbacks if affinity setup fails. Affinity affects the
whole calling thread. After successful initialization, do not move that thread
to CPU0 or broaden its mask: success is cached and later affinity changes are
not rechecked. The [application guide](../api-reference/userspace/index.md)
contains the complete build, link and run example; the
[library implementation](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/rootfs/esp_simd.c#L30-L75) defines this behavior.

The ordinary application flags omit XespV and Xesploop. The SIMD package
explicitly compiles hand-written extension assembly; this project does not
depend on automatic XespV vectorization.
Xesploop state handling exists, but the parent Makefile explicitly says live
loop state is not safe across all S-mode return paths used by arbitrary
libraries. Keep extension use within the reviewed library/firmware paths;
do not enable Xesploop globally for ordinary applications. See the
[build restriction](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L26-L33) and
[SIMD package flags](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/package/esp-simd/esp-simd.mk#L12-L23).
