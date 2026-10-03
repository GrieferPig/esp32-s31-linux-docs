# Development setup

Start with [Build from source](../get-started/build-from-source.md) to install
the tools and build an image. Every build includes the full board configuration.

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
make linux rootfs radio-fs
```

A driver or device-tree change needs `make linux`; a packaged userspace or
overlay change needs `make rootfs`. The native build systems decide which changed objects need rebuilding. The
radio XIP image is linked against that kernel, so rebuild `radio-fs` and flash
kernel, rootfs/module, and radio together after integrated changes. `make all`
creates the complete matched image set. Boot
firmware changes use `make uboot`, and radio firmware changes use the
[radio build workflow](../api-guides/radio-payload-development.md).

Keep generated files under the selected `out/` tree. Shared downloads
and toolchains belong under `cache/`; never generate staged firmware in the
tracked rootfs overlay. For lasting kernel or package selections,
edit the source configuration described in
[Build configuration](../get-started/build-configuration.md).

## Test a change

Run the relevant host tests before flashing. For the repository's aggregate
checks, install `docs/requirements.txt` and `dtschema==2026.6` in a host Python
virtual environment and run:

```sh
make btstack-source
make check-host check-docs
make check-dt
```

`btstack-source` prepares the pinned source before the host suite;
`check-host` does not download it and skips its BTstack regression when the
source is absent. `check-dt` needs the project cross-toolchain; the CI alternative is
`python3 tools/checks/devicetree.py --cross-compile riscv64-linux-gnu-`.
`make check-fast` combines these checks. They validate host-side contracts and
build inputs, not electrical behavior. Then check the feature on the
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
