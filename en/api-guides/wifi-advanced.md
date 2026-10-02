# Advanced Wi-Fi

The driver exposes station, access-point, and monitor interfaces, with up to one
of each type sharing one 2.4 GHz channel. For ordinary open or PSK station setup, follow
[Wi-Fi and Bluetooth setup](../user-guides/networking.md).

Monitor reception has a direct `iw` workflow. AP authentication and enterprise
association require additional integration beyond the normal configuration
wizard; the boundaries are described below.

## Monitor reception

With the Wi-Fi radio loaded, stop the managed station connection on the board:

```sh
esp32-config stop
```

Also stop any AP manager before selecting a channel. Create a receive-only
monitor interface:

```sh
iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
iw dev mon0 set channel 6 HT20
```

The channel command requires the station to be disconnected and the AP to be
stopped. With an active station or AP, monitor reception uses their channel.
Received packets include a radiotap header with channel and signal information.
Packet injection is unsupported.

To save a capture, first [add `tcpdump` to the image](adding-a-userspace-tool.md),
then run on the board:

```sh
tcpdump -i mon0 -s 0 -w /tmp/capture.pcap
```

Keep the capture small because `/tmp` uses RAM, or select a file on mounted
external storage. Stop the capture with Ctrl+C, remove the interface, and
restart the saved station connection if wanted:

```sh
iw dev mon0 del
esp32-config apply wifi
```

## Access-point integration

These board commands create an AP interface:

```sh
iw dev wlan0 interface add ap0 type __ap
ip link set ap0 up
```

An AP manager must then start the access point and configure the IP address,
DHCP server, and routing. The image selects `hostapd`, but this port's driver
expects the AP-start request to carry the WPA2 PSK or WPA3 SAE password for
firmware authentication offload. A complete working `hostapd` configuration for
that path has not been established here. Creating `ap0` alone does not start
an access point.

The [driver](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c#L702-L750) validates the following settings and requests at most four clients
from firmware:

| Setting | Accepted value |
|---|---|
| Security | Open, WPA2-PSK, or WPA3-SAE |
| Protected-network cipher | CCMP |
| Channel width | 20 MHz |
| Maximum clients requested from firmware | 4 |
| Beacon interval | 100–60000 TU |
| DTIM period | 1–10 |
| SAE password | 1–63 bytes |

These are software limits; acceptance of every extreme by the firmware and
connected clients needs integration testing. Select one authentication method;
mixed WPA2/WPA3 transition mode is unsupported. For AP+station use, start the AP
first and connect the station on the same channel. AP reconfiguration stops and
restarts Wi-Fi in the firmware, which can interrupt the station.

## Enterprise credential provisioning

The firmware implements PEAP and EAP-TLS authentication. The host helper
[tools/s31_wifi_eap.py](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/s31_wifi_eap.py) provisions its identity, CA certificate, server domain,
and user credentials or client certificate. Provisioning installs credentials;
it does not associate with an SSID or obtain an IP address.

### 1. Prepare the host profile

For PEAP, create `profile.json` on your computer:

```json
{
  "identity": "anonymous@example.invalid",
  "username": "user@example.invalid",
  "password_file": "password.txt",
  "ca_file": "ca.pem",
  "domain": "radius.example.invalid"
}
```

Use your network administrator's identity, CA, and server domain. File paths are
relative to the JSON file. Password-file contents are used as written, including
any trailing newline. Keep these files private.

For EAP-TLS, replace the username/password pair with `cert_file` and `key_file`.
Identity, CA, and domain are required in both modes. Each field is limited to
4095 bytes, and the domain to 253 bytes; the helper rejects embedded NUL bytes.

### 2. Prepare access and provision

The helper sends binary input to `iw` locally or through SSH. The following host
example requires an SSH server added to the board image and working access to
it; the default image provides a serial console and has no SSH server. For
local execution on the board, Python must also be added to the image.

Disconnect the station and stop automatic reconnection before changing its
credentials. For a connection managed by `esp32-config`, run `esp32-config stop`
on the board. Use a separate access path if stopping Wi-Fi would close your SSH
connection. Set the board clock correctly before either PEAP or EAP-TLS
authentication: firmware enables [certificate time checks](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/radio_stack.c#L1426-L1444) in both modes.

With `BOARD` replaced by the reachable SSH address, run on the computer:

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD profile.json
```

The helper clears the old profile, transfers the fields, and commits the new
profile. Credential data travels through standard input, not command-line
arguments. To clear it after disconnecting the station:

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD --clear
```

A failed transfer triggers an attempted clear. If access to the board was lost,
restore access and clear the profile before retrying.

### 3. Integrate association

The remaining step is a station manager that submits the enterprise SSID through
the driver's connect path after provisioning. Ordinary `wpa_supplicant` WPA-EAP
settings do not populate this firmware profile, and the `esp32-config` setup page writes open or PSK profiles. This guide does not provide an integrated enterprise-connect command.
Validate association, certificate checks, and IP traffic with the intended
network when adding that integration.

The [EAP vendor protocol](../api-reference/radio/wifi-protocol.md) documents the
packet format for another provisioning client.

## After suspend

On resume, the driver attempts to restore the saved in-memory EAP fields, active
AP configuration, and running monitor interface. The station receives a
disconnection notification and relies on userspace to reconnect. Check service
status and network traffic afterwards; restarting the radio does not guarantee
that the peer reconnects. See [Power management](power-management.md) for the
current system-sleep limits.
