# Radio Subsystem

## Execution domain

- The radio bundle contains one `esp32s31-radio.ko` plus the external,
  versioned `esp32s31-radio-fw-v1.o` ESP-IDF closure. The module owns
  coexistence, PHY, clocks, interrupts, the compatibility runtime, SRAM heap,
  cfg80211 and direct H4. The closure is loaded and relocated at runtime; it
  is not statically linked into the module.
- The base device tree has separate disabled `wifi` and `bluetooth` child
  nodes. The `radio-wifi`, `radio-bluetooth`, and `radio-combo` overlays enable
  the requested hardware description. The module's `mode=wifi|bt|combo`
  parameter selects which Linux frontends and controller paths start.
- OpenSBI does not execute radio closure entry points and does not own radio
  interrupts or radio task scheduling.
- Linux enters the closure through the single `s31-radio` execution queue and
  manages CLIC sources, wakeups, and context only at that boundary.

## Scheduling behavior

- All closure requests execute serially through one channel.
- A scheduling pass may process deferred ISRs, compatibility RTOS ticks,
  closure tasks, HCI work, and cfg80211 adapter work.
- Linux saves and restores local-interrupt state around closure execution. It
  also preserves floating-point state when the selected closure can use it;
  the Bluetooth-only path skips that work, while Wi-Fi and combined profiles
  retain the full save/restore boundary. After a pass completes, execution
  returns to a standard Linux context before sleeping.
- The loader resolves only a generated allowlist of compatibility imports and
  verifies the payload ABI before execution. Callers cannot bypass the queue
  and invoke internal payload functions directly.

## API and state

- `include/linux/esp32s31-radio.h` exports typed APIs only and does not expose
  raw function-pointer entry points.
- `esp32s31_radio_get_health()` reports initialization state, tick/pass counts,
  and SRAM heap usage.
- Bluetooth traffic uses bounded H4 RX/TX rings. RX writes occur during the
  controlled pass; VHCI consumes TX data in a later pass. Both Bluetooth-only
  and combined profiles expose `/dev/s31-hci` directly to the sole BTstack
  process; BlueZ and Linux Bluetooth sockets do not share ownership.
- A read buffer larger than one maximum HCI frame enables the private direct-H4
  batch ABI. One read returns up to eight little-endian length-prefixed frames;
  it never waits to fill a batch, and consumes each SRAM slot only after a
  successful userspace copy.
- Linux exposes standard cfg80211/nl80211 for Wi-Fi and the private direct-H4
  character device for Bluetooth; the module mode determines which frontend
  is registered.

## Memory and interrupts

- The loader places payload code/data/BSS in an executable kernel arena. The
  arena is allocated on first use and kept at the same virtual address until
  reboot, even while `esp32s31-radio.ko` is unloaded. Some private ESP-IDF
  process-lifetime callback objects retain code addresses across controller
  shutdown, so moving the payload on a later load is unsafe. Each reload
  overwrites and relocates the pristine external ELF into that retained arena;
  module state, frontends, tasks, IRQs, rings, and the radio heap are still
  released. Radio heap, rings, and the synchronous-exception stack continue to
  use their dedicated internal-SRAM carve-out.
- The heap is managed by a Linux `gen_pool` and is not placed in PSRAM.
- Dedicated radio interrupts are managed through CLIC and irqdomain. The radio
  adapter does not bypass the Linux interrupt domain.
- Production timing diagnostics are disabled by default. Their fixed sample
  rings retain one opt-in sample instead of reserving several KiB of dormant
  BSS. The module's measured `.bss` is 26,652 bytes.
- Radio and Linux-device internal-SRAM carve-outs are listed in
  [Memory and DMA](memory-and-dma.md).

## Policy boundary

- Wi-Fi and Bluetooth are disabled by default. A user must explicitly enable a
  backend before it becomes active.
- `esp32-config` persists userspace radio policy. Driver shutdown paths do not
  rewrite policy files.
- Profile changes do not require a reboot. After Wi-Fi and BTstack users have
  stopped, `S00s31-radio restart` unloads the module and reloads it with the
  new mode. A busy module is left loaded and the change reports an error.
- The compact root filesystem provides WPA2 station operation and one BTstack
  host process for Classic A2DP/AVRCP plus BLE. BlueZ, D-Bus, GLib, BlueALSA,
  and the legacy pairing agent are neither selected nor retained.
- The controller remains in BTDM mode. The BTstack process advertises `S31
  Radio` and serves `0xff10/0xff11`; a Windows BLE client repeatedly connected
  and read `ready` while Wi-Fi remained associated and transferred an exact
  payload. The compact host does not implement BLE scanning or a general GATT
  client.
