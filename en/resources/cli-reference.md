# Command-line reference

Run these commands from the board's Linux console unless a section specifies
the host computer. For build and flash commands, see the
[Make reference](make-reference.md).

## esp32-config

```sh
esp32-config
```

Opens the board configuration menu for system settings, networking, Bluetooth,
interfaces, GPIO, memory/storage, and configuration backups. See [esp32-config](esp32-config.md) for its commands
and setup steps.

## s31-overlay

```text
s31-overlay list
s31-overlay status
s31-overlay routes NAME
s31-overlay parameters NAME
s31-overlay describe NAME
s31-overlay check CONFIG_FILE
s31-overlay apply NAME [KEY=VALUE ...] [--volatile]
s31-overlay remove NAME [--volatile]
s31-overlay remove --all [--volatile]
s31-overlay restore
```

`list` shows installed overlays; `status` shows the active and saved sets.
`routes` and `parameters` show the defaults and choices exported by an overlay.
`describe` separates default, current, and saved values in tab-separated records.
`check` validates a saved configuration against the installed catalog without
applying it.

`apply` and `remove` update the named saved selection by default; `remove --all`
clears the saved set. Use `--volatile` to leave saved selections unchanged.
`restore` replaces the active set with the saved entries when the saved file
exists. See [Using overlays](overlay-catalog.md) for examples and failure behavior.

## s31-lpctl

```text
s31-lpctl status
s31-lpctl ping
s31-lpctl sleep-test MS
s31-lpctl gpio-test PIN low|high [none|up|down] [MS]
s31-lpctl send WORD
s31-lpctl recv
```

| Command | Description |
|---|---|
| `status` | Show firmware readiness, mailbox counters, and ping status |
| `ping` | Request a PING/PONG exchange |
| `sleep-test` | Run the LP timer test for 10–5000 ms while Linux remains running |
| `gpio-test` | Test an LP GPIO0–7 level, with optional pull and 10–5000 ms timeout |
| `send` | Send one 32-bit mailbox word |
| `recv` | Wait for one mailbox word and print it in hexadecimal |

The GPIO test defaults to no pull and a 1000 ms timeout. Supply the pull
argument before specifying a timeout. For example:

```sh
s31-lpctl gpio-test 3 high up 500
```

See [LP core](../api-reference/lp-core/index.md) for setup and protocol details.

## s31-selftest

```text
s31-selftest [--quick|--stress] [--json] [--duration SECONDS]
             [--require-radio-traffic]
```

The default quick test checks system health and performs a small persistent
write test. Stress mode adds concurrent CPU, XIP-read, persistent-write, and
radio-health checks. Its default duration is 60 seconds, with a range of
10–3600 seconds.

```sh
s31-selftest --quick
s31-selftest --stress --duration 60 --json
```

`--json` prints one JSON result per line. In stress mode,
`--require-radio-traffic` makes unchanged Wi-Fi/Bluetooth packet counters a
failure; generate suitable traffic while the test runs.

## s31-modload

```text
s31-modload MODULE.ko [PARAM=VALUE ...]
s31-modload --remove MODULE_NAME
```

Loads a kernel module, including XZ-compressed modules, or removes one by its
kernel name. Normal radio startup is handled by the board's service scripts.
Use this helper for module development after stopping applications that use
the device.

## HIL (hardware-in-the-loop) tools

These tools are used to automate hardware-in-the-loop testing for the ESP32-S31 platform.

On the host, list the runner options with:

```sh
python3 tools/hil/s31_hil.py --help
```

The runner coordinates `s31-hil-agent` on the S31 and optional peer firmware.
See [Hardware-in-the-loop testing](../contribute/testing-hil.md) for complete
commands and fixture setup.

## Wi-Fi diagnostics

```sh
iw dev
iw phy
wpa_cli -p /run/wpa_supplicant -i wlan0 status
ip addr show wlan0
```

The mac80211 SoftMAC frontend supports one station and does not expose firmware
EAP-credential vendor commands. See [Advanced Wi-Fi](../api-guides/wifi-advanced.md)
for AP, monitor, authentication, and suspend limitations.

## Development utilities

The project includes sources for CoreMark, memory and libc tests, extension
tests, and other diagnostics. Several are removed from the compact rootfs by
`post-build.sh`. To add a tool to your image, follow
[Adding a userspace tool](../api-guides/adding-a-userspace-tool.md).
