# Advanced Wi-Fi

In addition to station mode, the Wi-Fi driver provides an access-point
interface, monitor reception, and enterprise credential provisioning. Station,
AP, and monitor interfaces share one 2.4 GHz channel, with up to one interface
of each type.

For ordinary station setup, use `esp32-config` and the
[radio guide](../api-reference/radio/index.md).

## Monitor reception

Create a monitor interface and bring it up:

```sh
iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
iw dev mon0 set channel 6 HT20
```

Choose the channel while the station is disconnected and the AP is stopped.
With an active station or AP, monitor reception uses their channel.

Received packets include a radiotap header with channel and signal information.
The interface supports reception only. To save a capture, add `tcpdump` to the
rootfs and run:

```sh
tcpdump -i mon0 -s 0 -w /tmp/capture.pcap
```

Stop the capture with Ctrl+C, then remove the interface:

```sh
iw dev mon0 del
```

`/tmp` uses RAM, so keep captures small or write them to attached storage.

## Access-point mode

Create an AP interface with:

```sh
iw dev wlan0 interface add ap0 type __ap
ip link set ap0 up
```

An AP manager must then start the access point and configure its IP address,
DHCP service, and routing. This port uses firmware authentication offload:
the AP-start request supplies the WPA2 PSK or WPA3 SAE password. Integration
with a standard hostapd setup still needs testing.

The AP configuration accepts:

| Setting | Values |
|---|---|
| Security | Open, WPA2-PSK, or WPA3-SAE |
| Protected-network cipher | CCMP |
| Channel width | 20 MHz |
| Maximum clients requested from firmware | 4 |
| Beacon interval | 100–60000 TU |
| DTIM period | 1–10 |
| SAE password | 1–63 bytes |

Select one authentication method; mixed WPA2/WPA3 transition mode is currently
unsupported. For AP+station use, start the AP first, then connect the station
on the same channel. Restarting the AP can interrupt the station connection.

## Enterprise credentials

Enterprise authentication runs in the radio firmware. Use
`tools/s31_wifi_eap.py` to provision its identity, CA certificate, server domain,
and user credentials or client certificate.

The helper runs on a computer with Python and sends commands to `iw` locally
or over SSH. To use the remote example below, first add an SSH server to the
board image and set up access. The default image uses the serial console.

### 1. Prepare a profile

For PEAP, create `profile.json`:

```json
{
  "identity": "anonymous@example.invalid",
  "username": "user@example.invalid",
  "password_file": "password.txt",
  "ca_file": "ca.pem",
  "domain": "radius.example.invalid"
}
```

Use the identity, CA, and server domain supplied by your network administrator.
File paths are relative to the JSON file. Password-file contents are used as
written, including a trailing newline. Keep the profile and credential files
private.

For certificate-based authentication, supply both `cert_file` and `key_file`
in place of the username/password pair. The identity, CA, and domain are
required for both forms. Each field can contain up to 4095 bytes, with a
253-byte limit for the domain; embedded NUL bytes are rejected.

### 2. Provision the firmware

Disconnect the station and stop automatic reconnection while changing the
profile. Set the board's clock before certificate-based authentication, then
run on your computer:

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD profile.json
```

Replace `BOARD` with the board's SSH address. The helper clears the old profile,
transfers the fields, and commits the new profile. It sends credentials through
standard input rather than command-line arguments.

### 3. Connect to the network

After provisioning, initiate a station connection to the enterprise SSID using
your station integration. The usual `wpa_supplicant` WPA-EAP settings do not
populate this firmware profile. End-to-end enterprise authentication remains
an integration task; check authentication and IP traffic with your network.

To clear the installed credentials, disconnect first and run:

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD --clear
```

If a transfer fails, restore the connection to the board and clear the profile
before retrying.

### Vendor command format

For tools that implement provisioning directly, use vendor ID `0x18fe34` and
subcommand `0x1`. Each request contains five little-endian 32-bit integers:
operation, field, offset, total length, and chunk length. Up to 512 bytes of
field data follow the header.

Operations are WRITE (`6`), COMMIT (`7`), and CLEAR (`8`). Field IDs 0–6 select
identity, username, password, CA, domain, client certificate, and private key.
Send each field in consecutive chunks and complete every field before COMMIT.
Provisioning is rejected while the station is connected, connecting, or
suspended.

## After suspend

Wireless connections are re-established after the radio restarts. Restart the
AP manager when needed and reconnect the station. See
[Power management](power-management.md) for the available suspend modes and
current limitations.
