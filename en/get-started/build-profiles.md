# Build Profiles

The default is `S31_LEAN_RADIO=1`, a radio appliance that removes many optional
peripheral drivers after applying the defconfig. Use `S31_LEAN_RADIO=0 make all`
for a build intended to use I2C, SPI target, I2S and other peripheral overlays.
Keep this setting on subsequent component builds because they reconfigure the
kernel and root filesystem. The parent integrated payload recipe explicitly
builds combo Wi-Fi/Bluetooth; `S31_WIFI_ONLY=1` does not override that recipe.
Runtime `mode=wifi` is distinct from a firmware built without Bluetooth.

| Profile choice | Effect |
|---|---|
| Default / lean radio (`1`) | Console, flash/persist, USB swap and integrated radio appliance |
| Full peripheral (`0`) | Retains optional peripheral drivers and diagnostic userspace |
| Runtime Wi-Fi only | `esp32s31_radio mode=wifi`; uses the same combo payload |
| BTstack optimized | Selects the configured optimization policy for BTstack objects |

Profiles do not change the fixed flash offsets. A profile that removes a module
must also remove or disable dependent services and overlays. The current
release workflow explicitly sets `S31_LEAN_RADIO=0` and publishes the full
flash image, six slot images, a manifest and checksums. A separately distributed radio package carries its own manifest
and license material.
