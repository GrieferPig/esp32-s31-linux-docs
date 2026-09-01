# Build Profiles

The normal profile produces the complete Linux system selected by the active
defconfig and Buildroot configuration. Radio packaging can be reduced through
`S31_LEAN_RADIO`; a Wi-Fi-only selection is available through
`S31_WIFI_ONLY` where the current payload and rootfs rules support it.

| Profile choice | Effect |
|---|---|
| Default | Standard kernel modules, rootfs, and configured radio components |
| Lean radio | Reduces radio/rootfs content while preserving selected frontend behavior |
| Wi-Fi only | Omits Bluetooth-specific radio content where supported |
| BTstack optimized | Selects the configured optimization policy for BTstack objects |

Profiles do not change the fixed flash offsets. A profile that removes a module
must also remove or disable dependent services and overlays. Release metadata
must state which profile produced an image and include the corresponding legal
manifest.
