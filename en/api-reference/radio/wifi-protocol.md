# Wi-Fi control and authentication

The current Wi-Fi frontend is `esp32s31_softmac.c`, using mac80211/cfg80211 and
normal `iw`/`wpa_supplicant` control for a single station interface. There is no
firmware-owned EAP vendor-command provisioning interface exposed by this frontend.
Do not use vendor-command credential helpers as a current connection procedure.

For open and PSK station setup, follow [Wi-Fi and Bluetooth setup](../../user-guides/networking.md).
For enterprise authentication, validate the selected `wpa_supplicant` build and
current station stack against the intended network. CA and server-identity
validation must follow the network administrator's policy.

[Advanced Wi-Fi](../../api-guides/wifi-advanced.md) documents the current
station, monitor, AP and suspend boundaries. The common firmware radio ABI is
an implementation interface; its available operations do not establish Linux
frontend support.
