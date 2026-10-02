# Use peripherals

These examples cover the full-peripheral image. Run target commands as root
on the S31; run the explicitly marked build commands on the Linux build host.
Prepare the image using [Build from source](../get-started/build-from-source.md)
and `S31_LEAN_RADIO=0`. The rootfs includes libgpiod v2 tools, I2C tools,
`spidev_test`, `aplay`/`arecord`, `candump`, and `cansend`. The CAN recipe below
also needs full iproute2, and the external-codec recipe needs extra kernel
options.

The examples follow the drivers, shipped overlays, and existing helper/HIL
usages. Consult the [support matrix](../resources/support-matrix.md) for
recorded hardware status, and the
[peripheral reference](../api-reference/peripherals/index.md)
for controller limits and errors.

(peripheral-setup)=

## Before connecting anything

Use the [board default routes](../hw-reference/modules-and-boards.md) to find
SoC GPIO numbers, then use your board's schematic to locate the corresponding
pads or connector pins. The repository does not supply a complete header
map. Match the electrical levels and connect a common ground where required.

Run one example at a time: UART1, SPI2, and I2S0 defaults reuse GPIO42–45.
Inspect active overlays and available routes first:

```sh
s31-overlay list
s31-overlay routes uart1
s31-overlay routes gpspi2
s31-overlay routes i2s0
```

Stop users of conflicting pins and remove the corresponding temporary
overlay before proceeding. Each example uses `--volatile`, so it does not
change the saved boot selection. A saved overlay restored at boot can still
conflict with a temporary example. Stop if an apply command fails; do not
continue with an assumed device or pin route.

## Configure GPIO

Choose **Interfaces → GPIO** in `esp32-config`, select a pin, and set its mode:

| Mode | Effect |
|---|---|
| Application controlled | Release the pin for an application or driver |
| Input | Hold an input, with no pull, pull-up, or pull-down |
| Output low | Hold the output at logical 0 |
| Output high | Hold the output at logical 1 |

Select **Save and apply** to use the setting immediately and restore it when
Linux starts. Returning before this step discards the page's edits. The pin
list shows current use and any saved setting that has not been applied.
Reserved pins and pins used by another application or interface cannot be
claimed by the configuration tool.

For example, with GPIO42 free:

```sh
esp32-config gpio list
esp32-config gpio set 42 high
```

The output remains held after the command or menu exits. To configure GPIO43
as an input with a pull-up, then read it:

```sh
esp32-config gpio set 43 input up
esp32-config gpio read 43
```

The helper holds these requests while it runs. Before using the pins from
libgpiod or an interface, release them:

```sh
esp32-config gpio set 42 application
esp32-config gpio set 43 application
```

Selecting application control removes that pin's saved assignment. Releasing
a pin does not promise a particular electrical level afterwards. Startup
restoration begins with the Linux service; use board hardware or earlier
firmware for a level required from power-on.

## GPIO from an application

With GPIO42 and GPIO43 free, connect GPIO42 to GPIO43 for a digital loopback.
Inspect the lines:

```sh
gpioinfo -c gpiochip0
```

In one terminal, hold GPIO42 high:

```sh
gpioset -c gpiochip0 42=1
```

In another terminal, read GPIO43. It should report an active/high input:

```sh
gpioget --unquoted -c gpiochip0 43
```

Press Ctrl-C in the first terminal to release the output request, then
repeat with `42=0`; GPIO43 should report inactive/low. Ctrl-C releases the
line; applications must not rely on its output level after ownership ends.
Remove the loopback wire before assigning these pins to a peripheral.

