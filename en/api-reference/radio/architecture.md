# Radio Architecture

The radio implementation is split so Linux-facing drivers never call arbitrary
closed payload symbols. A loader validates and relocates the external payload;
the radio core owns execution, memory, IRQs, work scheduling, coexistence, and
health; typed frontends expose Wi-Fi and Bluetooth to standard Linux stacks.

```text
cfg80211/netdev       Bluetooth HCI or direct H4
       |                       |
       +------ typed ABI v1 ---+
                   |
             radio core
          /        |        \
  SRAM pools   coexistence   payload loader
                              |
                         radio payload
```

## Ownership

The radio core owns the payload lifetime, the radio interrupt, worker context,
preallocated queues, SRAM pools, PMU vote, and health counters. Wi-Fi and HCI
frontends register typed callback tables and copy data into Linux-owned bounded
buffers. Payload callbacks may run in interrupt context and therefore cannot
sleep or allocate through general kernel paths.

## Payload boundary

The payload image is packaged in `radio.sqfs`, loaded from the configured
firmware name, checked against the generated import allowlist, relocated into
its fixed execution/data regions, and started only after required clocks,
power, and memory are available. An unresolved import, unsupported relocation,
overlapping region, or ABI mismatch fails closed.

The external payload format is an implementation boundary, not a userspace
ABI. Changes require synchronized loader, generator, package, legal-manifest,
and radio-core updates.

## Coexistence

Wi-Fi and Bluetooth share radio hardware and scheduling state. Combo mode uses
the coexistence implementation supplied with the payload dependencies. Linux
frontends submit work; they do not bypass coexistence or directly manipulate
radio arbitration registers.
