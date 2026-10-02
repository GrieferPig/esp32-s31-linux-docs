# USB functions

Use **Interfaces → USB** in `esp32-config` to choose host mode, a serial
connection, or a USB network connection. Device functions need the
[full-peripheral image](../get-started/build-profiles.md) and their compiled
kernel support; the menu offers only the functions available in the image.
Run the board commands below as root.

These settings control DWC2. The fixed USB Serial/JTAG port is a separate
peripheral. Use the board schematic to identify the DWC2 connection, and keep
a separate console available when changing its role.

## Choose a USB function

| Selection | Use |
|---|---|
| Host | Connect a USB peripheral, including storage |
| USB serial connection | CDC ACM application port or Linux login console |
| USB network connection (ECM) | Direct IPv4 connection to a computer with an ECM driver |

Before changing from host mode to a device function, unmount all USB-backed
filesystems and stop USB-backed swap. Use
[Memory and storage](memory-and-storage.md) for devices managed by the tool.
The role change is refused while those devices are in use. Disconnect host
peripherals before attaching the device-mode cable.

The selected mode is saved and restored at startup. Applying a different USB
function disconnects the current USB connection.

## USB serial

Choose **USB serial connection**, then select **Application serial port** or
**Linux login console**. For a login console from the command line:

```sh
esp32-config usb configure serial 1
esp32-config usb status
```

Connect the DWC2 port to the computer and open the newly enumerated serial
port. For the login console, log in with the board's account credentials.
For an application port, use `serial 0` instead; your application opens the
board-side `/dev/ttyGSN` path shown by `usb status`.

The number is discovered from the ACM function. It may differ from `ttyGS0`
when the fixed USB Serial/JTAG driver already uses that name.

## USB network

Choose **USB network connection (ECM)** and set the board's address, or run:

```sh
esp32-config usb configure network 0 192.168.7.2/24
esp32-config usb status
```

Configure the computer's USB network interface with a different address on
the same subnet, such as `192.168.7.1/24`. The board does not start a DHCP
server. For example, on a Linux computer, replace `USB_IFACE` with the actual
new interface name:

```sh
sudo ip address add 192.168.7.1/24 dev USB_IFACE
sudo ip link set USB_IFACE up
ping 192.168.7.2
```

Choose another subnet if that one is already used by a different connection.
The USB address is independent of the Wi-Fi address. Applications can use
ordinary network sockets over this link.

## Return to host mode

Close programs using the USB connection, then run from the separate console:

```sh
esp32-config usb configure host
```

Disconnect the device-mode cable before reconnecting host peripherals.

## Configure a custom ACM function

For a custom gadget with your own USB identifiers, use the configfs recipe
below. It is source-derived; USB gadget mode remains
[outside the standard HIL suite](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/hil/README.md#L146-L150).
Complete the [common pin and overlay checks](peripheral-setup), and release
any gadget created by the configuration tool first:

```sh
esp32-config usb stop
```

This keeps the saved USB selection, which will return at the next boot.

First inspect storage use:

```sh
cat /proc/mounts
cat /proc/swaps
```

Unmount every filesystem on USB storage and run `swapoff` for every
USB-backed swap entry, using the actual listed path. Disconnect the USB drive
before connecting the device-mode cable. Then apply the role overlay:

```sh
s31-overlay apply usb-device --volatile
[ -d /sys/kernel/config/usb_gadget ] || mount -t configfs none /sys/kernel/config
ls /sys/class/udc
```

Use your project's USB vendor/product IDs. Enter each hexadecimal value with
a `0x` prefix so configfs interprets it as hexadecimal.
Run this in one shell, stopping if a command fails or
if `s31-acm` already exists:

```sh
printf 'USB vendor ID (hex): '
read -r S31_USB_VID
printf 'USB product ID (hex): '
read -r S31_USB_PID
S31_GADGET=/sys/kernel/config/usb_gadget/s31-acm
mkdir "$S31_GADGET"
echo "$S31_USB_VID" > "$S31_GADGET/idVendor"
echo "$S31_USB_PID" > "$S31_GADGET/idProduct"
mkdir "$S31_GADGET/strings/0x409"
echo 's31-example-001' > "$S31_GADGET/strings/0x409/serialnumber"
echo 'S31 development' > "$S31_GADGET/strings/0x409/manufacturer"
echo 'S31 CDC ACM example' > "$S31_GADGET/strings/0x409/product"
mkdir "$S31_GADGET/configs/c.1"
mkdir "$S31_GADGET/configs/c.1/strings/0x409"
echo 'CDC ACM' > "$S31_GADGET/configs/c.1/strings/0x409/configuration"
mkdir "$S31_GADGET/functions/acm.usb0"
ln -s "$S31_GADGET/functions/acm.usb0" "$S31_GADGET/configs/c.1/acm.usb0"
S31_UDC=$(ls /sys/class/udc | head -n 1)
: "${S31_UDC:?No UDC found}"
echo "$S31_UDC" > "$S31_GADGET/UDC"
S31_ACM_PORT=$(cat "$S31_GADGET/functions/acm.usb0/port_num")
printf 'Device serial node: /dev/ttyGS%s\n' "$S31_ACM_PORT"
```

The host should enumerate a CDC ACM serial interface; inspect its newly
created serial device. Open it on the host, then send a line from the S31:

```sh
printf 'hello from S31\n' > "/dev/ttyGS$S31_ACM_PORT"
```

The S31 write can wait until the host opens the interface. Do not assume
the gadget is `/dev/ttyGS0`: the fixed USB Serial/JTAG driver may already own
that name, and the gadget allocator skips occupied names. The configfs
`port_num` attribute gives the actual number. Close both ends before cleanup:

```sh
echo '' > "$S31_GADGET/UDC"
rm "$S31_GADGET/configs/c.1/acm.usb0"
rmdir "$S31_GADGET/functions/acm.usb0"
rmdir "$S31_GADGET/configs/c.1/strings/0x409"
rmdir "$S31_GADGET/configs/c.1"
rmdir "$S31_GADGET/strings/0x409"
rmdir "$S31_GADGET"
s31-overlay remove usb-device --volatile
```

The cleanup releases the function and restores the base host role. Disconnect
the device-mode cable before reconnecting host peripherals. Sources:
[kernel configfs lifecycle](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/usb/gadget_configfs.rst#L55-L300),
[S31-aware serial allocation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/usb/gadget/function/u_serial.c#L1299-L1325),
[ACM port number](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/usb/gadget/function/f_acm.c#L818-L823).
