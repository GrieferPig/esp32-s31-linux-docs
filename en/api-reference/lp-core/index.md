# Low-power core

The `esp32s31_lp` remoteproc driver loads firmware into LP SRAM and exchanges
32-bit messages with the LP core through the hardware mailbox. The normal
firmware name is `esp32s31/s31-lp-core.elf`. Startup and replacement are covered
in [LP firmware development](../../api-guides/lp-firmware-development.md).

## Check startup and the timer

```sh
s31-lpctl status
s31-lpctl ping
s31-lpctl sleep-test 1000
```

`status` includes `ready=1` once READY has arrived, the last message and mailbox
counters. `ping` reports `ready` and `rtt_us`; the round-trip value varies.
`sleep-test` accepts **10–5000 ms** and sets `DRY_RUN`, so Linux stays awake.
A successful timer test reports `result=0` and the timer bit (`0x1`) in
`wake_reason`.
See the [test handler and result formatting](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c).

## Test a GPIO transition

The CLI accepts LP GPIO0–7, level `low` or `high`, pull `none`, `up` or `down`,
and a timeout of **10–5000 ms** (default 1000 ms). Select a pin available on your
board and keep it at the **inactive level while ARM executes**.

For GPIO3 high-level wake, start with the input low, then drive it high after
arming and before the one-second timeout:

```sh
s31-lpctl gpio-test 3 high down 1000
```

For low-level wake, start high and then drive it low:

```sh
s31-lpctl gpio-test 3 low up 1000
```

The firmware configures the pull, waits 100 microseconds for the input to
settle, and rejects an already-active input with `S31_LP_SLEEP_ERR_WAKE_MASK`.
This check applies to `DRY_RUN` too. Matching the internal pull to the active
level is therefore not a valid standalone test; an external circuit or strap
can also change the initial level. See the [ARM validation](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c).

A successful GPIO3 test reports `result=0`, the GPIO bit (`0x2`) in
`wake_reason` and bit 3 (`0x8`) in `raw`. A timeout means no accepted transition
completed in the interval. Linux remains awake; passing this test does not
establish system-suspend or deep-sleep wake reliability.

## Devices and attributes

| Interface | Description |
|---|---|
| `/dev/s31-lp` | Write exactly 4 bytes; read with a buffer of at least 4 bytes to receive one 32-bit mailbox word |
| `ready` | Whether a READY notification has been received |
| `last_message` | Last received word |
| `mailbox_stats` | Message, acknowledgement and timeout counts |
| `tx_message` | Send a mailbox word |
| `ping` | Start or read a PING/PONG test |
| `sleep_test` | Start or read a timer test |
| `gpio_test` | Start or read a GPIO test |
| `deep_sleep` | Read deep-sleep markers or request timed shutdown |

The attributes belong to the bound LP platform device. Firmware selection and
start/stop use remoteproc's `firmware` and `state` attributes. Binary reads can
block waiting for a word; a nonblocking empty read returns `-EAGAIN`. See the
[character-device implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c).

## Mailbox and shared control block

Command words use the upper 16 bits for the operation and the lower 16 bits
for a sequence number. READY (`0x53310001`) and WAKE (`0x53310002`) are fixed
notifications. PING/PONG and STATUS accompany these sleep operations:

| Operation | Purpose |
|---|---|
| PREPARE | Validate the request and supported wake configuration |
| ARM | Arm the transaction and its wake sources, including the inactive GPIO check |
| QUERY | Read state, result, wake reason and timestamps |
| RECLAIM | Return the completed transaction to Linux control |
| ABORT | Cancel the request and disarm wake sources |

The shared block uses **ABI version 1**, with **28 packed 32-bit words
(112 bytes)** at `0x2E007C00`. The final KiB of LP SRAM is reserved for it.
Linux and LP firmware include the same protocol definition; OpenSBI's current
validation agrees with this version and layout.

| Field group | Units / meaning |
|---|---|
| `deadline_lo`, `deadline_hi` | One relative interval in microseconds, despite the field name |
| `sleep_ticks_lo`, `sleep_ticks_hi` | Absolute RTC counter value when the timer starts / transaction is armed |
| `wake_ticks_lo`, `wake_ticks_hi` | Absolute RTC counter value when wake is recorded |
| `state`, `result` | Transaction state and protocol result code |
| `wake_reason`, `wake_raw` | Wake-source mask and source-specific raw bits |

For retention (`MEM`), firmware starts the timer after OpenSBI publishes
`HP_ASLEEP`; it does not consume the interval during Linux's earlier device
suspend work. See the [timer conversion](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c) and
[retention start condition](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c).

The request CRC covers bytes before `request_crc`; the response CRC covers
bytes before `response_crc`, including request and result fields. Linux uses
`crc32_le(~0U, data, length) ^ ~0U` and retries a response snapshot while LP is
publishing it. The [protocol header](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/soc/espressif/esp32s31-lp-protocol.h)
is the authoritative list of message codes, flags, states and fields; the
[CRC reader](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c) defines validation behavior.

System sleep commands and validation limits are in
[Power management](../../api-guides/power-management.md).
