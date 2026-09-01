# Userspace Interfaces

S31 userspace prefers standard Linux ABIs. `s31-overlay` and `esp32-config`
provide only board-level resource orchestration and persistent policy; they do
not replace the standard control plane for each subsystem.

## Interface matrix

| Subsystem | Kernel interface | Userspace components | Boundary |
| --- | --- | --- | --- |
| Wi-Fi | cfg80211/nl80211 and `wlan0` | `iw`, `wpa_supplicant`, `wpa_cli`, `ip`, `udhcpc` | WPA2 station; no AP, P2P, WPS, WPA-Enterprise, or WPA3 |
| Bluetooth | `/dev/s31-hci` direct H4 | BTstack A2DP/BLE appliance, `rfkill` | A2DP sink, AVRCP, SSP pairing, and minimal BLE GATT peripheral; no BlueZ runtime |
| GPIO | `/dev/gpiochipN` | libgpiod 2.x | Line requests are exclusive and end with the owning process |
| I2C | `/dev/i2c-N` | `i2c-tools` | Intended for known device addresses; overlays manage routing |
| CAN/TWAI | SocketCAN and `canN` | `ip`, `can-utils` | A normal bus requires a transceiver and termination |
| SPI | `/dev/spidevN.M` or target controller | Standard SPI userspace interfaces | The active overlay selects controller role and routing |
| Audio | ALSA/ASoC | ALSA tools and applications | PCM capabilities depend on the active I2S overlay |
| Hardware monitoring | IIO, hwmon, Counter, and PWM | Standard sysfs and character-device ABIs | No board-specific private ioctl |

## GPIO lifetime

- The legacy `/sys/class/gpio/export` ABI is disabled.
- GPIO line requests are exclusive. An application must retain ownership for as
  long as it needs a persistent output.
- The system configuration layer does not store arbitrary GPIO output levels
  or replay application outputs after reboot.
- Normal requests cannot override lines reserved by Flash, the console, invalid
  pads, or active overlays.

## Persistent policy

- Network and radio policy is stored under `/etc/esp32-conf`.
- Wi-Fi configuration stores only a derived PSK, not a reversible plaintext
  passphrase.
- Boot scripts restore the overlay set; the corresponding Linux drivers still
  create the device nodes.
- See [System configuration](configuration.md) for the complete policy rules.

## Bluetooth ownership

The BTstack service exclusively opens `/dev/s31-hci`; the direct endpoint
allows one host process and bypasses the generic Linux Bluetooth socket path.
The image does not build or install BlueZ or its D-Bus audio chain. It also
does not expose the Classic A2DP stream as an ALSA PCM device: the default path
validates and counts compressed media transport, while the optional decoder
diagnostic discards decoded PCM samples. The same process advertises `S31
Radio` and a read-only `0xff11` GATT characteristic returning `ready`; it is
not a BLE scanner or general GATT client.
