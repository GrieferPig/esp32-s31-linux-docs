# Prerequisites

Use a Linux environment with Git submodule support, GNU Make, a POSIX shell,
Python 3, device-tree compiler, host C/C++ build tools, filesystem image tools,
and USB/serial access appropriate to the target board.

Clone the parent repository recursively so the Buildroot, Linux, OpenSBI,
U-Boot, and documentation revisions remain aligned:

```sh
git clone --recurse-submodules <repository-url>
```

The integrated Makefile can fetch the configured RISC-V musl toolchain. A radio
payload build additionally needs the pinned ESP-IDF environment and any
redistributable inputs allowed by the project license policy.

Before flashing, identify the correct serial/download device without embedding
its workstation-specific path in scripts or documentation. Stop programs that
own the port, and preserve persistent flash unless the intended operation
explicitly replaces it.
