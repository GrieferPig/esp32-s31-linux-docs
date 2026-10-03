# Releases and licensing

Every push to `main` starts the release workflow's fast checks. After those
checks, its image-build and publication job runs only when the head commit
message starts with `release:`. That job builds the single full-board
configuration and checks its expected driver selections.

The local publication set from `tools/release/assets.py` contains six component
images (`spl_app.bin`, `u-boot.itb`, `esp32s31_generic.dtb`, `radio.bin`,
`xipImage`, and `rootfs.sqfs`), the combined `s31_full_flash.bin`, `radio.json`,
`build-manifest.json`, and `SHA256SUMS`. `make image` verifies and publishes this
matched set under `dist/`.

The GitHub release workflow checks that complete set and uploads **only
`s31_full_flash.bin`**. Its release tag points to the parent source revision;
the component images, manifest and checksums are not currently attached. Do not
promise those downloads or a preserve-data update from the combined image.

## Prepare a release

Build and test the changes, update the feature status and installation
instructions, and check that the image fits the flash layout. Include the
build version and any migration notes in the release description.

The combined installation image replaces saved settings. When providing an
update for existing users, also explain how to preserve their data with
separate-image flashing.

## Package the radio files

For a separate engineering radio archive, run:

```sh
make radio-package
```

The result is placed as `out/images/esp32s31-radio-engineering-only.tar.xz`. The packaging helper also
has a release mode that includes a redistribution grant and corresponding
source archive:

```sh
tools/release/radio_bundle.sh --release \
  --grant GRANT_FILE --source-archive SOURCE_ARCHIVE
```

Replace the two paths with the reviewed files for that release. The helper
checks that the files exist and copies them into the package; it does not
validate the grant's scope or verify that the archive corresponds to every
binary input. Review those files against the actual payload before selecting
release mode. The combined
image workflow publishes its image separately and does not call this helper's
release mode.

## Include notices and source

Review the terms of the components included in the image, including the
Espressif radio libraries and BTstack. Package the required notices, license
texts, and source material alongside the release as appropriate.

Start with the parent repository's
[third-party notices](https://github.com/GrieferPig/esp32-s31-linux/blob/main/THIRD_PARTY_NOTICES.md)
and the radio directory's
[bundle licenses](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/radio/RADIO_BUNDLE_LICENSES.md).
Packaging commands do not change those terms.

## Record the test results

Attach the relevant build and board-test results to the release or link them
from its notes. Include the board model, build configuration, test commands,
and remaining issues. Remove credentials and private keys from shared logs.
