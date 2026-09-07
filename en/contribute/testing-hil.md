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
| `sdmmc` | S31 controller behavior against peer-mediated storage signals |
| `ethernet` | S31 network interface and peer link behavior |
| `usb-drive` | S31 USB host/device role used by the case definition |
| `mtd` | Flash partition read/write/persistence semantics |
| `lp-core` | remoteproc, READY, mailbox, and LP ABI behavior |
| `power-wake` | APPWR retention, external LP-GPIO wake, SMP resume, RAM retention, and optional USB readback |
| `smp-irq-dma` | Concurrent hart, interrupt, and DMA invariants |
| `all` | Ordered execution of supported cases |

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
  --p4-port COM6 --lp-wake-connected \
  --lp-wake-s31-gpio 0 --lp-wake-p4-gpio 2 \
  --repeat 5 \
  --output logs/hil-power-wake.json
```

The explicit `--lp-wake-connected` gate prevents an unwired run from being
misreported as a timer wake. Before suspend, the host drives and samples both
logic levels across the dedicated wire; a mismatch fails closed without
entering suspend. The host also proves that an already-active wake level is
rejected before APPWR power-down. The P4 then schedules a rising level after four seconds,
holds it for 750 ms, and returns the pad to high-Z. The S31 retains a 12-second
LP RTC timer as a recovery bound. PASS requires a GPIO wake-reason bit, resume
before the timer bound, both HP harts online, an unchanged 128 KiB tmpfs
checksum, and an unchanged first-4-KiB USB checksum when `/dev/sda` is present.
An active-low fixture uses `--lp-wake-active-low`; the host chooses the matching
LP pull automatically.

The S31 remoteproc driver measures the actual RTC slow clock before starting
the LP firmware. Do not assume a 32 kHz source: the tested coreboard used its
internal slow oscillator at about 155 kHz. The measured Q13.19 period is placed
in the same LP store used by ESP-IDF, so both the LP target and OpenSBI's timer
fallback use the board's runtime value.

## Host contract checks

Run `python3 tools/tests/test_s31_feature_contracts.py` from the parent tree.
The suite compiles the actual I2C command generator and SPI word conversion
functions with a host harness, checks I2S DAI configuration and exercises EAP
chunking/cleanup failures. It does not execute MMIO, DMA or RF hardware.
`python3 tools/tests/test_s31_btstack_reset.py` applies the recovery patch to
the local BTstack source and checks stale-connection cleanup, advertising
eligibility, initialization ordering and the custom-handler path. Run
`make btstack-source` first if that source is not present.

Board acceptance for the new paths must separately prove untimed shutdown with
no delayed reset, radio-enabled sleep with post-resume traffic, AP client
authentication, enterprise server validation, monitor capture, long I2C target
readback, target SPI DMA/abort and an external-codec I2S stream. Build or host
test success must not be used as a hardware PASS.

## Adding a case

Define the host request, device-agent operation, optional peer request, timeout,
resource ownership, cleanup, structured evidence, and exact PASS/FAIL/SKIP
criteria together. Update the agent, orchestrator, peer firmware when required,
and the support matrix in the same change.
