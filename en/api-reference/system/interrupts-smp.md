# Interrupts and SMP

Each HP core has a CLIC. Linux initializes local interrupt state as each core
starts, with SYSTIMER events and IPI doorbells on separate reserved slots.
Exact matrix-source and CLIC-slot assignments are in
[Interrupt routing](../../hw-reference/interrupt-routing.md).

## CPU affinity

**Generic peripheral interrupts are currently fixed to HP core 0.** The matrix
irqchip accepts an affinity mask only if it includes CPU 0 and reports the
effective affinity as CPU 0. A CPU-1-only request returns `-EINVAL`; an ordinary
IRQ affinity write cannot move these handlers to HP core 1. Local timer and
IPI routes use their separate per-core setup. See
[`esp_intmtx_set_affinity()`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp-intmtx.c#L117-L124).

The radio service worker and generic radio IRQ path run on HP core 0. The
Wi-Fi frontend schedules receive NAPI and buffer-refill work on HP core 1.
Payload-created compatibility tasks retain their requested CPU affinity, so
“all radio work runs on HP0” is too broad. See the
[radio worker](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-smode.c#L3405-L3415),
[task binding](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-rtos.c#L893-L898) and
[frontend receive work](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c#L428-L463).

## Inspect interrupt activity

```sh
cat /sys/devices/system/cpu/online
cat /proc/interrupts
```

`/proc/interrupts` reports counts for each online CPU. Compare counts before
and after a peripheral operation when investigating a missing completion or
unexpected load. Generic device counts on CPU 0 are consistent with the
current routing policy; they do not by themselves indicate an SMP failure.

## Write an interrupt handler

Obtain the Linux IRQ with `platform_get_irq()` and register the handler with
the Linux IRQ API. Read the peripheral status, handle the asserted sources,
and acknowledge them as required by that device. For a shared or multiplexed
source, inspect status before deciding whether the event belongs to the driver.

Keep hard-IRQ work bounded and non-sleeping. Defer processing to a threaded
handler, worker or NAPI when the subsystem permits it. Protect data shared
with another CPU or context using the appropriate kernel synchronization
primitive; CPU0-only IRQ routing does not make the rest of the driver single
threaded. The [I2C IRQ registration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/i2c-esp32s31.c#L816-L830)
is one concrete platform-driver example.

## DMA completion

The AHB and AXI GDMA providers handle their hardware completion interrupts and
notify clients through DMAengine callbacks. Keep callbacks within their
execution-context constraints and synchronize termination before freeing a
buffer. See [DMA and cache coherency](../../api-guides/dma-and-cache.md).
