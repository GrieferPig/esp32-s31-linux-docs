# Radio API Reference

```{toctree}
:maxdepth: 1

architecture
```

## Core ABI

`ESP32S31_RADIO_CORE_ABI_VERSION` is **1** (payload ABI **1**). The public kernel header exposes:

- a stable radio state and health snapshot;
- HCI registration, bounded send/dequeue, peek/consume, purge, and flow checks;
- Wi-Fi registration, MAC retrieval, scan, connect, disconnect, TX/RX, and
  bounded access-point result structures; and
- explicit Bluetooth enable and disable operations.

The current ABI includes interface-specific AP/monitor traffic, AP station
events, bounded Wi-Fi control requests and frontend restart hooks. See the
[advanced mode guide](../../api-guides/wifi-advanced.md).

Maximum typed frame sizes are 1,029 bytes for HCI and 1,600 bytes for Wi-Fi.
Wi-Fi scans return at most 32 access points through the typed result structure.
The station `rx_copy` callback uses preallocated buffers and schedules NAPI.
Auxiliary AP/monitor callbacks must not sleep and use atomic allocations;
allocation failure drops the frame. Monitor frames have a separate 4096-byte
firmware bound and include radiotap metadata in Linux.

## Module parameters

| Module | Parameter | Access | Meaning |
|---|---|---|---|
| radio loader | `firmware` | load-time, read-only | Payload firmware path |
| radio module | `mode` | load-time, read-only | `wifi`, `bt`, or `combo` |
| radio module | `direct_hci` | load-time, read-only | Expose direct H4 misc device instead of normal attachment path |
| S-mode core | `radio_rt_wake` | runtime | Enable real-time wake behavior |
| S-mode core | `radio_timing` | runtime callback | Configure supported timing policy |

Invalid mode, missing payload, ABI mismatch, or unavailable required frontend
causes initialization to fail rather than silently degrading the selected mode.

## Health sysfs

The radio platform device exposes read-only `radio_health`. Its snapshot
contains state, Wi-Fi/BT initialization status, IRQ and worker progress, heap
usage, queue drops, HCI ACL traffic totals, and coexistence state. Field names
are diagnostic contracts; their values are cumulative runtime observations and
do not guarantee external association, GATT discovery, or RF performance.

## Direct H4 device

With `direct_hci=1`, `/dev/s31-hci` has one exclusive opener. Opening enables
the Bluetooth controller; another opener or a suspended device returns `EBUSY`.
Closing unregisters the host and purges queued packets but leaves the controller
enabled until radio shutdown.

Each write supplies one H4 packet type followed by its packet bytes (2–1029
bytes total). Invalid size returns `EMSGSIZE`; suspend or queue backpressure
can return `EAGAIN`. A successful write returns the complete record length.

Read format depends on the requested buffer size:

- At most 1029 bytes requests one unprefixed H4 frame.
- More than 1029 bytes requests a batch of up to eight records. Each record
  starts with a two-byte little-endian length followed by that many H4 bytes.
  Do not parse this mode as an ordinary concatenated H4 stream.

A buffer too small for the next complete record returns `EMSGSIZE` without
consuming that record (or returns the preceding complete records in a batch).
An empty nonblocking read returns `EAGAIN`; a blocking reader waits for RX,
suspend or a controller reset notification. Suspend returns `EAGAIN`; resume
can deliver a Hardware Error event requiring host reinitialization.
`poll()` exposes readable RX/reset events and available TX capacity; suspended
state reports no readiness. Seek operations are unsupported.

The owning implementation is
[`hci_esp32s31.c`](https://github.com/GrieferPig/linux-esp32-s31/blob/feature/s31-radio-bt-6.18/drivers/bluetooth/hci_esp32s31.c).
These framing rules are private port ABI, distinct from normal Bluetooth sockets.

## Wi-Fi behavior

The Linux frontend presents a normal netdev/cfg80211 control plane. Scanning,
association, key material, TX queue wake-up, RX delivery, and disconnect
reasons cross the typed ABI. Credentials belong in runtime configuration and
must never be committed to documentation or default images.
