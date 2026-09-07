# Advanced Wi-Fi Modes

The integrated fullmac frontend supports a station, one AP and one receive-only
monitor interface on a single 2.4 GHz channel. AP and station traffic use
separate Ethernet paths. The firmware owns authentication and encryption;
Linux reports AP client join/leave events and can deauthenticate clients.
These interfaces are implemented and build-checked; board interoperability,
throughput, coexistence and suspend/reconnect acceptance are still pending.

## Access point and concurrent station

Create the AP interface before starting an AP-capable nl80211 manager:

```sh
iw dev wlan0 interface add ap0 type __ap
ip link set ap0 up
```

The `start_ap` operation accepts open authentication, WPA2-PSK with a 32-byte
PMK, or WPA3-SAE with a password, using CCMP. WPA3 requires PMF. The manager must
support firmware authentication offload and supply the key in the AP-start
request. AP key installation through a subsequent `add_key` call is not the
implemented contract. Mixed WPA2/WPA3 transition mode and AP-side enterprise
authentication are not supported. Hostapd interoperability is not yet verified.
There are at most four clients. Beacon intervals are 100–60000 TU and DTIM
periods are 1–10; only 20 MHz channels are accepted.

Start the AP before connecting the station. Starting an AP reconfigures the
firmware and disconnects an existing station connection. In AP+STA mode the
station's channel wins; Linux reports the AP channel change. IP addressing,
DHCP service, forwarding and firewall rules are userspace responsibilities.

Open AP+STA operation has passed a same-channel peer test with both links
associated and 256 exact 1472-byte UDP echoes on each interface. The two data
phases ran sequentially; this does not establish simultaneous throughput,
protected AP interoperability or automatic AP recovery after suspend.

## Monitor reception

```sh
iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
iw dev mon0 set channel 6 HT20
tcpdump -i mon0 -s 0 -w capture.pcap
```

Received management/data frames carry a radiotap header with channel, RSSI and
the FCS-present flag. Control frames and injection are not supported. Channel
changes are rejected while a station is connected/connecting or an AP is
active, since the radio has only one channel. Capture follows that channel in
concurrent operation. Remove the interface with `iw dev mon0 del`.

## Enterprise station provisioning

The IDF EAP supplicant supports PEAP and EAP-TLS. Its certificate and identity
configuration uses vendor ID `0x18fe34`, subcommand `0x1`: five little-endian
32-bit values (operation, field, offset, total length, chunk length), followed
by at most 512 data bytes. Operations 6/7/8 are write/commit/clear. Field indices
0–6 are identity, username, password, CA, server domain, client certificate and
private key. Fields must arrive in order, fit 4095 bytes each, and be complete
before commit. PEM material includes no NUL on the wire; firmware appends it.

Use `tools/s31_wifi_eap.py` on a host with Python 3 and authenticated SSH access
to the board, or locally where Python and `iw` are available. A PEAP profile is
a local JSON file:

```json
{
  "identity": "anonymous@example.invalid",
  "username": "user@example.invalid",
  "password_file": "password.txt",
  "ca_file": "ca.pem",
  "domain": "radius.example.invalid"
}
```

Paths are relative to the JSON file. Password file bytes are used exactly;
avoid an accidental trailing newline. EAP-TLS uses `cert_file` and `key_file`
in place of username/password; the key must be unencrypted PEM. Keep these
private files outside the repository. CA and server-domain validation are
required. Set Linux's real-time clock correctly before connecting so the
firmware can check certificate validity.

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD profile.json
# On the board, with another station manager stopped:
ip link set wlan0 up
iw dev wlan0 connect EnterpriseSSID
udhcpc -i wlan0
```

This provisions the firmware EAP client; a standard wpa_supplicant WPA-EAP
profile does not supply these vendor fields automatically. Once committed,
the next station connect uses EAP. Disconnect before replacing or clearing a
profile. `--clear` removes it before switching back to personal/open networks.
The tool clears partial configuration after a failed transfer. Its commands
carry secrets through stdin, not shell arguments. The kernel keeps a private
copy for suspend recovery and wipes it on clear/unload.

## Suspend and remaining boundaries

With matching core ABI v4 and payload ABI v2, system suspend detaches netdevs,
quiesces radio tasks/IRQs/DMA, and releases the radio power vote. Resume resets
the firmware and replays retained monitor and committed EAP configuration.
Normal cfg80211 suspend stops the AP and clears its configuration before this
replay, so userspace must start the AP again after resume. Automatic AP service
restoration has not passed board acceptance. Station
association and IP reachability require userspace reconnection. A failed
restart keeps interfaces detached and returns an error.

There is no WoWLAN packet wake, retained wireless link, P2P or monitor injection
implementation. The closed firmware's public API does not expose the P2P
negotiation/role control needed to implement Wi-Fi Direct. See
[power management](power-management.md) for sleep/wake constraints.
