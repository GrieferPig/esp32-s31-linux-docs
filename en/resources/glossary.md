# Glossary

| Term | Meaning |
|---|---|
| ABI | Application binary interface: the data layout and calling conventions used between components |
| Active overlays | Device-tree overlays currently applied in the running kernel |
| CLIC | Core-Local Interrupt Controller, used to deliver interrupts to the HP cores |
| Device tree | Description of the hardware and the resources used by its drivers |
| DTB | Compiled device-tree file |
| DTBO | Compiled device-tree overlay, loaded to add or change a hardware description |
| FIT | U-Boot image format containing boot components and their metadata |
| H4 | Bluetooth packet framing with a packet-type byte before each HCI packet |
| HCI | Host Controller Interface between a Bluetooth host stack and controller |
| HIL | Hardware-in-the-loop testing using a host computer, the board, and optional test peers |
| HP core / hart | One of the high-performance RISC-V processors running Linux |
| LP core | Low-power processor running firmware managed by Linux remoteproc |
| M-mode | RISC-V machine mode, used by OpenSBI |
| S-mode | RISC-V supervisor mode, used by Linux |
| OpenSBI | Firmware that supplies low-level RISC-V services to Linux and U-Boot |
| Payload | In the radio guides, the external radio firmware loaded by the Linux driver |
| Persist | The writable JFFS2 flash partition used for saved files and settings |
| PSRAM | External pseudo-static RAM used for Linux's writable memory |
| Resource claim | An overlay entry that reserves a controller, DMA channel, or other shared resource |
| Saved overlays | Desired overlay selections for the next boot; `--volatile` changes leave this set unchanged |
| SPL | Small first-stage U-Boot loader that prepares the board for the next boot stages |
| Sv32 | RISC-V virtual-memory translation for a 32-bit address space |
| XIP | Execute in place: running code directly from mapped flash |
