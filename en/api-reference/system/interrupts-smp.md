# Interrupts and SMP

The ESP32-S31 uses a Core-Local Interrupt Controller (CLIC) on each HP core.
The interrupt matrix routes peripheral events to these controllers. Linux
initializes each core's interrupt state as the core starts.

## Timers and inter-processor interrupts

SYSTIMER provides Linux timekeeping and per-CPU timer events. Software
interrupts let one CPU request work from the other, including scheduler and
wakeup operations.

Radio device interrupts and generic peripheral IRQs run on HP core 0. Peripheral
drivers request IRQs through Linux, but routing these IRQs to HP core 1 is
currently unsupported: the interrupt-matrix affinity callback rejects masks
without CPU0. Per-core timer and IPI routes are managed separately.

## Inspect interrupt activity

On the board, run:

```sh
cat /sys/devices/system/cpu/online
cat /proc/interrupts
```

`/proc/interrupts` shows the number of interrupts handled by each CPU. Compare
the counts before and after using a peripheral when investigating missing
completions or unexpected CPU load.

## Writing an interrupt handler

Get the IRQ from the platform device and register it through the Linux IRQ
API. Read and acknowledge the peripheral's status in the handler, then pass
longer work to a worker, threaded handler, or NAPI as appropriate.

Hard-IRQ handlers run with restrictions on sleeping and allocation. Keep their
work short and use the normal kernel synchronization primitives for data
shared with another CPU.

## DMA completion

The AHB and AXI GDMA drivers handle their completion interrupts and notify
clients through DMAengine callbacks. A client can use those callbacks to wake
a waiting thread or advance a transfer queue.

Follow the [DMA and cache guide](../../api-guides/dma-and-cache.md) when passing
buffers between the CPU and a peripheral.
