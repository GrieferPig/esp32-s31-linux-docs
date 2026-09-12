# Support Matrix

This matrix records implemented software behavior. It is not a record of a
particular test run and does not guarantee external board wiring. Historical
board observations below describe bounded evidence and known limits, not
acceptance of the current checkout. Record new results locally with source and
image identity, fixture details and known limits.

Status values are **Supported**, **Partial**, **Blocked**, and **Not
implemented**. **Partial** means that the public Linux interface exists but a
hardware or firmware dependency still limits the intended behavior; **Blocked**
means a known correctness issue keeps the interface disabled.

| Area | Port behavior | Development boundary |
|---|---|---|
| Boot | ROM, SPL, U-Boot, OpenSBI, Linux XIP chain | Fixed NOR layout and FIT handoff |
| MMU | Sv32 enabled | Cached PSRAM is Linux writable memory |
| SMP | Two HP harts supported | CLIC, IPI, and SYSTIMER are platform dependencies |
| Storage | SquashFS root and MTD partitions; **experimental** writable JFFS2 persist | Slot-wise updates preserve the partition. The matched SRAM/cache/SBI-return changes passed bounded file-churn, compaction, ten reboot/hash cycles and a cleanup reboot. Long-term wear and abrupt-power-loss durability remain unverified |
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
| Suspend-to-idle | **Supported as a diagnostic**: LP dry-run handshake and timer wake | LP state is polled in `noirq`; HP CPUs remain active. Validate connected USB resume separately; this is not a low-power state |
| Suspend-to-RAM | **Supported**: SBI `mem`, RTC-timer/GPIO wake, dual-hart warm resume and radio restart | Validate external GPIO wake, RAM retention and radio reconnection per build; current draw and selective-bank retention remain unmeasured |
| LP core | **Supported**: remoteproc, mailbox ABI v1, calibrated timer, GPIO polling wake, and wake log | Linux measures RTC_SLOW over 100 ms before starting firmware and publishes its Q13.19 period in the IDF-compatible LP store; the value is board- and clock-source-dependent |
| Wake sources | **Supported with stated limits**: RTC timer and external LP GPIO0-7 | Use the guarded LP-GPIO fixture to verify the wake reason; LP-UART and WoWLAN are absent |
| Retention | **Supported for the all-bank profile**: HP memory banks, OpenSBI state, Linux page tables/cache state, and SMP resume | Verify a retained RAM checksum and both harts after wake; selective-bank retention and current draw are unverified |
| Deep sleep | **Experimental**: non-retentive PMU deep sleep with LP RTC timer and normal ROM cold boot | GPIO wake and selective retained-memory policy are not implemented. Verify reset reason and persist/JFFS2 health on cold boot |
| USB | DWC2 high-speed host, mass storage, diagnostic s2idle, suspend-to-RAM cold recovery, device-mode overlay and gadget interfaces | Validate enumeration and readback of the attached drive after APPWR recovery; destructive writes require a separate test |
| Watchdogs | Linux watchdog drivers as configured | Reset effects depend on selected watchdog block |
| Normal poweroff | **Experimental**: orderly shutdown reaches the untimed PMU request with RTC wake disabled | Verify lack of automatic restart and recovery by external reset; shutdown current remains unmeasured |
| Advanced Wi-Fi | **Experimental**: AP/AP+STA, receive-only monitor, PEAP/EAP-TLS vendor provisioning | Open same-channel AP+STA has bounded historical traffic evidence. Protected AP, monitor capture and enterprise authentication require separate acceptance; P2P, injection and WoWLAN are absent |
| I2C long messages | **Experimental**: 7/10-bit FIFO continuation and repeated-start combined transfers | Host wire-model coverage reaches 65535 bytes; long-message board readback remains unverified. Validate register/repeated-start/NACK/recovery at each intended rate |
| SPI controller | **Supported within the stated test boundary**: both GPSPI controllers and modes 0–3 | Validate bounded bidirectional transfers and CRCs on both controllers; electrical speed limits depend on the peer and fixture |
| SPI target | **Experimental**: DMA up to 4096 bytes, 8/16/32-bit words and LSB/MSB order | 8-bit target transfers have bounded historical peer evidence; other word sizes, abort and malformed-frame behavior remain unverified |
| Generic I2S | **Experimental**: I2S/left-justified/DSP A/B, TDM masks, MCLK and external cards | The historical fixture boundary is external-master S16_LE stereo at 8/16/48 kHz after synchronization. DMA cache synchronization is implemented; startup samples, external codecs, other formats and endurance remain unverified |
| HIL | Host agent plus optional P4 programmable peer; guarded sequencing and repeat execution | Verify all four physical lanes, IRQs and final release before accepting a changed fixture |

For exact compile-time availability, use the Kconfig reference and active
kernel configuration. For exact runtime availability, inspect the applied
overlays and corresponding Linux subsystem interfaces.
