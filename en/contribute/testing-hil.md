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

## Adding a case

Define the host request, device-agent operation, optional peer request, timeout,
resource ownership, cleanup, structured evidence, and exact PASS/FAIL/SKIP
criteria together. Update the agent, orchestrator, peer firmware when required,
and the support matrix in the same change.
