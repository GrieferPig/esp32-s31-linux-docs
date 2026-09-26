# ESP32-S31 Linux documentation

This repository contains the programming guide for the
[ESP32-S31 Linux port](https://github.com/GrieferPig/esp32-s31-linux).

Read the [guide online](https://grieferpig.github.io/esp32-s31-linux-docs/),
or start with [Getting started](en/get-started/index.md) in this repository.

## Build the guide

From this directory, install the documentation tools in a Python environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
make html
```

Open `build/html/index.html` in a browser. To check external links, run:

```sh
make linkcheck
```

Pages are written in Markdown under `en/`. The
[writing guide](en/contribute/writing-documentation.md) explains how to add or
update a page.
