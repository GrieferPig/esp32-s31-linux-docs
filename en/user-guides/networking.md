# Wi-Fi and Bluetooth setup

Open `esp32-config` on the board's console. **Network** contains Wi-Fi and IPv4
settings; **Bluetooth** contains the Bluetooth service, device name, and pairing
controls. Run the examples below as root. Saved settings are restored at boot;
see [Configuration](../resources/configuration.md) for storage and backup.

Wi-Fi and Bluetooth share one radio module. Changing which services are enabled
restarts that module and can interrupt both connections. Choosing an already
saved enabled/disabled state leaves the radio alone. Reconnecting Wi-Fi with
its current radio mode does not restart Bluetooth.

## Connect to Wi-Fi

1. Choose **Network → Wi-Fi network → Connect / change network**.
2. Select a nearby network, or choose **Enter network name** for a hidden or
   manually entered SSID.
3. For a protected network, enter its password once and select **Connect**.
   An open network has no password prompt.

The selection is saved and the connection starts immediately. Returning from
an input page before submitting keeps the saved profile unchanged. The Wi-Fi
page shows the selected network, connection state, and assigned IPv4 address.
Use **Reconnect saved network** to connect again without entering its password.

The setup page supports open networks and WPA/WPA2 Personal. A protected network
accepts an 8–63-byte password or a 64-digit hexadecimal PSK. Network names are
preserved even when they contain spaces, punctuation, or non-ASCII characters.
For other authentication methods, see [Advanced Wi-Fi](../api-guides/wifi-advanced.md).

From an interactive console, the same save-and-connect operation is:

```sh
esp32-config wifi configure
```

Enter the SSID and the password once. Alternatively, specify the network name
on the command line; the password is still entered at a separate prompt:

```sh
esp32-config wifi connect 'My Wi-Fi'
```

For an open network:

```sh
esp32-config wifi connect 'Guest Wi-Fi' open
```

## Check or retry the connection

```sh
esp32-config wifi status
esp32-config network status
```

A completed connection has Wi-Fi association and an IPv4 address. If the wait
ends before those steps complete, the tool says the settings are saved and the
connection is still pending. The connection workers remain active, so you can
leave the menu and check again later. A pending result does not identify a
password error.

The retry page keeps the network selection and provides **Retry connection**,
**Change password**, **Choose another network**, and **View details**. From the
command line, restart the saved Wi-Fi connection with:

```sh
esp32-config apply wifi
```

For detailed state and logs:

```sh
wpa_cli -p /run/wpa_supplicant -i wlan0 status
cat /run/esp32-config/wpa_supplicant.log
cat /run/esp32-config/udhcpc.wlan0.log
```

The DHCP client stays running to obtain and renew the lease. To remove the
saved network and turn Wi-Fi off, choose **Forget saved network** or run
`esp32-config wifi forget`.

## Set the IPv4 address and DNS

Choose **Network → IP address and DNS**. The default is automatic addressing
and DNS through DHCP. For a static address, select **Manual**, fill in the
address and prefix, and provide a gateway if the board needs one. Set DNS
servers manually or leave that list empty for a local network without DNS.
Select **Save and apply** when finished; changing an active connection reconnects
Wi-Fi. If Wi-Fi is off, the settings apply the next time it connects.

For example, on a network using `192.168.1.0/24`, with a router and DNS server
at `192.168.1.1` and an unused board address of `192.168.1.50`:

```sh
esp32-config network static 192.168.1.50 24 192.168.1.1 192.168.1.1
```

Use the addresses assigned for your network. The arguments are `ADDRESS`,
`PREFIX`, `GATEWAY`, and up to three DNS addresses. Use `-` for no gateway.
To return to automatic addressing and DNS:

```sh
esp32-config network dhcp
```

You can also keep DHCP addresses while choosing your own DNS servers:

```sh
esp32-config network dhcp manual 192.168.1.1
```

The saved manual DNS policy remains in effect when DHCP renews its lease.
These settings apply to the managed Wi-Fi interface. USB networking has its own
address setting in [USB functions](usb-gadget.md).

## Use the bundled Bluetooth application

