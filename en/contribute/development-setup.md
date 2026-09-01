# Development Setup

Initialize all submodules and confirm their recorded revisions before editing.
Use the parent Makefile for integrated builds and component-local build commands
only when their output directory, cross compiler, and configuration match the
parent project.

Keep changes in the repository that owns the source. Commit a modified
submodule before updating its parent gitlink. Preserve unrelated dirty files,
generated binaries, local credentials, and hardware logs outside commits.

For documentation work, install `requirements.txt`, run `make html` and
`make linkcheck`, scan Markdown for private paths or identifiers, and confirm
the parent README still resolves `docs/README.md` and `docs/bootlog.png`.
