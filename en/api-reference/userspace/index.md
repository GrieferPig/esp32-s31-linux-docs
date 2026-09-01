# Userspace Interfaces

Applications should prefer standard Linux ABIs: TTY, GPIO character devices,
I2C, spidev where enabled, ALSA, SocketCAN, netdev/cfg80211, Bluetooth sockets,
IIO, PWM, watchdog, MTD, block devices, configfs-backed overlay management, and
remoteproc sysfs.

The S31 image adds a small set of platform tools:

| Command | Contract |
|---|---|
| `esp32-config` | Persistent configuration and service policy |
| `s31-overlay` | List, validate, apply, restore, and remove named overlays |
| `s31-lpctl` | LP status, ping, bounded sleep test, raw send, and receive |
| `s31-selftest` | Quick or stress behavior checks with optional JSON output |
| `s31-hil-agent` | Machine-readable HIL case dispatcher |
| `s31-peripheral-test` | Peripheral behavior checks selected by the HIL agent |
| `s31-modload` | Load a kernel module with explicit parameters |
| `s31-hil-io` | Bounded UART and peripheral I/O helper |
| `s31-cpu-sample` | CPU utilization sampler used by diagnostics |

Additional binaries exercise libc, strings, memory comparison, crypto,
extensions, fork behavior, faults, and memory bandwidth. They are diagnostic
programs rather than stable application libraries.

## Configuration safety

Runtime credentials, MAC addresses, host serial ports, absolute workstation
paths, and captured device logs are not documentation. `esp32-config` stores
runtime policy in the persistent filesystem; images and examples use
placeholders only.

## Exit and output behavior

Commands return zero only when the requested operation was accepted and its
defined local completion condition was met. Machine-readable modes write data
to standard output and diagnostics to standard error. A successful driver
load or interface creation does not by itself prove association, external
wiring, GATT behavior, storage integrity, or RF performance.
