# ISA Extensions

## Architecture and compilation policy

- The HP CPU architecture string is `RV32IMAFBCNSUX`.
- The Linux kernel ABI uses `ilp32` soft-float and does not treat FPU state as a
  general kernel calling convention.
- General userspace targets use
  `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs_xesploop`.
- `xespv2p2` is enabled only for `libesp-simd` and is not part of the global
  `-march` setting.
- The current software does not advertise `xespdsp`, `Zcb`, `Zcmp`, or `Zcmt`.

## `libesp-simd`

- The Buildroot option is `BR2_PACKAGE_ESP_SIMD`.
- The public header is `/usr/include/esp_simd.h`.
- The shared library is `/usr/lib/libesp-simd.so.1`; applications link it with
  `-lesp-simd`.
- The library provides 17 memory/string APIs, `esp_simd_eq_u8x16`, and
  `esp_simd_add_sat_u8`.
- `esp_simd_add_sat_u8` performs unsigned saturation with a maximum result of
  255.
- The library does not interpose on musl. Applications that do not link it do
  not execute XespV instructions.

## Runtime constraints

- The library constructor calls `esp_simd_init()` and pins the calling thread
  to CPU1.
- Each public entry point performs one-time initialization for a new thread.
  Pthreads inherit and confirm CPU1 affinity.
- If affinity cannot be established, every entry point falls back to its scalar
  libc/C implementation.
- After successful initialization, the caller must not broaden the thread's
  affinity.
- `esp_simd_cpu()` and `esp_simd_active()` report the current selection without
  changing state.

## Memory semantics

- Vector loads and stores process only aligned, complete 16-byte blocks.
- Scalar paths handle alignment, tails, terminators, mismatches, and overlapping
  move boundaries.
- Composite copy APIs use the same bounded primitives and do not replace native
  musl symbols.
- The kernel, OpenSBI, and userspace library manage FP and extension state
  independently and do not share uncontrolled contexts.
