# Hardware-in-the-Loop Framework

The HIL framework describes repeatable interfaces between a host, an
ESP32-S31 device under test, and an optional programmable ESP32-P4 peer. Its
documentation records cases, protocol messages, resource ownership, and pass
conditions; it does not preserve individual test sessions.

## Topology

The P4 is a programmable peer that drives or observes S31 Linux interfaces.
The host orchestrator controls serial transport, selects cases, collects
structured results, and enforces timeouts. A peer-dependent case is complete
only when the peer firmware participates in the required electrical or
protocol exchange.

## Cases

| Case | Defined boundary |
|---|---|
| `firmware` | Host/device agent protocol and baseline firmware state |
| `peer` | Programmable-peer discovery and protocol handshake |
| `gpio` | Four-lane bidirectional levels, IRQ transitions, and final high-Z release |
| `uart` | S31 UART overlays and peer-mediated bidirectional byte streams |
| `spi`, `spi-stress` | S31 controller transfers, modes, and bounded lengths against the peer target |
| `spi-target` | S31 target-mode DMA transfers against the P4 controller |
| `i2c` | S31 controller transfers against the programmable target |
| `i2s`, `i2s-stress` | Peer-clocked playback/capture and bounded stream stress |
| `pwm-pcnt` | P4-observed PWM output and S31 pulse-counter input |
| `sdmmc` | Read-only S31 SD/MMC enumeration and block-device checks against an inserted card |
| `ethernet` | S31 network interface and peer link behavior |
| `usb-drive` | S31 USB-host mass-storage enumeration and bounded readback |
| `mtd` | Flash partition read/write/persistence semantics |
| `lp-core` | remoteproc, READY, mailbox, and LP ABI behavior |
| `power-wake` | APPWR retention, external LP-GPIO wake, SMP resume, RAM retention, and optional USB readback |
| `c6-wifi`, `c6-ble` | Radio association/data and BLE interoperability against the P4's hosted C6 |
| `c6-wifi-recover` | S31 Wi-Fi fault injection and recovery using the configured network |
| `smp-irq-dma` | Concurrent hart, interrupt, and DMA invariants |
| `all` | Ordered host suite; peer stages run only when both serial ports are available, and powered wake requires its explicit wiring gate |

## Result semantics

- `PASS` means every requirement of the selected case completed.
- `FAIL` identifies the first failed protocol or behavior gate.
- `SKIP` means a declared prerequisite was absent; it is not an end-to-end
  pass.
- Driver probe, interface enumeration, or a transmitted command is not enough
  when the case requires an external response.

The device agent provides a machine-readable response for each case. The host
must release serial ownership when a run ends, including timeout and failure
paths. Energized GPIO, PWM, or motor-control fixtures require bounded output,
fault monitoring, and final zero-output/disarm behavior in the relevant test
definition.

## Powered LP-GPIO wake fixture

The powered-suspend case uses one dedicated signal in addition to a common
ground. Connect a P4 safe-pool output (GPIO2 by default) to one S31 always-on
LP GPIO (GPIO0 by default). Do not reuse the normal four-lane GPIO42--45
fixture: those S31 pads are not in the always-on LP GPIO0--7 bank. Both boards
use 3.3 V logic; never connect either signal to 5 V.

After checking the selected header pins and continuity, run:

```sh
tools/hil/s31_hil.py --board both --case power-wake \
  --p4-port P4_PORT --lp-wake-connected \
  --lp-wake-s31-gpio 0 --lp-wake-p4-gpio 2 \
  --repeat 5 \
  --output logs/hil-power-wake.json
```

The explicit `--lp-wake-connected` gate prevents an unwired run from being
misreported as a timer wake. Before suspend, the host drives and samples both
logic levels across the dedicated wire; a mismatch fails closed without
entering suspend. The host also proves that an already-active wake level is
rejected before APPWR power-down. The P4 then asserts a rising level after four
seconds and holds it until the S31 resumes; its ten-second output safety window
is renewed immediately before the assertion, and explicit cleanup returns the
pad to high-Z. The S31 retains a 15-second LP RTC timer as a recovery bound.
PASS requires a GPIO wake-reason bit, resume
before the timer bound, both HP harts online, an unchanged 128 KiB tmpfs
checksum, and an unchanged first-4-KiB USB checksum when `/dev/sda` is present.
An active-low fixture uses `--lp-wake-active-low`; the host chooses the matching
LP pull automatically.

The S31 remoteproc driver measures the actual RTC slow clock before starting
the LP firmware. Do not assume a 32 kHz source: a board using the internal slow
oscillator can run near 155 kHz, and the exact value is measured at runtime.
The measured Q13.19 period is placed in the same LP store used by ESP-IDF, so
both the LP target and OpenSBI's timer fallback use the board's runtime value.

## Host contract checks

Run `python3 tools/tests/test_s31_feature_contracts.py` from the parent tree.
The suite compiles the actual I2C command generator and SPI word conversion
functions with a host harness, checks I2S DAI configuration and exercises EAP
chunking/cleanup failures. It does not execute MMIO, DMA or RF hardware.
`python3 tools/tests/test_s31_btstack_reset.py` applies the recovery patch to
the local BTstack source and checks stale-connection cleanup, advertising
eligibility, initialization ordering and the custom-handler path. Run
`make btstack-source` first if that source is not present.

Historical board runs exercised radio-enabled Wi-Fi sleep with post-resume
traffic, open AP+STA data paths, and target SPI DMA transfers. These results
do not certify a changed checkout; retain new acceptance summaries with build
identity in local acceptance records.
Protected AP client authentication, enterprise server validation, monitor
capture, long I2C target readback, target SPI abort/malformed handling and an
external-codec I2S stream still require separate board tests. Build or host
test success must not be used as a hardware PASS.

## Adding a case

Define the host request, device-agent operation, optional peer request, timeout,
resource ownership, cleanup, structured evidence, and exact PASS/FAIL/SKIP
criteria together. Update the agent, orchestrator, peer firmware when required,
and the support matrix in the same change.

## Cross-hart TLB regression

The rootfs includes `s31-tlb-stress` for remote-flush regressions. It pins a
permission-changing thread to CPU0 and a reader to CPU1, then alternates
read-only/read-write permissions on a shared 128 KiB address-space mapping.
The reader checks the data while both harts participate in the same process.
A pipe stops the reader after the requested changes; the test has a 90-second
process alarm and releases its mapping and file descriptors on completion.

```sh
s31-tlb-stress 2000
```

Require exit status zero, a `PASS` line, nonzero `reader_passes`, and no CSD,
RCU stall, or kernel fault diagnostics. This exercises remote TLB invalidation
without Flash writes. The CPU1 reader never writes to protected pages, so
this does not prove enforcement of CPU1 write permissions. Pair it with the dedicated scratch MTD case and a
persist file-hash/reboot test when investigating JFFS2 corruption; passing
this command alone does not validate JFFS2 garbage collection or durability.

For durability tests, wait passively for a fresh ROM banner and the new login
prompt after issuing `reboot`, then establish a shell and compare boot IDs.
A fixed delay followed by an active shell probe can interrupt a slow shutdown.
The shell wait helper reads the console before probing it, stays passive
through observed boot/shutdown output, and sends Ctrl-C only to an observed
ash continuation prompt. This avoids cancelling shutdown or stopping U-Boot
autoboot during the test.
