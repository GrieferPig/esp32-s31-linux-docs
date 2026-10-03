# Adding a userspace tool

Use the Buildroot external tree to include an application in the Linux image.
Shell scripts can go directly into the board overlay. Compiled programs need a
package build rule.

## Add a shell script

Place a user command under:

```text
buildroot-external/board/esp32-s31/overlay/usr/bin/
```

Use `usr/sbin/` for an administrative command. Start the script with its
interpreter, such as `#!/bin/sh`, and make it executable. Buildroot copies the
board overlay into the target filesystem during the rootfs build.

## Add a compiled program

Small project utilities have their sources in `rootfs/` and are built by the
`s31-tools` package under `buildroot-external/package/`. Follow its existing
compile and install rules for a similar utility.

For an application with its own dependencies or configuration options, add a
separate directory under `buildroot-external/package/`, with a `Config.in`
and package `.mk` file. Source its `Config.in` from
`buildroot-external/Config.in`; `external.mk` includes the package makefiles.
Select the package in `buildroot-external/configs/esp32s31_rootfs_defconfig`.
Use Buildroot's `TARGET_CC`, `TARGET_CFLAGS`, and `TARGET_LDFLAGS` so the
application inherits the image's ISA, ABI, and size-optimization settings.

The board's `post-build.sh` removes optional tools to keep the image small.
Check that your install path is retained by this script.

## Build and try it

If package selection or toolchain configuration changed in a populated
Buildroot output, run `make buildroot-reconfigure` first. Fetch any new source
dependencies separately with `make fetch`; build targets do not download them.
Edits to the existing `s31-tools` sources are detected by the parent build.

From the parent repository, build and verify a matched image set:

```sh
make image
```

The rootfs target also rebuilds Linux, so deploy the resulting kernel,
rootfs/module, and radio image together using
[Flash and first boot](../get-started/flash-and-first-boot.md). Then run the
command from the serial console.

