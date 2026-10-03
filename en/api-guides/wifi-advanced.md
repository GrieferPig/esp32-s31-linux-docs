# Advanced Wi-Fi

The current image builds the mac80211 SoftMAC frontend, which exposes one
2.4 GHz station interface. Use `esp32-config` for ordinary station setup and
check the connection with `iw`, `wpa_cli`, and `ip`; see the
[radio guide](../api-reference/radio/index.md).

This page distinguishes current frontend limits from interfaces retained in
the underlying firmware. A firmware operation or packaged utility alone does
not establish that the Linux frontend exposes it.

## Inspect the current interface

Run on the board:

```sh
iw dev
iw phy
wpa_cli -p /run/wpa_supplicant -i wlan0 status
```

Use `iw phy` to inspect the capabilities of the kernel you actually booted.
The current driver accepts one station interface and rejects additional
station or AP interfaces.

## Monitor reception

mac80211 can expose a software monitor interface, but the current radio receive
path retains station-oriented filtering, including dropping unrelated unicast
frames. Captures therefore are not a complete promiscuous view of the channel.
Do not use this path to conclude that absent packets were absent over the air.

`tcpdump` is not selected in the compact rootfs. If adding capture tools for
development, keep captures bounded: `/tmp` uses RAM, and persist is only
2120 KiB before filesystem overhead. Use attached storage for larger captures.

## Access-point mode

AP, AP+station, and protected-AP operation are not exposed by the current
SoftMAC frontend. The standard image includes the full board configuration;
installing or running `hostapd` does not add AP support.
The P4/C6 fixture can still provide an external AP for S31 station tests.

## Enterprise authentication

Enterprise authentication needs validation through the current Linux station
stack and the selected `wpa_supplicant` build. Use the CA and server-identity policy supplied by the
network administrator when developing that integration; do not disable server
validation to make a test pass.

## Suspend and recovery

Current SoftMAC has no active-connection replay on resume. Its suspend helper
returns `EBUSY` for a running interface, and the radio module propagates
that error before suspending Bluetooth or stopping the shared payload. Bring
Wi-Fi down before experimenting with system sleep. Automatic radio restart does
not imply successful station reassociation. The HIL `--wifi-suspend-cycles`
option is a diagnostic sequence, not an established recovery capability.
See [Power management](power-management.md) before testing system sleep.