- The default A2DP mode receives and counts compressed SBC frames without PCM
  rendering. `S31_BTSTACK_DECODE_SBC=1` enables decoder-path diagnostics, but
  there is no BTstack-to-ALSA/I2S PCM backend in this image.
- The transport-only sink therefore has no PCM queue that can report an audio
  overrun or underrun.  It instead tracks every AVDTP RTP sequence number and
  periodically reports forward gaps, duplicates, and reordered media packets.
  The kernel health record independently exposes the bounded Wi-Fi and HCI RX/TX
  ring-drop counters; a zero ring-drop delta distinguishes controller/airtime
  loss from a Linux queue overrun.  Audible-output xrun claims require a future
  PCM or I2S backend with its own queue watermark and xrun counters.
- The measured audio profile advertises 44.1 kHz joint-stereo SBC with bitpool
  up to 53, 16 blocks, 8 subbands, and loudness allocation. SBC remains lossy,
  but this matches the high-quality source profile used by the IDF A2DP
  examples more closely than the former bitpool-35 CPU-oriented profile.
- In combined mode BTstack reports A2DP streaming and paused state to the
  matching IDF `libcoexist` status-bit API.  ESP32-S31's native IDF controller
  build disables the optional Bluedroid `0xfc82` vendor command, so the Linux
  module terminates that exact command and performs the same status-bit update
  inside the serialized radio execution domain.  This is an optional Linux host
  compatibility hint, not a claim that the native S31 host sends the VSC;
  setting `S31_BTSTACK_COEX=0` keeps the native S31 BTDM-plus-libcoexist policy
  for controlled comparisons.
- Bluetooth controller modem sleep is enabled with IDF's 100 kHz low-power
  timer derived from the 40 MHz main XTAL. This gates the PHY between radio
  events without placing Linux or external memory into SoC light sleep. The
  project leaves low-power clock initialization to IDF: calling only
  `btdm_lp_set_lpclk_src()` would mark the source as configured without filling
  the controller's cached frequency, causing wake scheduling to use 0 Hz.
- BTDM remains enabled across userspace service restarts. Modem sleep reduced
  the measured paused-link load to 0.035 core, whereas an IDF controller
  disable followed by enable left Classic page-scan state inconsistent and
  asserted in `olc_pscan.c`. Closing the HCI endpoint therefore unregisters and
  purges the host side without cycling controller power.
- During a matching 60-second Windows A2DP playback at bitpool 53, the conservative
  scheduler acceptance result was 0.531 core: 0.268 for `s31-radio`, 0.127 for
  BTDM, and 0.132 for BTstack. Available memory remained between 8,488 and
  8,616 KiB during that sample, BTstack RSS was 648 KiB, and USB swap usage
  remained zero. The same connection continued receiving media for more than
  six minutes without a supervision timeout or host disconnect.
- Classic pairing keys are retained under `/var/lib/btstack` on the persistent
  overlay.
- On the lean boot, one-shot DHCP leaves no resident `udhcpc`; after an
  exact payload transfer, settling, and cache reclamation, `MemAvailable` was
  8,228 KiB. A 20-second idle sample with
  Wi-Fi associated and BLE/A2DP service ready reported 0.114 core by the
  conservative acceptance metric. The final external-payload/reload build was
  also paired to Windows and completed A2DP plus four consecutive 4 MiB Wi-Fi
  downloads in 6/5/5/6 seconds. A 60-second active-radio stress run completed
  with 19 passes, no failures, 5,685 additional Wi-Fi packets, 8,215 cumulative
  Bluetooth ACL RX packets, zero change in all four ring-drop counters, and no
  new kernel fault signature.
- A stricter Windows A2DP coexistence comparison used four complete 4,625,804
  byte kernel-image downloads over the associated `wlan0` link.  With the Linux
  A2DP status hint enabled, repeated 63--67 second runs completed every download,
  increased Bluetooth ACL RX by thousands of packets, and kept all four kernel
  ring-drop counters unchanged.  The RTP tracker nevertheless saw 19 and 29
  missing media packets by its 4096-packet report.  With the hint disabled, the
  same load saw 34 missing packets by 4096 and 78 before the following stream
  boundary.  No duplicates or reordered packets, kernel fault, or host ring
  overrun occurred.  The remaining defect is therefore BR/EDR controller or
  shared-airtime loss under concurrent Wi-Fi load, not exhaustion of a Linux
  HCI queue.
