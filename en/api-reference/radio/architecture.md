# Radio architecture

Wi-Fi and Bluetooth share the `esp32s31-radio` Linux module. It contains their
Linux frontends, the external-firmware loader, and the runtime used by
Espressif's radio code.

| Application path | Frontend in the common module |
|---|---|
| Wi-Fi applications using sockets | cfg80211 and netdev |
| Bundled BTstack application | `/dev/s31-hci` direct H4 device |
| Alternative Linux Bluetooth host | Linux HCI controller with `direct_hci=0` |

All three paths reach the same radio runtime and external firmware. See the
[radio interface reference](index.md) for framing, ownership, and module settings.

## Firmware loading

ESP-IDF libraries and the port's compatibility code are linked into
`esp32s31-radio-fw-v1.o`, a relocatable RISC-V ELF object. The build packages it
with the matching module in `radio.sqfs`.

During startup, the [loader](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-loader.c)
allocates firmware memory, resolves imports, applies relocations, and finds
exported entry points. It checks the payload format and ABI before starting the
runtime. Use the firmware and module from the same build: a matching ABI number
alone does not establish compatibility of every private import.

Loaded firmware memory, including mutable sections, is separate from the fixed
internal-SRAM pools used by the runtime. The [allocation helper](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-loader-core.c)
and [Memory map](../../hw-reference/memory-map.md) describe these two allocations.

## Runtime and CPU placement

The main radio worker and hardware interrupt handling run on HP core 0.
Wi-Fi's frontend schedules receive NAPI and buffer-refill work on HP core 1.
The [Wi-Fi receive path](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c)
uses that split to process received packets alongside the radio runtime.

The compatibility layer provides the tasks, queues, timers, and synchronization
functions expected by the radio libraries. Its [task creation
adapter](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-rtos.c)
honors a valid requested core when binding a task's Linux kthread; the main
worker's CPU0 placement is not a rule that every payload-created task is bound
to CPU0.

Callbacks running in interrupt context copy data into preallocated storage and
schedule further work. Applications use their networking or Bluetooth interface
without calling the firmware directly.

## Suspend and recovery

On suspend, the module detaches its frontends, stops the runtime, and releases
its power request. On resume, it restores the firmware's initial mutable data,
restarts the runtime, and restores the frontends. If restart fails, it leaves
the interfaces detached and logs the error. This sequence is implemented in the
[module's power-management callbacks](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c).

The Wi-Fi frontend restores its cached EAP fields, active AP configuration, and
running monitor interface. Station connections need userspace reconnection. The
Bluetooth frontend reports the controller reset to an open direct-HCI client,
and the bundled BTstack reset handler restarts its HCI state machine. Existing
wireless connections still need to be established again with the peer.

For connection checks and service controls, see
[Wi-Fi and Bluetooth setup](../../user-guides/networking.md). System sleep
availability is described in [Power management](../../api-guides/power-management.md).
For code changes, see [Radio firmware development](../../api-guides/radio-payload-development.md).
