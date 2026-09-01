# Submodule Workflow

The parent project records exact commits for Buildroot, Linux, OpenSBI, U-Boot,
and this documentation repository.

For a submodule change:

1. enter the submodule and create the intended source commit;
2. verify its working tree and commit ID;
3. return to the parent and stage only the updated gitlink;
4. review `git diff --submodule=log`; and
5. keep unrelated parent changes unstaged.

Clones use `git submodule update --init --recursive`. A local relative submodule
URL is suitable only while both sibling repositories share the expected parent
directory; set a reachable remote URL before publishing to other machines.
