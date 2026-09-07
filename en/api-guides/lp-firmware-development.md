# LP Firmware Development

LP firmware links into the first 31 KiB of the 32 KiB LP SRAM. The final KiB,
starting at `0x2E007C00`, is reserved for ABI version 2 sleep-control state.

Firmware must publish READY, preserve the lower-16-bit sequence convention,
validate every sleep request field and request CRC, advertise only implemented
capabilities, and write result/state/wake data before the response CRC. Unknown
commands return the defined ERROR response.

LP peripherals are protected by the LP peripheral PMS block. A new firmware
feature must list every register window it touches and the remoteproc driver
must grant the corresponding REE read/write permission before releasing the
LP core. GPIO support currently requires the system-register,
peripheral-clock/reset, IOMUX, and mailbox windows.

The GPIO dry-run path keeps the LP core executing and samples RTCIO in
software. It intentionally does not set the RTCIO hardware wake-enable bit:
an already-active level can interrupt the LP core before it records and
publishes the wake event. Hardware wake-enable belongs to the later reviewed
HP-power-down sequence and must be paired with an LP interrupt/wake contract.

Build and stage the ELF under the remoteproc firmware name expected by the
device tree or driver. Changes to shared message values or control-structure
layout must update the shared header, Linux driver, firmware, `s31-lpctl`, HIL
case, migration guide, and ABI documentation together.
