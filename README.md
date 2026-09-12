# ESP32-S31 Linux Developer Documentation

This repository contains the English developer documentation for the
ESP32-S31 Linux port. It is included by the main `s31linux` repository as the
`docs` submodule.

The rendered programming guide is published at
<https://grieferpig.github.io/esp32-s31-linux-docs/>.

The documentation describes stable software and hardware behavior. It does
not preserve test logs, workstation-specific paths, device identifiers, or
one-off validation results.

## Build locally

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
make html
```

The generated site is written to `build/html/index.html`. Run `make linkcheck`
to validate external and internal links.

The boot image used by the parent repository is intentionally kept at
`bootlog.png`; the parent README references its raw URL in this repository.
