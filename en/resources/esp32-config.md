# esp32-config

`esp32-config` provides an interactive `dialog` menu and command-line controls.
Persistent configuration lives in `/etc/esp32-conf` on the writable OverlayFS
upper layer. Mutating operations require root.

## Commands

```text
esp32-config
esp32-config status
esp32-config apply [all|system|wifi|bluetooth]
esp32-config stop
esp32-config system hostname [NAME]
esp32-config wifi status|scan|configure|enable|disable
esp32-config bluetooth info|scan|enable|disable
esp32-config overlay COMMAND [ARG ...]
esp32-config gpio info [CHIP]
esp32-config gpio get CHIP LINE
esp32-config gpio pulse CHIP LINE VALUE [SECONDS]
```

Use `wifi configure` to enter an SSID and password interactively. Credentials
belong on the board, not in command examples or repository files. `enable` and
`disable` save service policy and apply the required radio mode. Changing radio
mode can disconnect existing Wi-Fi/Bluetooth users. `stop` stops Wi-Fi activity;
use explicit service disable commands to change saved policy.

`system hostname` reports the current name; supplying a name saves and applies
it. `overlay` forwards to [s31-overlay](cli-reference.md), including its
`--volatile` policy. `gpio pulse` drives a temporary output for at most
30 seconds and never saves a boot-time output selection. Identify the actual
chip and line before using an output command.

## Persistent files

| File under `/etc/esp32-conf` | Owner and meaning |
|---|---|
| `system.conf` | `hostname` policy |
| `wifi.conf` | Wi-Fi service policy, `enabled=0/1`, `interface` (normally `wlan0`), and `dhcp=0/1` |
| `bluetooth.conf` | Bluetooth service policy, including `enabled`, `index`, and `le` |
| `wpa_supplicant.conf` | Personal/open station profile managed by configuration tools |
| `overlays.conf` | Desired overlay selections managed by `s31-overlay` |

Prefer the tool to hand editing files. It creates the configuration directory
with mode 0700 and protects configuration files. A writable persistent layer
is required to save settings; a successful temporary hardware operation does
not prove that its saved policy was written.

## Boot and recovery

On startup, `/init` mounts JFFS2, constructs the root OverlayFS, restores saved overlays,
then starts the selected radio before BusyBox init launches the remaining
services. Radio startup checks the bound device and requested local frontend. Wi-Fi association and
Bluetooth connections are established by their respective userspace services.

The implementations are in
`buildroot-external/board/esp32-s31/overlay/usr/sbin/esp32-config`,
`overlay/init`, and `overlay/etc/init.d/S00s31-radio`. See the [userspace reference](../api-reference/userspace/index.md)
for overlay persistence and failure semantics.
