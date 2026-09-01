# LP Firmware Development

LP firmware links into the first 31 KiB of the 32 KiB LP SRAM. The final KiB,
starting at `0x2E007C00`, is reserved for ABI version 2 sleep-control state.

Firmware must publish READY, preserve the lower-16-bit sequence convention,
validate every sleep request field and request CRC, advertise only implemented
capabilities, and write result/state/wake data before the response CRC. Unknown
commands return the defined ERROR response.

Build and stage the ELF under the remoteproc firmware name expected by the
device tree or driver. Changes to shared message values or control-structure
layout must update the shared header, Linux driver, firmware, `s31-lpctl`, HIL
case, migration guide, and ABI documentation together.
