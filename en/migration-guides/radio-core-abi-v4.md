# Radio Core ABI Version 4

Core ABI v4 adds interface-specific Wi-Fi data paths, AP station events,
bounded AP/monitor/EAP control requests, and frontend suspend/resume hooks.
Payload ABI v2 adds the corresponding control-task and interface-send exports.
The loader rejects an incompatible payload before starting the runtime.

Rebuild the kernel module and radio payload together with `make linux`, then
build `make radio-fs`, which also rebuilds the root filesystem and packs the
matching module/payload into `radio.sqfs`. Deploy the kernel, root filesystem
and radio filesystem together. Keep `S31_LEAN_RADIO=0` across these commands
when optional peripherals are needed; the default lean profile removes them.
The installed payload retains the historical filename
`esp32s31-radio-fw-v1.o`; the filename is not its ABI version. Compatibility is
checked against the version exported inside the ELF payload.

Resume restores pristine relocated writable firmware sections, creates a new
runtime, replays the cached Wi-Fi configuration and resets the HCI host state.
Wi-Fi and Bluetooth connections are re-established; old association state,
encryption sequence counters and controller connection handles are discarded.
Userspace reconnection policy remains necessary. Raw EAP vendor configuration
is described in the [advanced Wi-Fi guide](../api-guides/wifi-advanced.md).

These new paths are experimental and require board validation. ABI v3 notes
remain available as historical migration documentation.
