# Single Reloadable Radio Module Implementation Plan

## Objective

Use one loadable kernel module with independently selectable Wi-Fi and
Bluetooth frontends, while keeping the private ESP-IDF closure outside the
module:

```text
 radio partition: esp32s31-radio-fw-v1.o (external IDF closure)
                                  |
                     restricted ELF/ABI loader
                                  |
                        esp32s31-radio.ko
             shared runtime, coexistence, PHY, SRAM,
              clocks, interrupts, cfg80211, direct H4
                                  |
                       mode=wifi|bt|combo
```

The device tree retains separate `wifi` and `bluetooth` child nodes, and the
existing overlays remain the hardware-description selectors. Runtime policy
is passed to the single module as `mode=wifi`, `mode=bt`, or `mode=combo`.
After clients stop, the module can be unloaded and reloaded to change mode;
the symmetric shutdown path remains an explicit hardware acceptance gate.

This is a technical packaging and ownership boundary. It does not by itself
resolve redistribution or license compatibility; release source, notices, and
the existing redistribution gate remain mandatory.

## Non-negotiable ownership rules

| Resource | Sole owner | Client access |
| --- | --- | --- |
| IDF compatibility RTOS and task state | radio core | typed request API only |
| Closed Wi-Fi/BTDM/coexistence entry points | radio core | serialized blob gate |
| Coexistence adapter and `libcoexist` state | radio core | Wi-Fi/BT activity votes |
| PHY, modem clocks, resets, PMU vote, and radio IRQ routing | radio core | reference-counted requests |
| Internal-SRAM heap and HCI/Wi-Fi rings | radio core | bounded producer/consumer APIs |
| cfg80211/netdev state | Wi-Fi frontend inside the module | no direct BTDM access |
| HCI/direct-H4 state | BTDM frontend inside the module | no direct Wi-Fi access |

The module and payload must be generated from the same ESP-IDF commit,
resolved `sdkconfig`, generated headers, compiler flags, and firmware ABI. A
mismatched payload must fail before touching hardware. Undefined payload
symbols are resolved only through a generated explicit import table; arbitrary
kernel-symbol lookup is not permitted.

## Workstreams from the performance review

### 1. Batch direct-HCI receive

The first implementation keeps legacy one-frame reads when the supplied buffer
is at most `ESP32S31_RADIO_HCI_FRAME_MAX`. A larger read uses a private batch
ABI containing up to eight records:

```text
u16 frame_length_le
u8  h4_frame[frame_length]
```

The kernel peeks a stable SRAM ring slot, copies it directly to userspace, and
consumes the slot only after a successful copy. It does not wait to fill a
batch, so command and link-state events retain immediate delivery. BTstack
still copies each batch record into its incoming buffer to preserve the
14-byte pre-buffer contract; eliminating that final userspace copy is a later
measured optimization, not an ABI assumption.

### 2. Verify real BR/EDR EDR packet use

Add counters for negotiated ACL packet types, ACL packets and bytes, radio IRQs,
and serialized worker passes. Record whether active A2DP uses `2-DH5` or
`3-DH5`. Change packet-type or link policy only when controller capabilities
and a peer negotiation trace show that the link remained at Basic Rate. Never
advertise a controller capability that the IDF controller does not report.

### 3. Isolated BTstack `-Os` / `-O2` A/B

`BR2_PACKAGE_BTSTACK_S31_OPTIMIZE_O2` changes only the BTstack appliance. The
default remains `-Os`. Compare executable text, resident memory, media CPU,
packet loss, and link stability before selecting `-O2`; test LTO only after the
plain `-O2` result. Do not change the global Buildroot optimization level.

### 4. One module with selectable Wi-Fi and BTDM frontends

The target artifacts are `esp32s31-radio.ko` and external
`esp32s31-radio-fw-v1.o`. Wi-Fi and BTDM coexist only when they share one
compatibility runtime, one internal heap, one PHY owner, and one serialized
execution gate. The selected module mode controls frontend registration; it
does not select a different payload build.

For concurrent A2DP and Wi-Fi, the BTstack process must mirror IDF Bluedroid's
coexistence notification by sending vendor HCI opcode `0xfc82` with Bluetooth
type `2`, SET operation `1`, and A2DP streaming status `0x10`; paused and stop
transitions must update or clear that state. This is enabled only after the
controller acknowledges the command and the combo acceptance test passes.

### 5. BLE in the same BTstack process

Keep the controller in BTDM mode. Add minimum LE GAP advertising and GATT
server support to the same BTstack instance that owns `/dev/s31-hci`; BlueZ
must not be reintroduced and no second host may open the direct HCI endpoint.
The compact image remains a BLE peripheral rather than pretending to provide a
general scanner. A richer GAP/GATT application must be linked into the same
BTstack process.

