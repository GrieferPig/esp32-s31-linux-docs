# Working with submodules

The parent repository includes Linux, OpenSBI, U-Boot, Buildroot, and the
documentation as submodules. Each has its own commits and branches.

## Get the source

For a new checkout, follow [Build from source](../get-started/build-from-source.md)
to select the documented parent commit, its submodule revisions, and the
matching ESP-IDF/toolchain versions. A submodule update uses the commits
recorded by the selected parent revision; it does not update each component
to the tip of its branch.

For an existing checkout after pulling parent changes:

```sh
git submodule update --init --recursive
```

Commit or save local edits before updating a submodule.

## Make a change

Enter the submodule and create a branch. For example, for a kernel change:

```sh
cd linux-esp32-s31
git switch -c my-driver-change
```

Edit and test the files, then stage the relevant paths and commit them inside
that repository. Push the branch to a reachable remote when the change is
ready to share.

## Update the parent repository

Return to the parent and record the new submodule revision:

```sh
cd ..
git add linux-esp32-s31
git diff --cached --submodule=log
git commit -m "Update Linux for driver change"
```

The parent records the component commit, while the edited files remain in the
component repository. Push the component commit before publishing the parent
change so other developers can check it out.

The same workflow applies to `docs/` and the boot-firmware submodules.

## Review your checkout

```sh
git status
git submodule status
git diff --submodule=log
```

Run `git status` inside a submodule to see its file changes. This is useful
when the parent reports a modified component without showing the individual
files.
