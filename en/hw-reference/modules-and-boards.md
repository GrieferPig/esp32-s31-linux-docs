# Modules and boards

The port targets ESP32-S31 platforms.

Currently, tested boards include:

- Espressif ESP32-S31 Coreboard
- Espressif ESP32-S31 Korvo

Tested modules include:

- Espressif ESP32-S31-WROOM-3 E1H16R16V

## Connect the console

Use the board's USB-UART download and console connection. The default console uses UART0
at 115200 baud, 8N1.

The generic configuration reserves `GPIO58` and `GPIO59`
for the console.

Board layouts differ, so use the carrier's schematic to identify the connector,
power input, and download/reset buttons.

## Connect a peripheral

Check the selected overlay's pin assignments before wiring:

```sh
s31-overlay routes i2c0
```

The output uses GPIO numbers. Match those numbers to the pins on your
board, then connect the peripheral signals and a common ground. Check the
peripheral's voltage requirements and any required pull-ups, transceiver,
codec, or PHY.

Many matrix-routed signals can be moved to another GPIO. See the
[overlay catalog](../resources/overlay-catalog.md) for the command syntax and
reserved pins.

## Use another memory configuration

The supplied images use a fixed 16 MiB flash layout and a 16 MiB PSRAM mapping.
Supporting a different capacity requires changes to the boot configuration,
device tree, and image layout before flashing.

See [Flash layout](flash-layout.md) and [Memory map](memory-map.md).
