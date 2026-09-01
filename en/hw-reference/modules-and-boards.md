# Modules and Boards

The generic ESP32-S31 device tree describes SoC resources, not the wiring of
every module or carrier. Optional interfaces are selected by overlays and may
require external level shifting, pull-ups, regulators, PHYs, antennas,
connectors, or storage devices.

A board description should record:

- module and silicon revision;
- usable flash and PSRAM sizes;
- oscillator and clock inputs;
- console and download-mode wiring;
- regulator and power-domain constraints;
- routed GPIO matrix signals and voltage levels; and
- external PHY, RF, USB, SD/MMC, audio, or CAN components.

Do not claim board compatibility from USB VID/PID, a boot banner, or a shared
module name alone. A board overlay belongs in the kernel tree when it encodes
stable wiring; local fixture wiring belongs in HIL configuration, not the
generic hardware reference.
