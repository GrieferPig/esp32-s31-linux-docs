# Adding a userspace tool

Use the Buildroot external tree to include an application in the image. Follow
[Writing applications](../api-reference/userspace/index.md) for a first C program
and a build-to-board example. The commands here run from the parent project root
unless marked as board commands.

## Add a shell script

Place a user command under
`buildroot-external/board/esp32-s31/overlay/usr/bin/`; use `usr/sbin/` for an
administrative command. Start the script with its interpreter, such as
`#!/bin/sh`, and make it executable. Buildroot copies this filesystem overlay
into the image during the rootfs build.

## Add a Buildroot package

This example adds a small `s31-hello` program using the same local-source package
mechanism as [s31-tools](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/s31-tools/s31-tools.mk).

### 1. Add the source

Create `rootfs/s31-hello/hello.c`:

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from the s31-hello package!");
    return 0;
}
```

### 2. Add the package definition

Create `buildroot-external/package/s31-hello/Config.in`:

```kconfig
config BR2_PACKAGE_S31_HELLO
    bool "s31-hello"
    help
      Small example application for ESP32-S31 Linux.
```

Create `buildroot-external/package/s31-hello/s31-hello.mk`. The command lines
inside the `define` blocks start with a tab:

```make
S31_HELLO_VERSION = 1.0
S31_HELLO_SITE = $(BR2_EXTERNAL_ESP32_S31_PATH)/../rootfs/s31-hello
S31_HELLO_SITE_METHOD = local

define S31_HELLO_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_LDFLAGS) \
		$(@D)/hello.c -o $(@D)/s31-hello
endef

define S31_HELLO_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/s31-hello \
		$(TARGET_DIR)/usr/bin/s31-hello
endef

$(eval $(generic-package))
```

Add this line inside the existing menu in `buildroot-external/Config.in`:

```kconfig
source "$BR2_EXTERNAL_ESP32_S31_PATH/package/s31-hello/Config.in"
```

`buildroot-external/external.mk` already includes `package/*/*.mk`, so the new
Makefile is found automatically. For a larger application, add its build
dependencies and corresponding Kconfig dependencies or selections. Record its
actual license and license files in the package metadata when preparing it for
distribution. `s31-tools` and `esp-simd` are local examples.

### 3. Select and save the package

After `make fetch` has prepared the Buildroot output, open its menu:

```sh
make buildroot-menuconfig
```

Find `s31-hello` under the external ESP32-S31 packages menu and enable it. Exit
with the configuration saved, then use [Buildroot’s savedefconfig target](https://github.com/buildroot/buildroot/blob/cb857ba4c87a93e5265a9e4a3f32071abf39e14a/Makefile#L1064-L1068) to export a review copy:

```sh
make -C buildroot O="$PWD/out/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" \
  savedefconfig DEFCONFIG="$PWD/out/generated/buildroot-menu.defconfig"
```

Merge the intended package selections into
`buildroot-external/configs/esp32s31_rootfs_defconfig`; this example adds
`BR2_PACKAGE_S31_HELLO=y`. Preserve the source expressions for
`BR2_TOOLCHAIN_EXTERNAL_PATH` and `BR2_ROOTFS_OVERLAY`: the review copy contains
resolved host/toolchain and staging paths injected by the parent, so do not
replace the portable source defconfig with that whole file.

Review the source diff before reconfiguring. A populated Buildroot output
rejects manually changed output configuration and changed package/toolchain
inputs. Reconfiguration discards that output while retaining download caches.

### 4. Build, flash, and run

The application is deployed as part of a verified matched image set. With the
ESP-IDF environment active, run on the host:

```sh
make buildroot-reconfigure
make fetch-rootfs
make image
ls -l out/buildroot/target/usr/bin/s31-hello
make flash-existing-all PORT=/dev/ttyUSB0
```

Replace the port and close its serial monitor before flashing. This updates
kernel, rootfs/module and radio together; partial flash targets are disabled.
After restart, log in through the serial console and run on the board:

```sh
s31-hello
```

It prints `Hello from the s31-hello package!`. This process does not require an
SSH server on the board.

### 5. Rebuild after changing local source

The parent tracks changed inputs for its existing local utility packages; your
new package is not in that list. After editing `rootfs/s31-hello/hello.c`, remove this
package's build directory before rebuilding the image:

```sh
make -C buildroot O="$PWD/out/buildroot" \
  BR2_EXTERNAL="$PWD/buildroot-external" s31-hello-dirclean
make image
make flash-existing-all PORT=/dev/ttyUSB0
```

This makes Buildroot copy and compile the updated local source. Repeat the board
run command after flashing.

(runtime-pruning)=
## Keep the application and its dependencies in the image

The [post-build script](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/post-build.sh) prunes selected programs and
shared libraries after package installation. Check `out/buildroot/target`
after `make rootfs`, including the libraries your executable needs. A successful
package build alone does not show that its runtime files remain in the image.

For example, the script removes `libstdc++`, `libatomic`, BlueZ tools and daemon,
and D-Bus/GLib/BlueALSA files. Adding a C++ application or a BlueZ-based system
therefore needs a corresponding review of those removal rules. The current
script requires `s31-btstack-a2dp`, `s31-ext-test`, `s31-gpio`,
`s31-config-archive`, and `esp32-config` to remain executable. Replacing one of
these tools requires updating that check and the services or commands that use
it. The parent build checks that the finished rootfs fits its flash partition.

(deploy-files-that-must-survive-reboot)=
## Deploy files that must survive reboot

Ordinary persistence is covered by [Configuration](../resources/configuration.md).
Two startup cleanup rules matter when uploading replacements for packaged files.
Before mounting the writable root layer, [the init script](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/overlay/init) removes writable copies of:

```text
/usr/sbin/s31-btstack-a2dp
/etc/init.d/S40btstack
/etc/init.d/S40bluetoothd
/etc/init.d/S42s31-a2dp
/usr/sbin/bluetoothd
/usr/bin/bluealsa
/usr/sbin/s31-bt-agent
/etc/bluetooth/main.conf
```

It also removes writable copies of `.dtbo` filenames shipped in
`/usr/lib/s31-overlays` by the current rootfs. A replacement uploaded to one of
these paths can work during the current session and disappear at the next boot.
To retain changes to these packaged files, rebuild and flash the rootfs. For a
temporary experiment, use a separate filename and invoke it explicitly. Pairing
keys and `/etc/esp32-conf` are outside these cleanup rules.
