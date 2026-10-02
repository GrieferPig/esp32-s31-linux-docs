# Writing documentation

Write for someone trying to use or develop the port. Start with what the
feature does, show how to use it, and explain the settings that matter for the
task.

## Structure a page

Use a short introduction and descriptive headings. For a procedure, use
numbered steps such as “Install the tools”, “Build the image”, and “Flash the
board”. Put a command after the explanation that introduces it, then describe
what the reader should see or do next.

Reference pages can use tables for options, limits, and return values. Keep
implementation details after the usage examples so a reader can get started
without reading the driver design first.

## Tone and wording

Use clear, ordinary language. Address the reader as “you” when it helps, and
use the names shown by the tools. For example:

> To enable I2C0, run `s31-overlay apply i2c0`. The selection is saved and
> restored at boot.

Explain restrictions where they affect a choice or command. A flashing warning
belongs beside the flashing command; a transfer-size limit belongs in the
peripheral reference. Link to an existing explanation instead of repeating
background or warnings on every page.

## Examples

State whether commands run on the host or the board. Use neutral example
names and explain values the reader needs to replace. Keep passwords and
private keys out of examples.

Before changing a behavior claim, search the implementation and its callers,
configuration, or tests. For example, check a command's argument parser, its
handler, and a usage test; check a build option where it is assigned and where
it affects the final configuration. Link the relevant source beside precise
contracts or limitations. Distinguish a source check from a successful hardware
run, and link a dated run artifact when claiming tested behavior.

Show the ordinary
workflow first, followed by optional configuration and troubleshooting.
Versions can be included where needed to install compatible tools; detailed
test histories belong in linked test reports.

## Add the page to the guide

Pages are Markdown files under `en/` and `zh_CN/`, with the same relative path
in each language. Update both versions when changing a command, limit or
workflow. Translate the prose and headings; preserve executable examples,
identifiers and command output. Use an explicit shared label when linking to a
section whose translated heading differs. Define it as `(shared-label)=`
before the heading and link to it with `[section title](shared-label)`;
`page.md#heading-slug` links use the heading text instead of explicit labels.

Add a new page to the appropriate section's `toctree` in both languages so it
appears in the navigation. Give it one toctree parent, and use ordinary links
from other relevant pages. Prefer relative Markdown links within the guide.

Keep existing page paths where practical. Preserve images that are still
referenced by the guide or the main README.

## Preview your changes

From the documentation repository, install `requirements.txt` in a Python
virtual environment and run:

```sh
make html SPHINXOPTS="-W --keep-going"
python3 -m http.server --bind 127.0.0.1 --directory build/html 8000
```

Open `http://127.0.0.1:8000/` and check the changed pages, navigation, tables,
search results and code examples in both languages. Stop the server with Ctrl+C
when finished. Before submitting changes, check external links:

```sh
make linkcheck SPHINXOPTS="-W --keep-going"
```

`make html` runs Sphinx separately with
`language=en` and `language=zh_CN`, then builds the landing page. This localizes
the generated navigation and search as well as the page text.

The language dropdown comes from `sphinx_rtd_theme`. For GitHub Pages,
`conf.py` supplies local translation URLs to the theme's dropdown renderer;
Read the Docs hosting supplies its own data. Check switching from a nested
page and from search, and confirm that each language's sidebar contains only
that language. For a behavior change, update the related usage guide and
reference together.
