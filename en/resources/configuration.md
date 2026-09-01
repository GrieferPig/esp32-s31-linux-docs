# System Configuration

`esp32-config` is the persistent-policy entry point for the compact root
filesystem. It manages policy storage, menu organization, backend dispatch,
and boot restoration. It does not replace standard Linux networking, radio,
GPIO, or bus ABIs.

## Interface behavior

- The interactive frontend uses `dialog`.
- Menus are grouped into system, Wi-Fi, Bluetooth, hardware interfaces, GPIO
  diagnostics, and status.
- The serial interface emits only control characters that render reliably on
  the console.
- A successful policy change is applied immediately and persisted through an
  atomic file replacement.

## Storage format

- The configuration root is `/etc/esp32-conf`.
- Policy files use a data-only `key=value` format and are not executed as shell
  scripts.
- Writes use a temporary file in the same directory followed by an atomic
  rename, so readers never observe a partially written state.
- Wi-Fi stores only the derived PSK and does not retain a reversible plaintext
  passphrase.
- Wi-Fi and Bluetooth are disabled by default and require explicit enablement.

| File | Contents |
| --- | --- |
| `system.conf` | Hostname and system properties |
| `wifi.conf` | Interface enablement and DHCP policy |
| `wpa_supplicant.conf` | WPA2 network profile and derived PSK |
| `bluetooth.conf` | Controller enablement; BLE is kept on with BTDM |
| `overlays.conf` | Persistent device-tree overlay set |

## Backends

| Function | Backend |
| --- | --- |
| Wi-Fi | `iw`, `wpa_supplicant`, `wpa_cli`, `ip`, `udhcpc` |
| Bluetooth | BTstack A2DP/BLE service and `rfkill` |
| GPIO | libgpiod and the GPIO character-device ABI |
| I2C | `i2c-tools` and device-tree overlays |
| CAN | `ip`, `can-utils`, and SocketCAN |
| Port and device orchestration | `s31-overlay` |

## Boot restoration

- Early boot scripts read policy from the merged root and restore radio
  switches and the overlay set.
- A disabled policy keeps the backend in a controlled off state and does not
  initiate scanning or radio startup.
- An invalid or conflicting overlay does not replace a working instance. If a
  dynamic replacement fails, the previous instance is restored.
- GPIO output levels are not persistent policy. Line-ownership rules release
  them when the owning application exits.

The selected compact-image Bluetooth backend keeps BTDM and BLE enabled. The
single BTstack process provides Classic A2DP/AVRCP and a minimal BLE GATT
peripheral. A legacy `le=0` value is normalized to `le=1` when Bluetooth is
enabled because the two roles share one BTDM host. It does not enable a BLE
scanner. Bluetooth pairing keys are stored under `/var/lib/btstack` on the
persistent overlay.
