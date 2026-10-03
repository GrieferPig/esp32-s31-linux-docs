# Development setup

Start with [Build from source](../get-started/build-from-source.md) to install
the tools and build the standard full-board image.

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

Integrated native outputs are under `out/`; LP firmware and generated rootfs
files are staged in `out/staging/` rather than the source overlay. Shared
downloads/toolchains remain in `cache/`, and verified matched images are published
under `dist/`. Component builds alone do not publish a new matched set. Finish
with `make image`, then use `make flash-existing-all` to deploy that set.
For lasting kernel or package selections, edit the source inputs in
[Build configuration](../get-started/build-configuration.md).

## Test a change

Run host regressions from the parent repository root before flashing:

```sh
make check-host
```

This target checks the layout and runs `tools/tests`, `tests`, and the GPIO
shell regressions. It needs Python, the source submodules, a host C compiler,
and the build tools installed by the source-build guide. Prepare pinned
BTstack sources with `make btstack-source` first; checks do not download.
Use `make fetch` when also preparing the full firmware build.

After activating the documentation environment described below, install the
DT schema dependency used by CI. With the project toolchain installed, run the
combined host, strict-documentation, and device-tree checks:

```sh
python -m pip install dtschema==2026.6
make check-fast
```

`check-dt` uses the project cross compiler. The fast-checks workflow instead
installs `gcc-riscv64-linux-gnu` and invokes
`python3 tools/checks/devicetree.py --cross-compile riscv64-linux-gnu-`. Both paths
check schemas, compiled device trees, and merged overlays.

Then check the feature on the board, including an error case and cleanup
after use. Host checks do not establish electrical or radio behavior. The
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

Use the local HTTP preview in [Writing documentation](writing-documentation.md)
to review the result and search. That guide also covers page structure and tone.
Return to the parent repository with `cd ..` before running parent Make targets.
