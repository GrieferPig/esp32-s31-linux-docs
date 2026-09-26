# Low-power core

The LP core runs firmware alongside Linux. The `esp32s31_lp` remoteproc driver
loads the firmware into LP SRAM and exchanges messages through the hardware
mailbox.

## Check the firmware

With the LP driver enabled and firmware running, use:

```sh
s31-lpctl status
s31-lpctl ping
```

`status` shows whether the firmware has sent READY, the last received message,
and mailbox statistics. `ping` sends a request and reports the PING/PONG result.

The normal firmware filename is `esp32s31/s31-lp-core.elf`. For building a
replacement, see [LP firmware development](../../api-guides/lp-firmware-development.md).

## Test the timer

Run a one-second timer test:

```sh
s31-lpctl sleep-test 1000
```

The interval can be 10–5000 ms. Linux stays running while the LP firmware
handles the timer and reports the wake event.

## Test a GPIO input

Choose an available LP GPIO from 0 through 7. This example waits up to one
second for GPIO3 to read high with a pull-down enabled:

```sh
s31-lpctl gpio-test 3 high down 1000
```

Drive the selected input to the requested level during the test. To check
sampling with an internal pull alone, use:

```sh
s31-lpctl gpio-test 3 high up 500
s31-lpctl gpio-test 3 low down 500
```

A connected circuit or board strap may override the internal pull. The test
runs while Linux is awake. System sleep is covered in
[Power management](../../api-guides/power-management.md).

## Devices and attributes

| Interface | Description |
|---|---|
| `/dev/s31-lp` | Read or write a 32-bit mailbox word |
| `ready` | Whether a READY notification has been received |
| `last_message` | Last received word |
| `mailbox_stats` | Message, acknowledgement, and timeout counts |
| `tx_message` | Send a mailbox word |
| `ping` | Start or read a PING/PONG test |
| `sleep_test` | Start or read a timer test |
| `gpio_test` | Start or read a GPIO test |
| `deep_sleep` | Read deep-sleep status or request timed shutdown |

The device attributes are under the bound LP platform device. Firmware
selection and start/stop control use the standard remoteproc `firmware` and
`state` attributes.

## Mailbox protocol

Commands use the upper 16 bits for the operation and the lower 16 bits for a
sequence number. READY (`0x53310001`) and WAKE (`0x53310002`) are fixed
notifications.

The protocol includes PING/PONG, STATUS, and these sleep operations:

| Operation | Purpose |
|---|---|
| PREPARE | Check the request and prepare wake sources |
| ARM | Start the requested wake sources |
| QUERY | Read state, result, wake reason, and timestamps |
| RECLAIM | Return control to Linux after completion |
| ABORT | Cancel the request |

The sleep-control block uses ABI version 1 and contains 28 packed 32-bit
words (112 bytes). It starts at `0x2E007C00`, in the final KiB of LP SRAM.
Timer fields hold a relative interval in microseconds.

The request CRC covers all bytes before `request_crc`. The response CRC covers
all bytes before `response_crc`, including request and result data. The driver
uses `crc32_le(~0U, data, length) ^ ~0U` and retries a response snapshot while
the LP core is updating it.

See the [protocol header](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/soc/espressif/esp32s31-lp-protocol.h)
for message values, flags, states, and structure fields.
