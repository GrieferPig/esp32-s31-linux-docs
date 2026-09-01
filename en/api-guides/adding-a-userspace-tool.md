# Adding a Userspace Tool

Place target-only source in the Buildroot external package or board overlay
according to whether it is compiled or a script. Install it through the
`s31-tools` package or the owning package rather than copying it from an
untracked host path.

Every tool needs a concise usage string, deterministic exit status, diagnostics
on standard error, and stable machine-readable output when automation consumes
it. Accept device paths and credentials as runtime arguments or persistent
configuration; never compile private values into the image.

Document the command in the CLI reference, including required kernel config,
overlay, privileges, side effects, cleanup, and whether output is a stable API
or diagnostic text.
