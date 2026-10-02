# esp32-config

Run `esp32-config` as root on the board's console to open the configuration
menu. Select a setting, edit its current values, then save and apply it.
**Back** leaves the current page; **Finish** closes the tool. Submitted settings
remain saved when you exit.

## Menu

| Page | Settings |
|---|---|
| System | Hostname, login password, date/time, startup program |
| Network | Wi-Fi network, IPv4 address, DNS |
| Bluetooth | Enabled state, device name, saved pairings |
| Interfaces | Peripheral selection, pins, parameters, GPIO, USB function |
| Memory & storage | Swap and a removable storage volume |
| Maintenance | Export, import, reset, full status |

Pages use the drivers and tools installed in the running image. For example,
USB device functions require gadget support, and mounting a volume requires its
filesystem driver. A driver omitted from the image cannot be enabled by a
menu selection. See [Build profiles](../get-started/build-profiles.md).

Routine settings take effect when submitted. Startup-program selections take
effect at the next start of that program. Imported or reset settings are
applied together after restarting Linux. These actions state when a restart
is needed.

## System commands

```text
esp32-config system hostname [NAME]
esp32-config system password
esp32-config system time status|apply|sync
esp32-config system time configure ZONE AUTOMATIC SERVER
esp32-config system time set 'YYYY-MM-DD HH:MM:SS'
esp32-config system autostart status|enable|disable|start|stop
esp32-config system autostart configure EXECUTABLE [ARG ...]
```

`hostname` without `NAME` prompts for a new name. `password` opens the system
password tool for root. For time configuration, `AUTOMATIC` is `0` or `1`.
`EXECUTABLE` is an absolute path; each `ARG` is passed literally.
See [System settings](../user-guides/system-settings.md) for examples and
startup behavior.

## Network commands

```text
esp32-config wifi status|scan|configure|enable|disable|forget
esp32-config wifi connect SSID [psk|open]
esp32-config wifi configure-hex SSID_HEX [psk|open]
esp32-config network status
esp32-config network dhcp [auto|manual [DNS ...]]
esp32-config network static ADDRESS PREFIX GATEWAY_OR_- [DNS ...]
```

Interactive `wifi configure` asks for one SSID and one password, saves the
profile, and connects. `connect` takes the SSID as an argument and reads one
password from the terminal or standard input. `open` skips the password.
`configure-hex` takes the exact SSID bytes encoded as hexadecimal.

Protected profiles accept an 8–63-byte password or a 64-digit hexadecimal PSK.
The derived key is saved; the plaintext passphrase is not retained. For a protected
network whose SSID contains a zero byte, use `configure-hex` and a precomputed
PSK. Open networks with such an SSID need only `configure-hex`.

For existing automation, noninteractive `wifi configure` retains its three-line
input contract: SSID, password, matching password. That compatibility path only
saves the profile. New scripts can use `wifi connect`, with one password line
on standard input, for save-and-connect behavior.

A connection action returns `0` when connected, `1` on an apply failure, or `2`
when the bounded wait ends with connection work still pending. Check
`wifi status` before retrying. The connection workers continue after a pending
result. Usage errors also return a nonzero status.

Address commands accept IPv4 addresses and up to three DNS servers. Use `-`
for no gateway. Address settings reconnect enabled Wi-Fi; if Wi-Fi is off,
they are saved for the next connection. See
[Wi-Fi and Bluetooth setup](../user-guides/networking.md).

## Bluetooth commands

```text
esp32-config bluetooth info|status|enable|disable|restart
esp32-config bluetooth name [NAME]
esp32-config bluetooth clear-pairings
```

`name` without a value prints the saved name. Names contain 1–29 bytes and no
control characters. The default is `S31 Radio`. Changing an enabled device's
name restarts Bluetooth. `clear-pairings` clears the current controller's
Classic and BLE keys and restarts its running service.

Enabled Bluetooth provides Classic A2DP transport and a BLE peripheral.
The bundled application does not decode audio for PCM playback. The legacy
`bluetooth scan` command still reports that scanning is unsupported; there is
no scanning item in the menu.

Changing the Wi-Fi/Bluetooth enabled combination reloads their shared radio.
Setting an unchanged enabled state does nothing; use `apply wifi` or
`bluetooth restart` for recovery. See the
[network guide](../user-guides/networking.md) for pairing and service details.

