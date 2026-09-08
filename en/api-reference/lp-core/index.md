# Low-Power Core API Reference

The LP core is managed by the `esp32s31_lp` remoteproc driver and a firmware
image normally named `esp32s31/s31-lp-core.elf`. The driver loads the image into
LP SRAM, starts and stops the core, exchanges mailbox words, and coordinates
the documented sleep-control block.

## Devices and sysfs

| Interface | Direction | Meaning |
|---|---|---|
| `/dev/s31-lp` | read/write | Raw 32-bit mailbox messages |
| `ready` | read | Firmware READY state observed by the driver |
| `last_message` | read | Last mailbox word received |
| `mailbox_stats` | read | TX/RX and protocol progress counters |
| `tx_message` | write | Submit one 32-bit mailbox word |
| `ping` | read/write as implemented | Initiate or report a PING/PONG exchange |
| remoteproc `firmware` | read/write | Standard remoteproc firmware selection |
| remoteproc `state` | read/write | Standard start/stop control |

## Mailbox ABI version 1

The upper 16 bits identify a command or response and the lower 16 bits carry a
sequence number. Defined operations are READY, PING/PONG, STATUS, SLEEP_PREPARE,
SLEEP_ARM, SLEEP_ABORT, SLEEP_QUERY, SLEEP_RECLAIM, and ERROR.

Sleep coordination uses the final KiB of the 32 KiB LP SRAM. The control block
starts at `0x2E007C00` and contains magic, ABI version, size, sequence, flags,
wake sources, timer duration, GPIO masks and levels, retention/domain/clock
masks, resume information, capability/state/result data, timestamps, and two
CRC fields.

The request CRC covers bytes before `request_crc`. The response CRC covers all
bytes before `response_crc`, including request and result fields. Consumers
must validate magic, version, size, sequence, CRC, current state, and advertised
capabilities before acting on a response.

## Sleep behavior

The protocol advertises handshake, timer wake, GPIO wake, wake logging, and
retention-descriptor capabilities. Flags distinguish s2idle, standby, memory
sleep, deep-reboot, and dry-run requests. Unsupported wake masks, states, or
power levels return a protocol error; the high-performance side must not assume
that PREPARE implies ARM or that an ARM request guarantees a completed power
transition.

The current Linux integration uses the LP protocol for bounded sleep
coordination. Deep power-state support remains limited by platform clock,
domain, memory-retention, and wake restoration implementations.
