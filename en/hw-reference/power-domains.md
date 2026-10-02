# Power domains

The Linux PMU provider publishes seven generic power domains. Linux explicitly
controls HP connectivity (`HPCNNT`) transitions; the other domains are exposed
for topology and attachment and kept on by provider policy. Active-state radio
PMU initialization still occurs in the linked payload.

## Registered topology and policy

| Domain name | Binding identifier | Registered parent | Linux policy |
|---|---|---|---|
| `top` | `ESP32S31_PD_TOP` | None | Always on |
| `hp-alive` | `ESP32S31_PD_HPALIVE` | `top` | Always on |
| `modem-power` | `ESP32S31_PD_MODEMPWR` | `top` | Always on |
| `hp-cpu` | `ESP32S31_PD_HPCPU` | `top` | Always on |
| `hp-connectivity` | `ESP32S31_PD_HPCNNT` | `top` | Automatic only when `espressif,allow-hpcnnt-power-off` is present |
| `modem` | `ESP32S31_PD_MODEM` | `modem-power` | Always on |
| `lp-peripheral` | `ESP32S31_PD_LP_PERI` | None registered | Always on |

The supplied device tree includes the HPCNNT opt-in. The radio module holds a
separate vote while active because the payload accesses this domain outside a
normal device attachment. An active radio vote prevents HPCNNT power-off.
After payload PMU initialization, the reclaim hook reapplies Linux's HPCNNT
force state. See the [domain policy and topology](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/pmdomain/esp32s31-pmu.c#L305-L355),
[DTS opt-in](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L233-L241), and
[vote/reclaim implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/pmdomain/esp32s31-pmu.c#L152-L212).

## Read domain diagnostics

```sh
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

| Field | Meaning |
|---|---|
| Leading name | Domain name from the table above |
| `policy=` | `always-on` or `automatic`, from the genpd policy flag |
| `software=` | Provider's tracked `on` / `off` state |
| `hardware=` | Force-register interpretation: `off` if FORCE_PD is set, otherwise `on` if FORCE_PU is set, otherwise `firmware-auto` |
| `force=` | Low six force-control bits: reset, isolation, power-up, no-reset, no-isolation, power-down |
| `on=`, `off=` | Successful genpd on/off callbacks; `on` also includes initial HPCNNT ownership at probe |
| `reclaim=` | Reclaim attempts after payload PMU initialization |
| `errors=` | Force-register readback failures during transitions |
| `radio-vote=` | Active radio veto; reported only for `hp-connectivity` |

Despite the field name, `hardware=` decodes a force-control register. It is not
an independent power-good signal, current reading or proof of retention.
The output format is defined by [`domains_show()`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/pmdomain/esp32s31-pmu.c#L234-L270).

## System retention configuration

The OpenSBI APPWR profile writes power value `0x0000aa00` and clock value
`0x00000000`. The source defines these as memory-retention mode for the four HP
memory banks, power-down mode for HP logic groups and gating of HP clock
classes. LP firmware supplies the wake request. See the [profile constants](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L209-L219) and [entry sequence](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L830-L848).

For current suspend status, CPU idle, shutdown and timed deep sleep, see
[Power management](../api-guides/power-management.md).

## Power measurements

A repeatable board-current reference remains to be documented. Record the
board revision, supply point/voltage, USB connection, enabled peripherals,
radio state, CPU frequency and instrument/sample interval alongside each
measurement. Board-input current includes regulators, USB bridges and LEDs;
do not label it as CPU-domain current.
