# Interrupts and SMP

## CLIC model

- The HP harts use CLIC. `mtvec.MODE` and `stvec.MODE` select CLIC mode.
- The standard `mie/mip/mideleg/sie/sip` path is not used for interrupt
  dispatch on this platform, and the `sie` CSR is unavailable.
- The Machine CLIC base is reported by `mclicbase` CSR `0x350` and is currently
  `0x10800000`.
- The Supervisor CLIC base is reported by `sclicbase` CSR `0x150` and is
  currently `0x10A00000`.
- Each raw interrupt entry starts at `base + 0x1000 + 4 * raw_id`:

| Byte | Field |
| ---: | --- |
| `+0` | IP |
| `+1` | IE |
| `+2` | ATTR (`SHV/TRIG/MODE`) |
| `+3` | CTL |

CLIC windows are hart-address-virtualized. The normal window addresses the
current hart; the `+0x10000` window addresses the other HP hart.

## Levels and routing

- `CLICINTCTLBITS` is 3, and only `CTL[7:5]` is programmable.
- Linux uses a non-nested level-1 configuration. S-mode timer, IPI, and device
  slots follow the same rule.
- External interrupts use raw IDs `16..47`. INTMTX `SOURCE_MAP` values contain
  raw CLIC IDs.
- Linux uses the following doorbells:

| Direction | INTMTX source | Destination raw ID | Doorbell address |
| --- | ---: | ---: | ---: |
| CPU0 -> CPU1 | 66 | 40 | `0x20586014` |
| CPU1 -> CPU0 | 65 | 41 | `0x20586010` |

The sender publishes the `ipi_mux` reason, executes `wmb()`, and then writes the
doorbell. The receiver clears the doorbell before calling
`ipi_mux_process()`.

## Timer and shared slots

- Direct S-mode access to local MTIME/MTIMECMP faults, so Linux does not map a
  direct CLINT compare register.
- Linux uses the 16 MHz always-on SYSTIMER counter1.
- TARGET0/source33 is the hart0 one-shot clock event. TARGET1/source34 is the
  hart1 one-shot clock event.
- On hart0, the timer and doorbell share raw ID41. On hart1, they share raw
  ID40. The handler drains every asserted source associated with the slot.

## Trap causes and return

- High bits in CLIC `xcause` contain return state. Logical dispatch must use
  `xcause & 0xfff`.
- Linux stores the complete hardware token in `pt_regs.cause_raw` and exposes
  only the normalized cause to generic code.
- To return from a real CLIC interrupt, software restores the raw cause before
  status and EPC, then executes exactly one `sret`.
- A synchronous redirect across M/S privilege levels carries only the low
  logical cause and does not propagate raw CLIC metadata.
- Generic Linux code does not modify the raw return token. The current
  configuration does not permit nested S-mode interrupts.

## Initialization and pending recovery

- Before entering OpenSBI, each hart independently clears IP, IE, ATTR, and CTL
  for all 128 CLIC entries.
- Linux initializes external IDs `16..47` as disabled S-mode level slots. The
  irqdomain enables a slot when its device becomes active.
- Each hart initializes only its own combined IPI/SYSTIMER slot.
  `sintthresh` is zero.
- Runtime Linux does not use the OpenSBI M-mode IPI/RFENCE path.
- If hardware leaves a slot at `IP=1, IE=1` without entering its handler, the
  idle path scans doorbells, SYSTIMER state, and enabled external slots while
  local interrupts are disabled.
- A doorbell is cleared before processing. Timers enter the standard clockevent
  path. Device interrupts return to their owning driver through
  `generic_handle_domain_irq()`, and the driver performs acknowledgement.
- Software dispatch temporarily installs kernel-mode `pt_regs` and pairs
  `irq_enter/irq_exit`, so handlers observe a Linux IRQ context equivalent to a
  hardware trap.
