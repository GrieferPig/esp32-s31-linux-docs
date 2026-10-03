# Releases and licensing

The release workflow builds the full board image and publishes the
combined image, six component images, `radio.json`, `build-manifest.json`, and `SHA256SUMS`
on GitHub. Release publishing runs for pushes to `main` whose commit message
starts with `release:`, after the fast-check job succeeds. The component
filenames come from `configs/esp32s31-layout.cfg` through
`tools/release/assets.py`.

## Prepare a release

Build and test the changes, update the feature status and installation
instructions, and check that the image fits the flash layout. Include the
build version and current installation requirements in the release description.

The combined installation image overwrites persist. The six same-build
component images support a slot-wise update that preserves persist only when
the installed image already uses the same layout. Changing the installed
layout requires an external backup, a clean installation, and restoration of
needed files/settings. Publish the matching manifest and checksums, and keep
the installation and preservation instructions from `configs/release-notes.md`. Do not mix a radio
XIP image with a different kernel build. Do not describe host-only layout
validation as a successful hardware boot or flashing test.

`make image` stages the complete set in a temporary directory, checks the
manifest and checksums, then atomically publishes `dist/<manifest-id>/`.
`dist/current` is switched atomically only after verification succeeds.
A failed publication leaves the previous complete release available. The
manifest includes explicit provenance for any baseline-rootfs repack; that
path must never be described as a clean source build.

## Package the radio files

For a separate engineering radio archive, run:

```sh
make image
make radio-package
```

The result is placed under `out/images/`. The helper packages only
existing verified outputs and never triggers a build. Missing or mismatched
inputs fail before the archive is replaced. The packaging helper also
has a release mode that includes a redistribution grant and corresponding
source archive:

```sh
tools/release/radio_bundle.sh --release \
  --grant GRANT_FILE --source-archive SOURCE_ARCHIVE
```

Replace the two paths with the reviewed files for that release. The helper
checks that the files exist and copies them into the package. The combined
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