These commands use the libgpiod v2 syntax used by the
[GPIO HIL runner](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/hil/s31_hil.py#L278-L398).

## UART1 wire loopback

The shipped `uart1` overlay routes TX to GPIO42 and RX to GPIO43. Connect
those two pins together, without another transmitter driving RX, and run:

```sh
s31-overlay apply uart1 --volatile
s31-hil-io uart /dev/ttyS1 115200 256
s31-overlay remove uart1 --volatile
```

The helper configures a raw 115200-baud port, sends a 256-byte pattern, and
compares the returned bytes. A successful run prints `PASS uart`; a missing
wire, timeout, or mismatch fails the command. This uses a physical echo path;
`uart-loopback` is the helper's separate internal-loopback operation.
For an external UART device, connect its TX to S31 RX and its RX to S31 TX,
and match framing and baud rate. Keep UART0 available for the console.
See the [UART helper implementation](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/rootfs/s31_hil_io.c#L74-L164)
and [UART1 routes](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31-overlay-uart1.dtso#L10-L33).

(spi-host-loopback)=

## SPI host: wire loopback

For the unmodified `gpspi2` overlay, SCLK is GPIO42, MOSI is GPIO43, CS0 is
GPIO44, and MISO is GPIO45. Connect only MOSI to MISO for this loopback.
Run an 8-bit transfer at 100 kHz:

```sh
s31-overlay apply gpspi2 --volatile
spidev_test -D /dev/spidev2.0 -s 100000 -b 8 -v -p '\x01\x02\x03\x04'
s31-overlay remove gpspi2 --volatile
```

The verbose TX and RX byte sequences should match. For a real peripheral,
remove the loopback wire, connect SCLK/MOSI/MISO/CS as required, and use that
peripheral's mode, transaction format, and permitted clock rate. The host
driver accepts only 8-bit words; 16/32-bit support belongs to target mode.
The shipped spidev child also caps transfers at 20 MHz.

The existing `s31-hil-io spi` helper expects an external responder that returns
a specific transformed pattern; it is not a MOSI/MISO echo checker. Sources:
[host word mask](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/spi/spi-esp32s31.c#L896-L925),
[overlay defaults](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31-overlay-gpspi2.dtso#L14-L42),
[spidev_test options](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/tools/spi/spidev_test.c#L241-L313).

## SD card and USB storage

Before changing or disabling an SDMMC interface, unmount its filesystems and
stop any SD-backed swap. Both card slots share the controller, so check both
slots. The configuration menu refuses changes while any SD card is mounted
or used as swap; saving unchanged settings leaves the controller running.

The following commands assume an existing FAT partition. Check the detected
devices and replace the example partition name if necessary; a whole-device
filesystem uses the disk node instead of a `p1`/`1` partition node.

For SDMMC0, connect a suitable card socket to the fixed pins in the board
table. The stock overlay selects a 4-bit bus; a 1-bit wired socket needs
`bus-width=1` when applying it. Ensure the card socket provides a 10 kΩ
pull-up on the card's DAT3 pin even if DAT3 is disconnected from the S31.
DAT3 must stay high during initialization for native SD mode; a pull-up on
an unconnected S31 pad cannot bias the card pin. See the pinned
[S31 card wiring and 1-bit note](https://github.com/espressif/esp-idf/blob/a602e67b0bf9ee0806dc4e1df7afc9affedf5c33/examples/storage/sd_card/sdmmc/README.md#L92-L108)
and Linux's [SD initialization requirement](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/mmc/core/mmc_ops.c#L162-L180).
With the socket wired and powered, run:

```sh
s31-overlay apply sdmmc0 --volatile
ls /sys/class/mmc_host
cat /proc/partitions
mkdir -p /mnt/sd
mount -t vfat -o ro /dev/mmcblk0p1 /mnt/sd
ls /mnt/sd
umount /mnt/sd
s31-overlay remove sdmmc0 --volatile
```

USB host mode is selected by the base tree. Ensure `usb-device` is not active,
connect the drive through the board's DWC2 host connection, and inspect the
new disk before mounting it:

```sh
cat /proc/partitions
dmesg | tail -n 30
mkdir -p /mnt/usb
mount -t vfat -o ro /dev/sda1 /mnt/usb
ls /mnt/usb
umount /mnt/usb
```

Successful directory listing establishes access to that filesystem. If no
device enumerates, inspect power, wiring, the driver probe messages, and the
selected role. If the disk appears but mounting fails, check the partition
and filesystem type. The full kernel includes VFAT and EXT4; this example
mounts VFAT read-only. The repository also provides
[SD read and USB mount HIL cases](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/overlay/usr/bin/s31-hil-agent#L309-L399).

(audio-with-an-external-codec)=

## Audio with an external codec

Follow [Audio with an external codec](audio.md) for a complete PCM5102A
playback integration, including wiring, kernel options, the card overlay,
and playback checks. That guide also covers capture with the shipped
clock-consuming I2S overlays.

## USB CDC ACM gadget

Follow [USB CDC ACM gadget](usb-gadget.md) to switch the DWC2 role,
configure a serial function, discover its device node, and return to host
mode after cleanup.

## CAN with an external transceiver

Connect TWAI0 TX/RX to a suitable CAN transceiver using the board table, then
connect a correctly terminated bus with another active node at the same bit
rate. That node supplies acknowledgments and can transmit a known frame for
the receive check.

The rootfs selects `candump` and `cansend`, but the current source defconfig
**does not select iproute2**. Before using the `ip ... type can` command below,
set this in `buildroot-external/configs/esp32s31_rootfs_defconfig` on the host,
replacing its existing disabled entry, and rebuild/flash the rootfs:

```text
BR2_PACKAGE_IPROUTE2=y
```

On the S31, configure a 500 kbit/s bus:

```sh
s31-overlay apply twai0 --volatile
ip link set can0 type can bitrate 500000
ip link set can0 up
ip -details -statistics link show can0
candump can0
```

While `candump` runs, send this frame from a second terminal and inspect it
on the peer. Have the peer send a known frame back and inspect `candump`:

```sh
cansend can0 123#11223344
```

Stop `candump` with Ctrl-C, then release the interface:

```sh
ip link set can0 down
s31-overlay remove twai0 --volatile
```

Inspect error counters and peer reception if transmission fails. CAN remains
work in progress in the support matrix. Sources:
[rootfs package choices](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/configs/esp32s31_rootfs_defconfig#L63-L66),
[SocketCAN bitrate setup](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/networking/can.rst#L1340-L1375).

## Ethernet with the shipped PHY configuration

The `gmac` overlay enables the base RGMII configuration for a YT8531DC-CA PHY
at MDIO address 0, with reset on GPIO7. Use the board table and the base DTS to
match the RGMII/MDIO wiring, PHY address, reset, and delays; describe a different PHY in
a board-specific device tree.

On a matching board connected to a DHCP network:

```sh
s31-overlay apply gmac --volatile
ip link set eth0 up
cat /sys/class/net/eth0/carrier
udhcpc -n -q -i eth0
ip addr show dev eth0
```

Carrier should become `1`; a successful DHCP exchange supplies an address.
Use that address for a packet exchange with a known peer. If DHCP fails,
inspect link state and the network's address service separately. After closing applications
using Ethernet:

```sh
ip link set eth0 down
s31-overlay remove gmac --volatile
```

The recipe follows the [specific PHY description](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L830-L876)
and [existing Ethernet probe/link checks](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/overlay/usr/bin/s31-hil-agent#L253-L307).
Record your board revision, PHY, kernel/profile, link partner, and observations
when reporting hardware results.

```{toctree}
:hidden:

audio
usb-gadget
```
