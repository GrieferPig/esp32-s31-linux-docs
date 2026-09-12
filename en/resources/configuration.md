# Configuration Model

Configuration is split across build time, boot time, and runtime. A setting
must be documented at the layer that owns it.

| Layer | Source | Examples |
|---|---|---|
| Build | Make variables, Kconfig, Buildroot config | ISA, enabled drivers, rootfs profile |
| Image layout | `configs/esp32s31-layout.cfg` | Flash offsets and artifact names |
| Boot | FIT, DTB, kernel command line | XIP address, console, root filesystem |
| Hardware selection | Device-tree overlays | Peripheral instance, route, pins, parameters |
| Module load | Module parameters | Radio firmware, mode, direct HCI |
| Runtime | sysfs, `/dev/s31-overlay`, standard Linux APIs | PM policy, remoteproc, overlay state |
| Persistent policy | `esp32-config` data | Enabled services and boot-time selections |

## Precedence

A runtime setting cannot enable hardware omitted by Kconfig or the device
tree. An overlay cannot override a resource owned by an active overlay. Module
parameters are interpreted only when the corresponding module loads.
Persistent policy is applied by early userspace after the base kernel and root
filesystem are available.

## Secrets

Wireless credentials and device-specific identity are runtime data. They must
not appear in defconfig files, overlays, example output, documentation, Git
history, or release metadata. Examples use descriptive placeholders.

## Source of truth

Generated tables in this guide are convenience indexes. Kconfig, YAML binding
schemas, shared ABI headers, the flash-layout configuration, and the actual
tool usage strings remain authoritative for accepted values.

See [esp32-config](esp32-config.md) for commands, persistent files and recovery.
