# Build and Images

## Component relationships

The top-level `Makefile` coordinates the toolchain, U-Boot SPL, OpenSBI,
U-Boot proper, Linux, the radio payload, the Buildroot root filesystem, and the
final Flash image.

```text
radio-idf-deps -> external radio payload -----------\
                                                       -> radio.sqfs
Linux single radio module + overlays + configuration-/
btstack-source -------------------------------------------> Buildroot rootfs
OpenSBI --------------------------------------------------> U-Boot FIT
U-Boot SPL + FIT + DTB + Linux + radio + rootfs ----------> s31_full_flash.bin
```

- The default output directory is `build/`.
- The ESP-IDF radio closure is a versioned ELF relocatable payload. It remains
  separate from `esp32s31-radio.ko` and is loaded from the radio partition at
  module probe time.
- `configs/esp32s31-layout.cfg` constrains both image packaging and partial
  Flash targets.
- `tools/gen_esp_flash_image.sh` combines the final image according to that
  layout.
- The historical `bootloader` target is a compatibility alias for `uboot`.

## Memory profiles

The default build uses the 16 MiB radio profile (`S31_LEAN_RADIO=1`). It keeps
the serial console, Flash and persistent storage, USB mass storage, USB swap,
Wi-Fi, Bluetooth, and one BTstack process providing A2DP/AVRCP plus a minimal
BLE GATT peripheral. BlueZ is not built: the direct H4 transport uses only
libc, and the image does not select `bluetoothd`, D-Bus, GLib, BlueALSA, or the
legacy pairing agent. Unused wired
networking, CAN, MMC, sound, I2C, SPI, PWM, IIO, hardware monitoring, watchdog,
and optional timer/DMA devices are omitted from the base image. Device-tree
overlays remain the opt-in mechanism for the peripheral blocks that have an
overlay.

The lean profile also removes the idle syslog, klog, and cron daemons. Its DHCP
client exits after obtaining an IPv4 lease; `wpa_supplicant` stays resident to
maintain the association. Reapplying the Wi-Fi configuration obtains a new
lease rather than running a permanent renewal process.

Use `make S31_LEAN_RADIO=0 all` when producing a general-purpose image for
optional peripheral overlays. The base device tree leaves optional DMA,
GPTimer, and watchdog instances disabled; the matching overlay enables the
controller needed by that peripheral.

The startup scripts use the first Linux swap partition on USB storage and limit
its active signature to 256 MiB by default. This avoids retaining a roughly
1 MiB swap map for a 4 GiB partition on a 16 MiB target. Override the limit in
the environment with `S31_USB_SWAP_SIZE_KIB`; no zram or internal-Flash swap is
used by the default profile.

## Build targets

| Target | Artifact or behavior |
| --- | --- |
| `make all` | Prepares dependencies and builds U-Boot, Linux, rootfs, and the full image |
| `make toolchain` | Downloads and verifies the prebuilt toolchain |
| `make toolchain-source` | Builds the toolchain from the adjacent `crosstool-NG` source tree |
| `make opensbi` | Builds the OpenSBI `fw_dynamic` used by the U-Boot FIT |
| `make uboot` | Generates `spl_app.bin` and `u-boot.itb` |
| `make radio-idf-deps` | Builds the Wi-Fi, Bluetooth, coexistence, and PHY closure |
| `make radio-linux-payload` | Relinks the closure as external `build/esp32s31-radio-fw-v1.o` and generates its explicit kernel-import table |
| `make linux` | Builds the Linux 6.18 output, `xipImage`, DTB, and DTBO files |
| `make radio-fs` | Builds Linux and rootfs as needed, then packages one module, the external payload, overlays, configuration, and notices as `radio.sqfs` |
| `make btstack-source` | Fetches the exact pinned BTstack source commit into `build/` |
| `make btstack-notices` | Packages the BTstack license, commit, and downstream patch/build inputs |
| `make rootfs` | Generates `rootfs.sqfs` |
| `make initramfs` | Compatibility alias for `rootfs` |
| `make persist` | Generates an empty or initialized `persist.jffs2` |
| `make flash-image` | Generates `s31_full_flash.bin` without the persistent slot |

## Bluetooth userspace modes

The normal service runs `/usr/sbin/s31-btstack-a2dp -u 0 -l none`. With either
the Bluetooth-only or combined overlay it exclusively owns the BTDM client's
direct H4 endpoint at `/dev/s31-hci`. The service accepts SSP Just Works
pairing, provides Classic A2DP sink and AVRCP roles, and advertises a minimal
BLE peripheral named `S31 Radio`. Service `0xff10` contains read-only
characteristic `0xff11`, whose value is `ready`. Link keys are stored below
`/var/lib/btstack` on the persistent overlay.

The default build advertises 44.1 kHz joint-stereo SBC with a maximum bitpool
of 53, 16 blocks, 8 subbands, and loudness allocation. SBC remains lossy, but
this is the current high-quality profile and is closer to the IDF A2DP source
configuration than the former bitpool-35 profile. Because the compact image
has no PCM output backend for this service, its transport-only mode receives
and counts compressed A2DP frames without linking the SBC/PCM rendering path.
Neither mode routes A2DP samples to a board I2S/ALSA device.

