# Development Setup

Initialize all submodules and confirm their recorded revisions before editing.
Use the parent Makefile for integrated builds and component-local build commands
only when their output directory, cross compiler, and configuration match the
parent project.

Keep changes in the repository that owns the source. Commit a modified
submodule before updating its parent gitlink. Preserve unrelated dirty files,
generated binaries, local credentials, and hardware logs outside commits.

For documentation work, install `requirements.txt`, run `make html` and
`make linkcheck`, scan Markdown for private paths or identifiers, and confirm
the parent README still resolves the published manual and the docs repository's
raw `bootlog.png` URL.


## Port ownership and integration contracts

Paths below are relative to the parent checkout unless a submodule is named.
Review both sides of a shared interface when changing its layout or semantics.

| Subsystem | Source owners | Contract and relevant checks |
|---|---|---|
| SRAM, flash and packaging | `shared/s31_memory_layout.h`, `configs/esp32s31-layout.cfg`, parent `Makefile`; Linux DTS/linker and OpenSBI platform | `make check-layout`; slot capacity checks; manifest and artifact hashes; preserve persist when flashing |
| HP boot and SMP/XIP | `opensbi-esp32-s31/platform/generic/espressif`, `u-boot-esp32-s31`, `linux-esp32-s31/arch/riscv` | Match toolchain/IDF pins; boot both cores and run target quick selftest after a boot-chain or kernel change |
| LP firmware and IPC | `firmware/lp`, Linux `drivers/remoteproc/esp32s31_lp.c` and mailbox driver; shared headers | LP mailbox ABI and SRAM reservations; `lp-core` HIL; power-wake tests require the documented fixture |
| Radio payload and host frontends | `firmware/radio`, Linux `drivers/platform/esp32s31-radio*`, Wi-Fi and Bluetooth drivers | External ELF/import ABI; ELF negative tests; bound-device startup; separate over-air Wi-Fi and BLE acceptance |
| Overlays and peripherals | Linux `arch/riscv/boot/dts/espressif`, DT bindings and peripheral drivers; `rootfs/s31_overlay.c` | `make check-dt` includes merged overlays and a negative control; overlay host tests; electrical/data HIL only with the required wiring |
| Userspace policy and rootfs | `buildroot-external/board/esp32-s31/overlay`, `buildroot-external/package`, `rootfs` | Persistent desired state versus runtime state; service failure recovery; target boot and configuration checks |
| Host HIL and release metadata | `tools/hil/s31_hil.py`, `tools/hil/serial_transport.py`, `tools/build_manifest.py`, `tools/release_assets.py` | Protocol/timeout/cleanup negative tests; real serial and target tests; release slot files and checksum contract |

The parent repository owns integration and dependency pins; each submodule owns
its source changes. Documentation under this repository describes this downstream
port. Maintenance does not depend on a plan to submit it upstream. Keep dated
acceptance evidence separate from the support contract, and record skipped
fixture tests explicitly.