## Implementation phases

| Phase | Deliverable | Current status |
| --- | --- | --- |
| P0 | Remove BlueZ, BlueALSA, D-Bus agent integration; self-contained direct H4; first batch-read ABI; BTstack optimization switch | Implemented. BTstack has one libc dependency; CI rejects the retired closure. |
| P1 | Move common resource ownership and both typed frontends behind one execution boundary | Implemented as module ABI 3. |
| P2 | Build one `esp32s31-radio.ko`; package a separate versioned IDF payload; update loader and CI | Implemented and verified with the external payload loaded from the radio partition. |
| P3 | Select `wifi`, `bt`, or `combo` at module load and support symmetric unload/reload | Implemented; `wifi -> combo -> wifi -> combo -> bt -> off -> bt -> combo` passed on hardware. |
| P4 | Add EDR/link counters and IDF-equivalent A2DP coexistence signaling | Coexistence signaling and traffic counters are implemented. Capturing a negotiated `2-DH5`/`3-DH5` packet-type event remains open. |
| P5 | Add minimal LE GAP/GATT to the same BTstack process | Implemented as the `S31 Radio` peripheral with service `0xff10` and `ready` characteristic `0xff11`. |
| P6 | Run `-Os`, optional `-O2`, and remove avoidable copies/wakeups | `-Os` remains selected. Batch reads, hot-path trace removal, one-shot DHCP, and lean daemon removal are implemented; current playback needs a fresh host pairing for final remeasurement. |

## Current hardware evidence

- The single-module build boots with the mode derived from persisted Wi-Fi and
  Bluetooth policy. Hardware reload covered `wifi`, `bt`, `combo`, and `off`
  without rebooting, while retaining one stable executable payload address to
  satisfy private ESP-IDF process-lifetime callbacks.
- Wi-Fi associated through `wpa_supplicant`, obtained a DHCP lease, and
  downloaded the 4,621,708-byte `xipImage` with SHA-256
  `336a8394a8d4c413f99d96b5275915f9e2969a35884138ad2c1dd0b97b7f532b`.
- A Windows BLE client found `S31 Radio`, connected, and read `ready`. A
  25-second repeated-read window completed 151 reads with no GATT failures;
  Wi-Fi remained associated, transferred 3,410,040 bytes during that aggressive
  GATT polling window, and completed a separate exact payload download after
  disconnect. All four radio ring-drop counters remained zero.
- After the exact payload transfer, settling, and cache reclamation, the lean
  boot reported 8,228 KiB `MemAvailable`.
  A 20-second associated/service-ready idle sample reported 0.114 core by the
  conservative scheduler metric.
- Windows connected the final build as `A2DP Sink Demo 30:ED:A0:F3:D4:AE` and
  reported `Connected audio`. During playback, four consecutive 4 MiB payloads
  downloaded over Wi-Fi in 6/5/5/6 seconds with exact sizes.
- A further 60-second `--require-radio-traffic` stress run kept A2DP connected
  while eight 4 MiB downloads completed. It reported 19 passes, zero failures,
  5,685 additional Wi-Fi packets, 8,215 cumulative ACL RX packets, zero delta
  in all four Wi-Fi/HCI drop counters, and no new panic, oops, lockup, watchdog,
  MTD, or JFFS2 error.

## Acceptance matrix

| Profile | Required proof |
| --- | --- |
| Wi-Fi only | one module with `mode=wifi`; no HCI endpoint; scan; WPA2 association; DHCP and sustained traffic |
| Bluetooth only | one module with `mode=bt`; no wlan frontend; host pairing; A2DP/AVRCP playback; BLE scan and GATT transaction |
| Combined | one module with `mode=combo`; Wi-Fi remains associated during A2DP and BLE; coexistence state transitions are acknowledged |
| Reload | switch among `combo`, `wifi`, `bt`, and `off` after stopping users; every unload completes; no leaked task, IRQ, frontend, panic, or new ring drop; the documented same-address payload arena remains reserved until reboot |
| Build and release | no BlueZ, D-Bus, GLib, BlueALSA, or legacy agent selection/artifact; module ABI and dependency checks; notices/source bundle gate |
| Performance | 60-second conservative scheduler sample at the selected audio quality, at most 0.8 core, at least 8 MiB available memory, zero unexpected swap growth |

Build success, device registration, Wi-Fi association, Classic pairing/media,
and BLE/GATT are separate results. None may be inferred from another.
