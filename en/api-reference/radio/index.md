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

With `direct_hci=1`, `/dev/s31-hci` carries bounded H4 frames. Each operation
contains one H4 packet type followed by its packet bytes. Callers must preserve
packet boundaries, obey the maximum frame length, handle backpressure, and
close the device before switching to a kernel Bluetooth frontend.

## Wi-Fi behavior

The Linux frontend presents a normal netdev/cfg80211 control plane. Scanning,
association, key material, TX queue wake-up, RX delivery, and disconnect
reasons cross the typed ABI. Credentials belong in runtime configuration and
must never be committed to documentation or default images.
