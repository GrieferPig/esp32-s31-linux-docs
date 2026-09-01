# ESP32-S31 LP core and mailbox

The ESP32-S31 LP core is an independent RV32IMAC processor running at up to
40 MHz. It has 32 KiB of retention-capable LP SRAM and a 16-register hardware
mailbox connecting it to the HP CPUs. It is not a Linux CPU-idle state and the
mailbox is not process IPC.

## Architecture

The initial Linux framework has four layers:

1. `lp_firmware/` builds an ESP-IDF native LP-core application with
   `ulp_embed_binary()` and the native LP mailbox runtime.
2. `esp32s31_lp.c` loads the ELF into LP SRAM through remoteproc and controls
   LP reset, clock, wakeup and boot address registers.
3. The same driver registers the hardware mailbox controller and implements
   the synchronous ACK convention used by ESP-IDF.
4. `/dev/s31-lp`, sysfs attributes and `s31-lpctl` expose a small bring-up ABI.

The P0 protocol supports READY, PING/PONG and STATUS messages. The message ABI
is defined in `shared/s31_lp_protocol.h`.

## Build

```sh
make -C lp_firmware stage
make linux
```

Apply `esp32s31-overlay-lp.dtbo` during boot so the remoteproc device is
instantiated. The firmware must be available as
`/lib/firmware/esp32s31/s31-lp-core.elf`.

## Userspace

```sh
s31-lpctl status
s31-lpctl ping
s31-lpctl send 0x00020000
s31-lpctl recv
```

`/dev/s31-lp` transfers native-endian 32-bit messages. Reads block until an LP
message is available; writes complete after the hardware ACK or fail after a
bounded timeout.

## Current boundary

This is the P0 load/start/mailbox framework. It deliberately does not yet add
an RPMsg resource table, Linux suspend integration, or a deep-sleep retention
policy. Those belong after hardware READY and bidirectional mailbox operation
have been demonstrated reliably.
