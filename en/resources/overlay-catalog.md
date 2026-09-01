# Overlay Catalog

The current tree provides 29 named overlays.

| Group | Overlay names | Main ownership rule |
|---|---|---|
| Serial | `uart1`, `uart2`, `uart3`, `uart3-dma` | `uart3-dma` additionally owns UHCI0 and AHB GDMA pair 0 |
| I2C | `i2c0`, `i2c1` | Each owns its controller and SCL/SDA routes |
| SPI | `gpspi2`, `gpspi2-target`, `gpspi3`, `gpspi3-target` | Controller and target modes share the same instance claim |
| Audio | `i2s0`, `i2s1` | Each owns its I2S instance and selected routes |
| CAN | `twai0`, `twai1` | Each owns its controller and TX/RX routes |
| Storage | `sdmmc0`, `sdmmc1`, `sdmmc-dual`, `sdmmc-uhs` | All claim `sdmmc-host`; variants reserve their pad groups |
| Network/USB | `gmac`, `usb-device` | Own RGMII pads or USB OTG HS respectively |
| Timing/analog | `timers`, `pwm-counter`, `analog`, `watchdogs` | Enable grouped blocks and claim routed pads/IRQ resources |
| DMA | `gdma` | Claims AHB GDMA pair 4 |
| Radio | `radio-wifi`, `radio-bluetooth`, `radio-combo` | Mutually exclusive `radio` claim |
| Low power | `lp` | Claims the LP core and enables remoteproc/mailbox nodes |

## Parameters

| Overlay | Parameter | Accepted values |
|---|---|---|
| `i2c0`, `i2c1` | `clock-frequency` | `100000`, `400000`, `1000000` |
| `sdmmc0`, `sdmmc1`, `sdmmc-dual`, `sdmmc-uhs` | `bus-width` | `1`, `4` |

Routes are reported by `s31-overlay routes NAME`; accepted parameters by
`s31-overlay parameters NAME`. Route-specific GPIO selections are supplied as
documented key/value arguments when the overlay metadata exposes them.

## Application behavior

`s31-overlay apply NAME [KEY=VALUE ...] [--volatile]` validates the name,
parameters, routes, GPIO claims, and resource claims before applying the DTBO.
Persistent selections are restored during boot. Removing an overlay is rejected
when the kernel cannot safely detach its devices or when the requested name is
not active. `remove --all` removes only overlays managed through this interface.
