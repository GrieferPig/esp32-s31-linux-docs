# ESP32-S31 Linux documentation

This repository contains the programming guide for the
[ESP32-S31 Linux port](https://github.com/GrieferPig/esp32-s31-linux).

Read the [guide online](https://grieferpig.github.io/esp32-s31-linux-docs/),
or choose [English](en/index.md) or [简体中文](zh_CN/index.md) in this repository.

## Build the guide

From this directory, install the documentation tools in a Python environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
make html
```

Start a local preview server:

```sh
python3 -m http.server --bind 127.0.0.1 --directory build/html 8000
```

Open `http://127.0.0.1:8000/` in a browser. This also lets search load result
summaries. Stop the server with Ctrl+C when finished.

`make html` builds English under
`build/html/en/` and Simplified Chinese under `build/html/zh_CN/`, with separate
Sphinx language settings, navigation and search indexes. The Read the Docs
theme's language dropdown opens the corresponding page in the other language.

To check external links, run:

```sh
make linkcheck
```

Use `make html SPHINXOPTS="-W --keep-going"` for the strict build used in CI.
For a quick preview of one language, use `make html-en` or `make html-zh_CN`;
build both before checking links in the language selector.

Pages are written in Markdown under `en/` and `zh_CN/`, with matching paths in
both languages. The
[writing guide](en/contribute/writing-documentation.md) explains how to add or
update a page.
