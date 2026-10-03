# Radio architecture

Wi-Fi and Bluetooth share the `esp32s31-radio` Linux module. It contains the
Linux frontends, firmware loader, and runtime used by Espressif's radio code.

```text
Wi-Fi applications                 Bluetooth applications
       |                                   |
  mac80211/cfg80211                BTstack or Linux HCI
       |                                   |
       +---------- Linux radio module -----+
                            |
                  Radio runtime and loader
                            |
                  Prelinked flash-XIP payload
```

## Linux frontends

The current Wi-Fi frontend is a mac80211 implementation, with cfg80211 for
userspace control and one station interface. AP and AP+station operation are
not exposed. mac80211 can provide a software monitor interface, but the radio
receive path still applies station-oriented filtering; see
[Advanced Wi-Fi](../../api-guides/wifi-advanced.md).

The Bluetooth frontend offers either the direct `/dev/s31-hci` device or a
Linux HCI controller. Both frontends use the common radio API and are built
into the same module.

## Firmware loading

The radio firmware combines ESP-IDF libraries and the port's compatibility
code. The host prelinker resolves code/constant relocations against the built
kernel and produces `out/images/radio.bin`. Most radio code executes in place from
its dedicated flash slot; selected Wi-Fi code is copied to internal SRAM.
The compressed Linux module lives in the rootfs under `/usr/lib/s31-radio`.
The relocatable `esp32s31-radio-fw-v1.o` is an intermediate build artifact.

At startup, the loader validates the mapped image's ABI, memory layout, and
header/body CRCs. It copies the internal-SRAM code and initial writable data,
clears BSS, binds module imports, and reads the fixed exports. These checks
reject incompatible layouts and corruption; they do not prove common build
provenance. Build and deploy the kernel, rootfs/module, and radio image as a
matched set.

See [Memory map](../../hw-reference/memory-map.md) for the fixed SRAM
reservations and [Flash layout](../../hw-reference/flash-layout.md) for slots.

## Runtime

Radio device interrupts and the common worker use HP core 0. Compatibility
tasks retain their requested affinity; no-affinity tasks can migrate. SoftMAC
processing also uses HP core 1 when it is available. Wi-Fi-only SoftMAC uses
native task servicing without the common radio worker.

The compatibility layer supplies tasks, queues, timers, and synchronization
for the radio libraries. The current Wi-Fi frontend receives borrowed auxiliary
frames, copies data that must survive the callback before returning, and delivers packets through
NAPI to mac80211. This path can allocate with atomic allocation flags; it is
not an exclusively preallocated receive path.

## Suspend and recovery

The common runtime contains stop/reset/restart support, including restoring
initial mutable firmware data. This does not establish working recovery for
every frontend. Current SoftMAC rejects suspend while its interface is running
and has no active-connection replay implementation. Do not rely on automatic
Wi-Fi, Bluetooth, or combo reconnection after system sleep. The Wi-Fi suspend
HIL sequence is a diagnostic rather than a support guarantee.

See [Power management](../../api-guides/power-management.md) for sleep limits
and [Radio firmware development](../../api-guides/radio-payload-development.md)
for the matched build/deployment workflow.
