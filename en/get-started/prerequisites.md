# Prerequisites

The integrated build is intended for Linux. Ubuntu 24.04 is also the release
workflow host. Initialize source explicitly before building:

```sh
sudo apt-get update
sudo apt-get install -y git build-essential bison bc flex cpio gperf \
  device-tree-compiler libffi-dev libssl-dev ninja-build python3-venv \
  python3-pkg-resources python3-pyelftools rsync unzip xz-utils curl \
  mtd-utils gcc-riscv64-linux-gnu
git clone --recurse-submodules https://github.com/GrieferPig/esp32-s31-linux.git
cd esp32-s31-linux
```

For an existing clone, run `make download` as a separate operation. Ordinary
builds do not update submodule checkouts. Preserve local modifications before
explicitly moving submodules to their recorded revisions.

## ESP-IDF and compiler

`configs/build-versions.mk` is the version authority. Install its exact IDF
revision, using a new checkout directory:

```sh
export IDF_PATH="$PWD/.esp-idf"
git clone --filter=blob:none https://github.com/espressif/esp-idf.git "$IDF_PATH"
idf_ref=$(sed -n 's/^ESP_IDF_REF := //p' configs/build-versions.mk)
git -C "$IDF_PATH" checkout "$idf_ref"
"$IDF_PATH/install.sh" esp32s31
. "$IDF_PATH/export.sh"
make IDF_EXPORT="$IDF_PATH/export.sh" idf-check toolchain
```

IDF's installer supplies its required target compiler. The payload linker
expects the `ESP_ELF_RELEASE` installation declared in the same version file.
The `toolchain` target downloads and checks the pinned Linux musl compiler.
An intentionally different IDF revision requires `S31_ALLOW_UNPINNED=1` and
new acceptance; it is not the reproducible default.

## Host checks

```sh
python3 -m venv /tmp/s31-checks
. /tmp/s31-checks/bin/activate
python -m pip install -r docs/requirements.txt dtschema==2026.6
make check-host check-docs
python3 tools/check_s31_dt.py --cross-compile riscv64-linux-gnu-
```

Use the stock Linux RISC-V cross compiler for schema-only builds; use the
configured S31 compiler for the actual kernel image. No serial device is
opened by these host checks. Before flashing, identify the board's download
port, close competing serial applications and preserve persistent storage.
See [Flash and First Boot](flash-and-first-boot.md).
