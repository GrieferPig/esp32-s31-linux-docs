# Release and Legal

A release image is not complete until source, notices, license texts, and
redistribution-sensitive payload material are handled according to their
licenses. README navigation does not replace these bundle obligations.

The release workflow builds pinned component revisions, checks image sizes and
slot boundaries, embeds the radio filesystem, and publishes
`s31_full_flash.bin`, six slot images, `build-manifest.json` and `SHA256SUMS`. It does not run `radio-package` or a separate legal gate.
BTstack or other restricted inputs must not be redistributed outside their
permitted terms merely because they can be built locally.

Record release versions, but keep device test logs and private artifact
provenance out of published documentation. The current public LP mailbox and
radio core/payload interfaces are ABI version 1; no compatibility promise is
made for discarded pre-v1 development interfaces.
