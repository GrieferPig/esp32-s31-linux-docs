# ISA and ABI

The high-performance cores implement a 32-bit RISC-V architecture. The build
uses the following explicit ISA groups rather than relying on compiler host
defaults.

| Consumer | ISA/ABI contract |
|---|---|
| OpenSBI safe path | `rv32imabc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs` |
| Linux kernel | `rv32imafbc_zicsr_zifencei_zaamo_zalrsc_zba_zbb_zbc_zbs`, `ilp32f` |
| Userspace | same configured ISA set, `ilp32` |

Kernel code may use the single-precision floating-point calling convention
selected by `ilp32f`, while userspace follows the musl `ilp32` toolchain ABI.
This distinction is intentional and must be preserved when adding assembly,
external objects, or firmware interfaces.

`zicsr` and `zifencei` are named explicitly. Atomic operations use the
configured `zaamo` and `zalrsc` capabilities. Bit-manipulation extensions are
enabled for compiled code but must not be assumed by ROM routines or foreign
binary payloads unless their own contract states so.

Do not infer CPU compatibility from ELF class alone. Verify `Tag_RISCV_arch`,
ABI attributes, relocation type, and the exact toolchain prefix for every
prebuilt object introduced into the image.