## Interfaces and GPIO

```text
esp32-config overlay COMMAND [ARG ...]
esp32-config gpio list|status|apply|reset
esp32-config gpio set LINE application|low|high
esp32-config gpio set LINE input [none|up|down]
esp32-config gpio read LINE
```

`overlay` forwards arguments to [s31-overlay](overlay-catalog.md), including
`--volatile`. The interface page reads default, current, and saved settings
separately. Fixed pins are displayed without an editable GPIO field.

GPIO settings apply immediately, remain held after the menu exits, and are
restored by the Linux startup service. `application` releases the line and
removes its saved assignment. `reset` releases all GPIOs owned by the tool
and clears their saved assignments. `read` reads a managed input; for a managed
output it reports the configured level. For usage and ownership, see
[Use peripherals](../user-guides/peripherals.md).

The existing diagnostic commands remain available from the CLI:

```text
esp32-config gpio info [CHIP]
esp32-config gpio get CHIP LINE
esp32-config gpio pulse CHIP LINE VALUE [SECONDS]
```

`pulse` is a temporary output for 1–30 seconds, defaulting to 3 seconds. It does
not create a saved assignment and is not part of the configuration menu.

## Memory, storage, and USB

```text
esp32-config storage status
esp32-config storage swap status|disable|apply|stop
esp32-config storage swap enable DEVICE
esp32-config storage configure DEVICE PATH AUTOSTART READONLY
esp32-config storage mount|unmount
esp32-config storage autostart 0|1
esp32-config usb status|apply|stop
esp32-config usb configure MODE [SERIAL_LOGIN [IP/PREFIX]]
```

Storage commands select an existing swap device or filesystem; they do not
format it. Devices may be `/dev/...` paths or `UUID=...` identifiers.
`AUTOSTART` and `READONLY` are `0` or `1`. The mount path is an empty directory
under `/mnt` or `/media`. See [Memory and storage](../user-guides/memory-and-storage.md).

USB `MODE` is `host`, `serial`, or `network`. `SERIAL_LOGIN` is `0` for an
application serial port or `1` for a Linux login console. The network mode
uses ECM and defaults to board address `192.168.7.2/24`. See
[USB functions](../user-guides/usb-gadget.md) for host setup and role changes.

## Apply settings and manage backups

```text
esp32-config status
esp32-config apply [all|system|wifi|bluetooth|gpio|storage|usb]
esp32-config stop
esp32-config maintenance backup PATH.tar
esp32-config maintenance restore PATH.tar
esp32-config maintenance reset network|bluetooth|interfaces|gpio|system|memory|all
```

`apply` defaults to `all`. It reapplies system, radio, GPIO, USB, and storage
settings. It does not launch the startup program or replace the active overlay
set. `apply system` applies the hostname and time settings. `stop` stops the
managed Wi-Fi connection while retaining its saved policy.

Backups cover settings managed by `esp32-config`. Import and reset preserve
user programs, login passwords, and Bluetooth pairing keys. Restart Linux to
apply imported or reset settings. See [Configuration](configuration.md) for
backup examples, persistence, and recovery.

## Persistent files

| File under `/etc/esp32-conf` | Contents |
|---|---|
| `system.conf` | Hostname |
| `wifi.conf` | Wi-Fi enabled state, interface, SSID identifier, IPv4/DNS policy |
| `wpa_supplicant.conf` | Saved station profile |
| `bluetooth.conf` | Enabled state, controller selection, BLE policy, device name |
| `overlays.conf` | Saved peripheral selections and parameters |
| `gpio.conf` | Managed GPIO assignments |
| `time.conf` | Time zone, automatic-time selection, time server |
| `autostart.conf`, `autostart.args` | Startup program and literal arguments |
| `swap.conf` | Swap selection and startup policy |
| `storage.conf` | Selected volume, mount path, access, startup policy |
| `usb.conf` | USB mode, serial login selection, network address, device identity |

The configuration directory uses mode 0700; settings files use mode 0600.
Login passwords are managed separately by the system password tool. Runtime
state is stored under `/run/esp32-config` and is cleared at reboot.

The frontend is `buildroot-external/board/esp32-s31/overlay/usr/sbin/esp32-config`.
Its settings modules are under the adjacent `usr/lib/esp32-config` directory.