The ESP-IDF controller is built in BTDM mode and BLE stays active while A2DP is
available. The compact process implements a peripheral, not a general BLE
scanner or GATT client; richer applications must extend that same process
because `/dev/s31-hci` permits only one host owner.

The controller remains enabled across BTstack stop/start cycles and uses modem
sleep while idle. Closing `/dev/s31-hci` unregisters the host endpoint and
purges its rings, but does not call the controller's non-restart-safe
disable/enable sequence.

## Incremental radio workflow

- Changes below `radio_firmware/` or to the Linux radio module require
  `make radio-fs`, followed by `make flash-radio` for an on-board test.
- The startup service loads the single module with `mode=wifi`, `mode=bt`, or
  `mode=combo`, derived from `/etc/esp32-conf/{wifi,bluetooth}.conf`.
  `firmware=esp32s31-radio-fw-v1.o` selects the external payload. To change
  mode without rebooting, stop Wi-Fi and BTstack users, update the policy, and
  run `/etc/init.d/S00s31-radio restart`. The restart fails rather than forcing
  removal while an interface or HCI endpoint is still owned.
- A mode reload runs the payload shutdown entry point and tears down the
  selected Linux frontends, compatibility tasks, IRQ state, rings, and radio
  heap before loading the same versioned payload again. The executable arena
  is deliberately retained at one virtual address until reboot because
  private ESP-IDF process-lifetime callbacks can retain payload code pointers;
  the loader overwrites and relocates the pristine external ELF in that arena
  on every load. A successful module load alone is not proof of symmetric
  shutdown; on-board reload tests are required after changes to this path.
- `build-radio/sdkconfig` preserves resolved Kconfig values. After changing
  `radio_firmware/idf_deps/sdkconfig*.defaults`, run
  `idf.py -B build-radio fullclean` from `radio_firmware/idf_deps` in an active
  ESP-IDF environment before rebuilding, so an older generated value does not
  override the new default.
- BTstack or other target-userspace changes require `make rootfs`, followed by
  `make flash-rootfs`. `make radio-fs` also rebuilds rootfs when necessary.
- `make flash-existing-rootfs` and `make flash-existing-radio` write already
  built, non-empty images without traversing build dependencies. Use them only
  after the corresponding normal build target has passed and the running
  kernel/module version is known to match.
- The radio module must match the running kernel's version magic. If the Linux
  submodule revision or kernel configuration changed, flash both
  `make flash-linux` and `make flash-radio`; flashing only the bundle will make
  the old kernel reject the new module.
- Use `make all` and `make flash-all` for a complete integrated image. The
  persistent slot is preserved by `flash-all`.
- On the target, run
  `S31_CPU_TOP=1 s31-cpu-sample <radio-pid> <btdm-pid> <btstack-pid> 60`.
  Its acceptance value is the larger of global `/proc/stat` CPU use and the
  sum of all scheduler task ticks, avoiding an artificially low result when
  interrupt work is charged differently.

BTstack is pinned to commit
`431d58d5613fd8fae38afe50282b25302de84bf7`. Its included license permits
personal/non-commercial use; commercial images require a separate license
from BlueKitchen.

The BTstack appliance alone can be compiled with `-O2` by running
`make S31_BTSTACK_O2=1 rootfs`. The normal build remains `-Os`; this switch
does not change the kernel, ESP-IDF payload, or other Buildroot packages.

## Clean targets

| Target | Behavior |
| --- | --- |
| `make clean` | Removes `build/` and radio intermediates while retaining downloads and the toolchain |
| `make fullclean` | Performs `clean` and then removes the toolchain |
| `make buildroot-clean` | Removes only the Buildroot output tree |

## Flash targets

The default serial device is `/dev/ttyUSB0` and the default baud rate is
2 Mbaud. The caller may override the device path with a Make variable. All
offsets come from `configs/esp32s31-layout.cfg`.

| Target | Written region | Persistent state |
| --- | --- | --- |
| `make flash-bootloader` | SPL and FIT | Preserved |
| `make flash-linux` | DTB and Linux | Preserved |
| `make flash-radio` | Single radio module, external payload, overlays, and radio configuration | Preserved |
| `make flash-rootfs` | SquashFS | Preserved |
| `make flash-existing-radio` | Existing `build/radio.sqfs`; no rebuild | Preserved |
| `make flash-existing-rootfs` | Existing `build/rootfs.sqfs`; no rebuild | Preserved |
| `make flash-all` | SPL, FIT, DTB, Linux, radio, and rootfs | Preserved |
| `make flash-persist` | Persistent slot | Recreated or overwritten |
| `make erase` | Entire Flash device | Destroyed |

`flash-opensbi` is a historical compatibility target. It writes the FIT slot
that contains OpenSBI; there is no independent raw OpenSBI partition.

## Release artifacts

The release workflow pins the toolchain, ESP-IDF, and BTstack versions and
verifies that each artifact fits within its layout boundary. It rejects any
selected or retained BlueZ, D-Bus, GLib, or BlueALSA runtime closure and checks
that the BTstack executable needs only libc. A public release should include
images, hashes, Flash-layout metadata, licenses, and corresponding-source
information. `btstack-s31-notices.tar.xz` contains the exact BTstack license,
commit identifier, and downstream integration inputs. This manual does not
retain per-build logs or host-specific paths.
