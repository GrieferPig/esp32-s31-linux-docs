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
separate Buildroot package. Select the package in
`buildroot-external/configs/esp32s31_rootfs_defconfig`.

The board's `post-build.sh` removes optional tools to keep the image small.
Check that your install path is retained by this script.

## Build and try it

From the parent repository, run:

```sh
make rootfs
```

After updating the board's rootfs, run the command from the serial console.

