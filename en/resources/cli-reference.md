# Command-Line Reference

## `s31-overlay`

```text
s31-overlay list
s31-overlay routes NAME
s31-overlay parameters NAME
s31-overlay status
s31-overlay restore
s31-overlay apply NAME [KEY=VALUE ...] [--volatile]
s31-overlay remove NAME | --all
```

## `s31-lpctl`

```text
s31-lpctl status
s31-lpctl ping
s31-lpctl sleep-test <10..5000 ms>
s31-lpctl gpio-test <0..7> <low|high> [none|up|down] [10..5000 ms]
s31-lpctl send <u32>
s31-lpctl recv
```

`sleep-test` and `gpio-test` are bounded dry-run protocol checks and do not
prove that a powered-down HP domain can wake. Raw send/receive is intended for
ABI development and diagnostics.

## `s31-selftest`

```text
s31-selftest [--quick|--stress] [--json] [--duration SECONDS]
             [--require-radio-traffic]
```

`--json` is the machine-readable mode. `--require-radio-traffic` converts
absence of required traffic from an informational condition into a failure.

## HIL commands

```text
s31-hil-agent --case firmware|peer|sdmmc|ethernet|usb-drive|mtd|lp-core|smp-irq-dma|all
s31-modload MODULE.ko [PARAM=VALUE ...]
s31-modload --remove MODULE_NAME
s31-hil-io uart DEVICE BAUD LENGTH
```

The HIL agent emits structured case results. Helpers do not broaden permissions
or claim exclusive serial ownership beyond the lifetime of their operation.

## Diagnostic programs

`segfault`, `forktest`, `membench`, `s31-crypto-test`, `s31-ext-test`,
`s31-libc-test`, `s31-mem-compare`, `s31-string-bench`, and `s31-cpu-sample`
exercise bounded kernel or libc behavior. Their output format is diagnostic and
may evolve; applications must not treat it as a stable data API.