When Bluetooth is enabled, the image starts `/usr/sbin/s31-btstack-a2dp` through
`/etc/init.d/S40btstack`.
This is a BTstack host using `/dev/s31-hci`, with a Classic A2DP sink, AVRCP
support, and a small BLE GATT peripheral in the same process.

**The [bundled A2DP application](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/btstack-s31/btstack-s31.mk) receives compressed SBC media for transport
testing. SBC decoding is compiled out and it has no PCM playback backend.**
Connecting a phone and starting a stream therefore produces status and packet
counts in the log; adding audible playback requires application work.

### 1. Start Bluetooth

```sh
esp32-config bluetooth enable
esp32-config bluetooth info
/etc/init.d/S40btstack status
cat /run/s31-btstack-a2dp.log
```

Service status reports whether the process is running. Use the log to check
controller initialization, advertising, pairing, and stream events.

### 2. Pair and send a Classic audio stream

On the phone or computer, open Bluetooth settings and select the device whose
name is `S31 Radio`, or the name saved in **Bluetooth → Device name**. Complete
the peer's pairing prompts and choose the board as the audio destination.
The [bundled demo](https://github.com/bluekitchen/btstack/blob/431d58d5613fd8fae38afe50282b25302de84bf7/example/a2dp_sink_demo.c#L678-L697) automatically accepts SSP confirmation requests and rejects
legacy PIN-code pairing.

Start audio on the peer, then pause it and read the service log again. Look for
stream-start and stream-pause events and the media packet/SBC byte counters.
These show reception through the transport-test application. The service log
also records sequence gaps and duplicate packets.

### 3. Read the BLE test characteristic

Use a BLE central or GATT inspection application on the other device. Scan for
the configured Bluetooth name (initially `S31 Radio`), connect, discover service
`0xff10`, and read characteristic
`0xff11`. Its value is the text `ready`; this [test characteristic](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/btstack-s31/0013-a2dp-add-minimal-ble-gatt.patch) requires no
pairing. The normal phone Bluetooth device list may not show a GATT peripheral,
so use the BLE application's scan function.

The board-side `esp32-config bluetooth scan` command reports that scanning is
unsupported. The bundled host provides the peripheral role; BLE is enabled
alongside Classic Bluetooth.

## Change the Bluetooth name or clear pairings

Choose **Bluetooth → Device name** to use one name for Classic Bluetooth, BLE
scan responses, and the GAP Device Name. Names contain 1–29 bytes and no control
characters. UTF-8 names use more than one byte per character. For example:

```sh
esp32-config bluetooth name 'My S31'
```

If Bluetooth is enabled, changing its name restarts Bluetooth and disconnects
its current devices. The Wi-Fi service keeps running.

Choose **Clear saved pairings** to forget the controller's stored Classic and
BLE keys. Bluetooth must be enabled and running. From the command line:

```sh
esp32-config bluetooth clear-pairings
```

The operation restarts Bluetooth. Remove the old pairing from the phone or
computer before pairing again. For a saved enabled service that failed to
start, use **Retry starting Bluetooth** or `esp32-config bluetooth restart`;
this recovery can also reconnect Wi-Fi.

## Stop, restart, or hand over the controller

| Task | Board command |
|---|---|
| Stop the current Wi-Fi connection and keep the saved policy | `esp32-config stop` |
| Restart Wi-Fi from its saved profile | `esp32-config apply wifi` |
| Disable Wi-Fi for subsequent boots | `esp32-config wifi disable` |
| Stop BTstack and release `/dev/s31-hci` for another application | `/etc/init.d/S40btstack stop` |
| Start BTstack again when its saved policy is enabled | `/etc/init.d/S40btstack start` |
| Disable Bluetooth for subsequent boots | `esp32-config bluetooth disable` |

Stop BTstack before opening `/dev/s31-hci` from another program; the device
allows one client. Close your program before restarting the service. The
[radio reference](../api-reference/radio/index.md) describes the direct-HCI API,
module parameters, and `radio_health` diagnostics.

For startup failures, see [Debugging](../api-guides/debugging.md). Pairing data
and settings use the storage described in
[Configuration](../resources/configuration.md); the service log is temporary.
