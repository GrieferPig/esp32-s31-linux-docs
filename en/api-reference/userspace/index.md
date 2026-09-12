# Userspace Interfaces

Applications should prefer standard Linux ABIs: TTY, GPIO character devices,
I2C, spidev where enabled, ALSA, SocketCAN, netdev/cfg80211, Bluetooth sockets,
IIO, PWM, watchdog, MTD, block devices, and remoteproc sysfs. Runtime overlays use the private
`/dev/s31-overlay` misc-device ABI; they do not use configfs.

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

## Overlay device ABI

The shared definition is `linux-esp32-s31/include/uapi/linux/esp32s31-overlay.h`.
Buildroot installs this header into the SDK staging include directory and builds
`s31-overlay` against that same definition. The kernel ABI description is
`Documentation/ABI/testing/dev-esp32s31-overlay` in the kernel tree.

Write one complete DTBO (at most 128 KiB) to apply it. The ioctls list up to 32
active overlays, return the last applied ID, remove a named overlay, or remove
all overlays. GPIO claims are a 64-bit mask with explicit 8-byte alignment;
applications must include the header instead of duplicating structure layouts.
Access is controlled by the device node permissions. Removal can fail while a
consumer or dependent overlay still owns a resource.

The CLI serializes state-changing commands with `/run/s31-overlay.lock`.
The kernel must enable `CONFIG_FILE_LOCKING`; the standard profile and parent
build enforce it. A kernel without flock support returns `ENOSYS` and the CLI
fails before changing state.
`/run/s31-overlay.current` describes this boot's selections; the persistent file
records desired selections for restoration. A `--volatile` change updates only
the running selection. A later persistent change updates only the named desired
entry, so it cannot accidentally save an unrelated volatile overlay. Direct
ioctl clients bypass this CLI bookkeeping and must coordinate with its lock.

An error saving configuration after a successful hardware operation does not
roll that operation back. The CLI reports that the overlay is already applied
or removed and returns failure; inspect `s31-overlay status` before retrying.
