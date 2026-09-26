# Radio architecture

Wi-Fi and Bluetooth share the `esp32s31-radio` Linux module. It contains the
Linux frontends, firmware loader, and runtime used by Espressif's radio code.

```text
Wi-Fi applications                 Bluetooth applications
       |                                   |
  cfg80211/netdev                  BTstack or Linux HCI
       |                                   |
       +---------- Linux radio module -----+
                            |
                  Radio runtime and loader
                            |
                  External radio firmware
```

## Linux frontends

The Wi-Fi frontend connects the radio to Linux networking through cfg80211
and a network device. The Bluetooth frontend offers either the direct
`/dev/s31-hci` device or a Linux HCI controller.

Both frontends use the common radio API. They are built into the same module
and share its startup, shutdown, and error handling.

## Firmware loading

The radio firmware is built from ESP-IDF libraries and the port's compatibility
code. It is packaged as `esp32s31-radio-fw-v1.o`, a relocatable RISC-V ELF
object, and stored with the radio module in `radio.sqfs`.

During startup, the loader allocates memory for the firmware, resolves its
imports, applies relocations, and finds the exported entry points. It checks
the payload format and ABI before starting the runtime. Firmware should come
from the same project build as the module.

The executable firmware allocation is separate from the fixed internal-SRAM
pools used by the radio. See [Memory map](../../hw-reference/memory-map.md) for
those reservations.

## Runtime

Radio work and device interrupts run on HP core 0. The compatibility layer
provides the task, queue, timer, and synchronization functions expected by the
radio libraries. Wi-Fi receive processing also uses Linux workqueues and NAPI.

Callbacks that run in interrupt context copy data into preallocated storage
and schedule further work. Applications continue to use the normal Linux
network and Bluetooth interfaces.

## Suspend and recovery

On suspend, the module detaches its frontends, stops the runtime, and releases
its power request. On resume, it restores the firmware's initial mutable data,
restarts the runtime, and attaches the frontends again.

Wireless services reconnect after this restart. If startup fails, the
interfaces stay detached and the error is written to the kernel log. System
sleep availability is described in [Power management](../../api-guides/power-management.md).

For changes to the firmware itself, see
[Radio firmware development](../../api-guides/radio-payload-development.md).
