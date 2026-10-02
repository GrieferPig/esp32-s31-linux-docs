# Wi-Fi and Bluetooth

The ESP32-S31 radio module provides a cfg80211 Wi-Fi interface and a Bluetooth
controller. For configuration, pairing, service controls, and connection checks,
use [Wi-Fi and Bluetooth setup](../../user-guides/networking.md). This page
covers application interfaces and module parameters.

## Wi-Fi

The network interface is normally `wlan0`; the image includes `iw`,
`wpa_supplicant`, and `wpa_cli`. Application data uses normal network sockets.
[Advanced Wi-Fi](../../api-guides/wifi-advanced.md) covers monitor reception and
the AP/enterprise integration paths. The [EAP vendor protocol](wifi-protocol.md)
defines credential provisioning for firmware-owned enterprise authentication.

## Bluetooth

The bundled BTstack application uses `/dev/s31-hci`. Loading the module with
`direct_hci=0` instead exposes a Linux HCI controller. A BlueZ-based image also
needs its daemon, tools, dependencies, and service configuration retained:
`post-build.sh` explicitly removes BlueZ, D-Bus/GLib, and BlueALSA files. Selecting
the package alone is insufficient. See the [runtime pruning
rules](runtime-pruning) when building
that alternative, and stop the direct-HCI service before changing ownership.

### Direct HCI device

`/dev/s31-hci` allows one application to open it at a time and has permissions
`0600`. Stop BTstack before using the device from another application.

A write sends one complete H4 packet: a packet-type byte followed by the HCI
packet data. The accepted write size is 2–1,029 bytes.

The size passed to `read()` selects the receive format:

| Requested read size | Returned data |
|---|---|
| 2–1,029 bytes | One complete H4 frame |
| More than 1,029 bytes | Up to eight frames, each preceded by a two-byte little-endian length |

For a simple client, use a 1,029-byte read buffer. In batch mode, each length
includes the H4 packet-type byte. The read finishes when the buffer fills,
eight frames have been copied, or the queue becomes empty.

A buffer too small for the next frame returns `EMSGSIZE` if no frame has been
copied yet. A nonblocking read from an empty queue returns `EAGAIN`. Use
`poll()` to wait for incoming data or space in the transmit queue.

After a controller restart, an open client can receive an HCI Hardware Error
event. Reinitialize the host and reconnect devices when that happens. Closing
the device releases the host endpoint while leaving the controller enabled.
The [HCI frontend](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/bluetooth/hci_esp32s31.c) implements this framing and lifecycle.

## Module settings

The module file is `esp32s31-radio.ko`. Linux shows its name as
`esp32s31_radio` in `/sys/module`.

| Parameter | Default | Description |
|---|---|---|
| `mode` | `combo` | Enable `wifi`, `bt`, or `combo` |
| `direct_hci` | `1` | Expose `/dev/s31-hci`; use `0` for Linux HCI |
| `firmware` | `esp32s31-radio-fw-v1.o` | Radio firmware filename |

These settings are selected when loading the module. Use `esp32-config` for
routine mode selection; low-level applications should stop clients before
changing the module configuration. The [module implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c) defines the mode and direct-HCI defaults.

(radio-status)=
## Radio status

The `radio_health` attribute reports initialization results, heap use, packet
counts, and worker activity:

```sh
for file in /sys/bus/platform/devices/*/radio_health; do
    [ -r "$file" ] && cat "$file"
done
```

Use this together with `dmesg` when a radio service fails to start or stops
making progress.

## Kernel interface

The common radio API is declared in
[`include/linux/esp32s31-radio.h`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/esp32s31-radio.h).
It defines the Wi-Fi and HCI callbacks used by the frontends. The core and
external payload currently use ABI version 1.

| Item | Limit |
|---|---:|
| HCI frame | 1,029 bytes |
| Wi-Fi Ethernet frame | 1,600 bytes |
| Scan results | 32 access points |

The station receive-copy callback can run in hard-IRQ context and uses
preallocated buffers. A separate callback schedules packet processing.
Monitor traffic uses its own receive path.

```{toctree}
:maxdepth: 1

architecture
wifi-protocol
```
