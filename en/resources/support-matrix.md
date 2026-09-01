# Support Matrix

This matrix records implemented software behavior. It is not a record of a
particular test run and does not guarantee external board wiring.

| Area | Port behavior | Development boundary |
|---|---|---|
| Boot | ROM, SPL, U-Boot, OpenSBI, Linux XIP chain | Fixed NOR layout and FIT handoff |
| MMU | Sv32 enabled | Cached PSRAM is Linux writable memory |
| SMP | Two HP harts supported | CLIC, IPI, and SYSTIMER are platform dependencies |
| Storage | SquashFS root, JFFS2 persist, MTD partitions | Persist is excluded from normal full-image updates |
| Overlays | Named runtime overlays with conflict claims | Optional hardware depends on board wiring |
| Serial/GPIO/I2C/SPI | Linux subsystem drivers present | Pin routes selected by overlays |
| DMA | AHB and AXI DMAengine support | Descriptor SRAM and cache rules apply |
| Timers/PWM/counters | SYSTIMER, GPTimer, LEDC/MCPWM/SDM/PCNT support as configured | Channel and pin resources are shared |
| Analog | ADC, DAC, comparator, touch, TSENS support as configured | Analog pads conflict with some digital functions |
| Network | GMAC and S31 Wi-Fi frontend | External PHY/RF behavior is board-dependent |
| Bluetooth | Typed HCI path and optional direct H4 device | Radio payload and selected mode required |
| Radio coexistence | Wi-Fi/BT combo scheduling in radio core/payload | Payload dependency and packaging boundary |
| LP core | remoteproc, mailbox ABI v2, sleep coordination | Deep power states depend on retention and wake support |
| USB | Device-mode overlay and Linux gadget interfaces | Route and external connector are board-specific |
| Watchdogs | Linux watchdog drivers as configured | Reset effects depend on selected watchdog block |
| HIL | Host agent plus optional P4 programmable peer | Peer cases require actual peer execution |

For exact compile-time availability, use the Kconfig reference and active
kernel configuration. For exact runtime availability, inspect the applied
overlays and corresponding Linux subsystem interfaces.
