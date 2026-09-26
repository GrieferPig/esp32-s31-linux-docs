# Development setup

Start with [Build from source](../get-started/build-from-source.md) to install
the tools and build an image. For peripheral development, select
`S31_LEAN_RADIO=0`.

## Find the source

| Directory | Contents |
|---|---|
| `linux-esp32-s31/` | Linux kernel, drivers, device trees, and kernel configuration |
| `opensbi-esp32-s31/` | M-mode firmware and platform services |
| `u-boot-esp32-s31/` | SPL and U-Boot |
| `buildroot/` | Buildroot |
| `buildroot-external/` | Board files, packages, and rootfs configuration |
| `firmware/` | Radio and LP firmware |
| `rootfs/` | Sources for project userspace tools |
| `tools/` | Host build utilities and tests |
| `docs/` | This documentation |

The kernel, boot firmware, Buildroot, and documentation are Git submodules.
Create a branch inside the relevant submodule before editing it. The
[submodule guide](submodule-workflow.md) shows how to commit those changes.

## Rebuild after an edit

Use the parent Makefile for integrated builds:

```sh
make linux
make rootfs
```

A driver or device-tree change usually needs `make linux`. A target program,
startup script, or packaged overlay update also needs `make rootfs`. Boot
firmware changes use `make uboot`, and radio firmware changes use the
[radio build workflow](../api-guides/radio-payload-development.md).

Keep generated files under `build/`. For lasting kernel or package selections,
edit the source configuration described in
[Build profiles](../get-started/build-profiles.md).

## Test a change

Run the relevant host tests before flashing. Then check the feature on the
board, including an error case and cleanup after use. The
[HIL guide](testing-hil.md) covers automated board and peer tests.

When submitting a change, describe the problem, the fix, and how you tested
it. Include the board and wiring where they affect the result.

## Work on documentation

The docs repository has its own Python dependencies and build commands:

```sh
cd docs
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
make html
```

Open `build/html/index.html` to review the result. See
[Writing documentation](writing-documentation.md) for page structure and tone.
