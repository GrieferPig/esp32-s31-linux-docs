# Interrupt Routing

Peripheral sources enter the ESP32-S31 interrupt matrix and are delivered to
per-hart CLIC inputs. Device tree identifies the source and trigger behavior;
the irqchip and routing providers own the hardware programming.

Overlay route metadata covers GPIO matrix signals, not arbitrary interrupt
rewiring. Shared interrupt sources must have a driver-level demultiplexer. A
new driver should request its IRQ through the platform API, use the binding's
defined trigger type, acknowledge the peripheral before returning, and defer
sleeping work outside hard-IRQ context.

The system timer, software interrupt/IPI path, and radio interrupt are platform
infrastructure. Optional overlays must not claim or repurpose them unless an
explicit binding and ownership change accompanies the implementation.
