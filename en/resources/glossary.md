# Glossary

| Term | Meaning in this port |
|---|---|
| CLIC | Core-Local Interrupt Controller used by the HP harts |
| HP core | High-performance RISC-V core running OpenSBI/Linux |
| LP core | Low-power core managed by remoteproc firmware |
| XIP | Execute in place from mapped NOR flash |
| PSRAM | External pseudo-static RAM used for Linux writable memory |
| FIT | U-Boot Flattened Image Tree containing boot components |
| DTB/DTBO | Base device tree blob / device-tree overlay blob |
| Resource claim | Overlay-manager identifier preventing conflicting live hardware use |
| Typed radio ABI | Kernel-call interface that isolates frontends from payload symbols |
| Payload | External radio implementation loaded by the S31 radio loader |
| H4 | Bluetooth UART-style packet framing used by the direct HCI device |
| HIL | Hardware-in-the-loop framework using a host and optional P4 peer |
| Persist | Writable JFFS2 partition preserved by normal image updates |
