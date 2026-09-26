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

Use direct, ordinary English. Address the reader as “you” when it helps, and
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

Check commands against the relevant tool or build target. Show the ordinary
workflow first, followed by optional configuration and troubleshooting.
Versions can be included where needed to install compatible tools; detailed
test histories belong in linked test reports.

## Add the page to the guide

Pages are Markdown files under `en/`. Add a new page to the appropriate
section's `toctree` so it appears in the navigation. Prefer relative Markdown
links for other pages in this guide.

Keep existing page paths where practical. Preserve images that are still
referenced by the guide or the main README.

## Preview your changes

From the documentation repository, install `requirements.txt` in a Python
virtual environment and run:

```sh
make html
make linkcheck
```

Open `build/html/index.html` and check the changed pages, navigation, tables,
and code examples. For a behavior change, update the related usage guide and
reference together.
