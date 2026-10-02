# LP firmware development

LP firmware uses the ESP-IDF environment described in
[Build from source](../get-started/build-from-source.md). Linux loads its ELF
through remoteproc after the root filesystem becomes available.

## Build and install

From the parent project root:

```sh
make lp-firmware
make rootfs
```

The LP build creates
`firmware/lp/build/esp-idf/main/s31_lp_main/s31_lp_main.elf` and stages it as
`buildroot-external/board/esp32-s31/overlay/lib/firmware/esp32s31/s31-lp-core.elf`.
The rootfs build packages that file. See the [LP Makefile](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/lp/Makefile#L3-L17).

For an on-board replacement, first transfer the new ELF to
`/tmp/s31-lp-core.elf`, then stop LP before replacing the installed firmware:

```sh
/etc/init.d/S02s31-lp stop
cp /tmp/s31-lp-core.elf /lib/firmware/esp32s31/s31-lp-core.elf
/etc/init.d/S02s31-lp start
s31-lpctl status
s31-lpctl ping
```

The service locates remoteproc by the name `esp32s31-lp`, starts it and waits
for READY. `status` should include `ready=1`; `ping` reports a round-trip value
in microseconds. If startup fails, read `dmesg` and the service error before
attempting sleep. See [S02s31-lp](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/overlay/etc/init.d/S02s31-lp#L5-L43).

## Keep firmware within its memory budget

The current ESP-IDF configuration reserves **8192 bytes (8 KiB)** for LP
firmware. LP SRAM spans `0x2E000000`–`0x2E008000`, but the entire 32 KiB is not
available to code, data and stacks:

| Region | Address range, end exclusive | Role |
|---|---|---|
| LP firmware allocation | `0x2E000000`–`0x2E002000` | Current 8 KiB build budget |
| OpenSBI suspend snapshot | `0x2E002000`–`0x2E007000` | 20 KiB reserved runtime snapshot |
| Sleep-control reservation | `0x2E007C00`–`0x2E008000` | Final 1 KiB; current structure occupies 112 bytes |

Inspect ELF load segments and the linker map when increasing code, data or
stack sizes. Do not expand into either shared reservation. See the
[build allocation](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/lp/sdkconfig.defaults#L1-L4),
[OpenSBI snapshot](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L218-L219) and [memory map](../hw-reference/memory-map.md).

## Change the protocol coherently

`shared/s31_lp_protocol.h` includes Linux's
`include/linux/soc/espressif/esp32s31-lp-protocol.h`. LP publishes READY at
startup, validates requests, and writes response fields before the response
CRC. The current Linux, LP and OpenSBI sources agree on ABI 1 and the 28-word
layout.

When changing message codes, fields, states or CRC coverage, update all three
consumers together and run the existing checks from the parent root:

```sh
python -m unittest tools.tests.test_s31_feature_contracts.DriverContracts.test_lp_sleep_abi_matches_opensbi tools.tests.test_s31_feature_contracts.DriverContracts.test_lp_mem_timer_starts_after_hp_asleep -v
```

These checks compare source contracts; they do not execute a suspend cycle.
The [LP reference](../api-reference/lp-core/index.md) owns the wire-format and
field details, and [Power management](power-management.md) describes the
experimental retention path and the remaining validation needs.

## Add an LP peripheral

Before using a new register window, add its required LP peripheral-PMS access
in the remoteproc driver. The existing grant helper checks locked permissions
and verifies the written access bits; failure returns `-EACCES`. See
[permission setup](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/remoteproc/esp32s31_lp.c#L523-L588).

GPIO wake uses RTCIO ownership, level sampling and a configured LP GPIO
wakeup interrupt/ISR. The poll path covers the transition window; the ISR
records a GPIO reason and requests APPWR wake after `HP_ASLEEP`. Preserve the
inactive-at-ARM check and the cleanup that disables pulls, wakeup and input
before returning ownership. See [GPIO handling](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/lp/main/lp_core/main.c#L75-L192) and
[ARM setup](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/lp/main/lp_core/main.c#L343-L393).
