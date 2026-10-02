# EAP vendor protocol

This interface provisions credentials for the firmware-owned EAP client.
For the host helper and profile format, see
[Advanced Wi-Fi](../../api-guides/wifi-advanced.md). Provisioning and station
association are separate operations.

## Transport and request layout

Send a cfg80211 vendor command on the station interface with vendor ID
`0x18fe34` and subcommand `0x1`. The helper supplies each binary request to:

```sh
iw dev wlan0 vendor send 0x18fe34 0x1 -
```

The request has a 20-byte header followed by field data. All header members are
unsigned little-endian 32-bit integers; lengths and offsets count bytes.

| Byte offset | Member | Meaning |
|---:|---|---|
| 0 | operation | WRITE = 6, COMMIT = 7, CLEAR = 8 |
| 4 | field | Field ID for WRITE; zero otherwise |
| 8 | offset | Position of this chunk in the field; zero otherwise |
| 12 | total | Complete field length for WRITE; zero otherwise |
| 16 | length | Data bytes after the header; zero for COMMIT/CLEAR |
| 20 | data | Up to 512 bytes for WRITE |

The complete message must contain exactly `20 + length` bytes. WRITE requires
a nonempty chunk and a total field length of 1–4095 bytes.

## Field IDs

| ID | Field |
|---:|---|
| 0 | Identity |
| 1 | Username |
| 2 | Password |
| 3 | CA certificate |
| 4 | Server domain |
| 5 | Client certificate |
| 6 | Private key |

The server domain is limited to 253 bytes and cannot contain NUL. The supplied
Python helper also rejects NUL in every other field. Identity, CA, and domain
are required; provide either username and password for PEAP, or both client
certificate and private key for EAP-TLS.

## Transaction sequence

1. Disconnect the station and stop automatic reconnection.
2. Send CLEAR with all remaining header members zero.
3. Write each field from offset zero in consecutive chunks. Keep `total`
   unchanged for that field. Complete all fields before COMMIT.
4. Send COMMIT with all remaining header members zero. A successful commit
   enables enterprise credentials for the driver's later station-connect call.

The driver rejects provisioning while the station is connected, connecting,
or suspended, or when the command targets a different interface. Starting a
field again at offset zero without clearing it returns `EALREADY`. Bad sizes,
out-of-order chunks, incomplete fields, and writes after COMMIT are rejected.
On failure, clear the partial profile before retrying; the helper attempts this
cleanup automatically.

Credentials are held in runtime memory. The driver can replay them after its
suspend/resume cycle, while a reboot or module removal requires provisioning
again. Association and IP configuration remain the station manager's job.

## Implementation

The [control header](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/esp32s31-radio-control.h)
defines operation and field IDs. The
[Wi-Fi frontend](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c)
validates requests and caches fields for resume. The host serializer and failure
cleanup are exercised by `tools/tests/test_s31_feature_contracts.py` using
`tools/s31_wifi_eap.py`.
