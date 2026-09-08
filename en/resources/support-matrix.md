# Support Matrix

This matrix records implemented software behavior. It is not a record of a
particular test run and does not guarantee external board wiring.

Status values are **Supported**, **Partial**, **Blocked**, and **Not
implemented**. **Partial** means that the public Linux interface exists but a
hardware or firmware dependency still limits the intended behavior; **Blocked**
means a known correctness issue keeps the interface disabled.

| Area | Port behavior | Development boundary |
|---|---|---|
| Boot | ROM, SPL, U-Boot, OpenSBI, Linux XIP chain | Fixed NOR layout and FIT handoff |
| MMU | Sv32 enabled | Cached PSRAM is Linux writable memory |
| SMP | Two HP harts supported | CLIC, IPI, and SYSTIMER are platform dependencies |
| Storage | SquashFS root, JFFS2 persist, MTD partitions | Persist is excluded from normal full-image updates |
| Overlays | Named runtime overlays with conflict claims | Optional hardware depends on board wiring |
| Serial/GPIO/I2C/SPI | Linux subsystem drivers present | Pin routes selected by overlays |
| DMA | AHB and AXI DMAengine support | Descriptor SRAM and cache rules apply |
| Timers/PWM/counters | SYSTIMER, GPTimer, LEDC/MCPWM/SDM/PCNT support as configured | GPTimer1 in each timer group is firmware-reserved for SMP idle; Linux exposes GPTimer0 through Counter |
| Analog | ADC, DAC, comparator, touch, TSENS support as configured | Analog pads conflict with some digital functions |
| Network | GMAC and S31 Wi-Fi frontend | External PHY/RF behavior is board-dependent |
| Bluetooth | Typed HCI path and optional direct H4 device | Radio payload and selected mode required |
| Radio coexistence | Wi-Fi/BT combo scheduling in radio core/payload | Payload dependency and packaging boundary |
| CPU frequency | **Supported**: shared 80, 160, 240, and 320 MHz OPPs | HP clock changes are serialized across both harts |
| CPU idle | **Supported**: both HP harts enter an `SMP-WFI` state through an S31 OpenSBI service | Each hart has a private 10 ms M-mode GPTimer guard because delegated S-mode IRQs alone cannot wake M-mode WFI; an older OpenSBI image falls back to polling |
| Suspend-to-idle | **Supported as a diagnostic**: LP dry-run handshake, repeated timer wake, and connected DWC2 mass-storage resume pass | LP state is polled in `noirq`; the HP CPUs remain active, so this is not a low-power state |
| Suspend-to-RAM | **Experimental**: SBI `mem`, RTC-timer wake, dual-hart warm resume and radio restart | Three Wi-Fi-only cycles preserve RAM/boot identity and pass reassociation plus exact UDP echoes. Three connected BLE cycles preserve boot identity and the host process, with peer GATT rediscovery/read/reconnect after every wake. AP requires userspace restart; combo and external GPIO wake remain unverified |
| LP core | **Supported**: remoteproc, mailbox ABI v1, calibrated timer, GPIO polling wake, and wake log | Linux measures RTC_SLOW over 100 ms before starting firmware and publishes its Q13.19 period in the IDF-compatible LP store; this board measured 155386 Hz |
| Wake sources | **Partial**: RTC timer wake and LP GPIO0-7 arming/polling are implemented | The latest retained powered-wake result returned timer-only reason `0x1` despite fixture continuity passing; external GPIO wake cannot be marked passed. LP-UART and WoWLAN are absent |
| Retention | **Experimental**: HP memory banks, OpenSBI runtime state, Linux page tables/cache state, and SMP resume are retained | Timer-wake tests preserve RAM and USB readback; these checks do not establish GPIO wake, current draw or selective-bank retention |
| Deep sleep | **Experimental**: the LP RTC timer enters non-retentive PMU deep sleep and ROM performs a normal verified cold boot | Timer wake, deep-reset cause, both HP harts after reboot, and 3/4/5-second cycles pass; GPIO wake and selective retained-memory policy are not implemented, and pre-existing persist/JFFS2 write failures can delay userspace on a cold boot |
| USB | DWC2 high-speed host, mass storage, connected-device s2idle, device-mode overlay, and Linux gadget interfaces | Suspend-to-RAM cold-resets the S31 controller/UTMI PHY; 10 repeated cycles retained the connected disk and read checksum, with a port reset on each resume |
| Watchdogs | Linux watchdog drivers as configured | Reset effects depend on selected watchdog block |
| Normal poweroff | **Experimental**: orderly shutdown reaches the untimed PMU request, with RTC wake disabled | No automatic boot during a 50-second observation; external reset recovers Linux. Shutdown current remains unmeasured |
| Advanced Wi-Fi | **Experimental**: AP/AP+STA, receive-only monitor, PEAP/EAP-TLS vendor provisioning | Open AP passes; same-channel open AP+STA maintains both associations and passes 256 exact 1472-byte UDP echoes per interface in sequential data phases. Monitor captures 10 fixture beacons with valid radiotap framing. Protected AP and enterprise authentication remain unverified; P2P, injection and WoWLAN are absent |
| I2C long messages | **Experimental**: 7/10-bit FIFO continuation and repeated-start combined transfers | Exact 7-bit reads/writes up to 4096 bytes have passed, but repeated runs still encounter intermittent timeouts; stable board acceptance is incomplete. Host wire-model tests cover 65535 bytes |
| SPI target | **Experimental**: DMA up to 4096 bytes, 8/16/32-bit words and LSB/MSB order | Both controllers pass external-master data checks at 100 kHz for modes 0–3, 8/16/32-bit MSB words and up to 4096 bytes. LSB order, abort and malformed-frame acceptance remain pending |
| Generic I2S | **Experimental**: I2S/left-justified/DSP A/B, TDM masks, MCLK and external cards | Both controllers pass external-master S16_LE stereo at 8/16/48 kHz: exact 16 KiB playback and at least 16 KiB contiguous capture after clock synchronization. ALSA streaming DMA performs cache synchronization. Startup samples, external-codec, other formats and extended endurance remain unverified |
| HIL | Host agent plus optional P4 programmable peer; guarded sequencing and repeat execution are implemented | P4 standalone firmware passes 7/7 checks. After reconnecting L0, all four lanes pass bidirectional levels, GPIO IRQ and release checks |

For exact compile-time availability, use the Kconfig reference and active
kernel configuration. For exact runtime availability, inspect the applied
overlays and corresponding Linux subsystem interfaces.
