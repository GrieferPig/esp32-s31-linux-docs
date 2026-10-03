# Wi-Fi and Bluetooth

The ESP32-S31 radio module provides a mac80211/cfg80211 station interface and a Bluetooth
controller. For configuration, pairing, service controls, and connection checks,
use [Wi-Fi and Bluetooth setup](../../user-guides/networking.md). This page
covers application interfaces and module parameters.

## Wi-Fi

The network interface is normally `wlan0`; the image includes `iw`,
`wpa_supplicant`, and `wpa_cli`. Application data uses normal network sockets.
The current SoftMAC frontend exposes one 2.4 GHz station interface. AP and
AP+station operation are unavailable. Software monitor reception is incomplete;
see [Advanced Wi-Fi](../../api-guides/wifi-advanced.md) for filtering and
enterprise-validation limits.

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
The [HCI frontend](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/bluetooth/hci_esp32s31.c) implements this framing and lifecycle.

## Module settings

The module file is `esp32s31-radio.ko`. Linux shows its name as
`esp32s31_radio` in `/sys/module`.

| Parameter | Default | Description |
|---|---|---|
| `mode` | `combo` | Enable `wifi`, `bt`, or `combo` |
| `direct_hci` | `1` | Expose `/dev/s31-hci`; use `0` for Linux HCI |

The payload comes from the fixed `radio.bin` XIP flash slot and must match the
kernel/module; no firmware-filename parameter selects it.

These settings are selected when loading the module. Use `esp32-config` for
routine mode selection; low-level applications should stop clients before
changing the module configuration. The [module implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/platform/esp32s31-radio-module.c) defines the mode and direct-HCI defaults.

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

The common radio API is declared in the current checkout at
`linux-esp32-s31/include/linux/esp32s31-radio.h`.
It defines the Wi-Fi and HCI callbacks used by the frontends. The core and
external payload currently use ABI version 1.

| Item | Limit |
|---|---:|
| HCI frame | 1,029 bytes |
| Radio bridge frame | 4,144 bytes |
| Raw SoftMAC frame | 4,096 bytes |

The raw SoftMAC limit is defined in `include/linux/esp32s31-radio-control.h`.
The retained firmware scan API has a 32-entry array, but current station scans
use mac80211 software scanning; that array is not the current scan-result limit.

The frontend uses `receive_aux` borrowed frames whose storage remains valid
only during the callback. It copies data that must survive callback return and
uses NAPI to deliver frames to mac80211. Atomic allocations can occur in this
path. Generic software monitor reception shares the filtered radio receive
path and is not a complete promiscuous channel capture.

```{toctree}
:maxdepth: 1

architecture
wifi-protocol
```
