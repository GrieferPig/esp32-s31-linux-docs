# Flash Layout

The 16 MiB NOR map is shared by packaging and partial-flash targets.

```text
0x000000  reserved/ROM-visible area
0x002000  SPL application
0x100000  U-Boot/OpenSBI FIT
0x300000  base DTB
0x310000  radio SquashFS
0x500000  Linux xipImage
0xB30000  persistent JFFS2
0xBD0000  root SquashFS
0x1000000 end
```

The kernel and rootfs slots are sized by the parent build. Packaging must reject
an artifact that exceeds its slot rather than truncating or overlapping the
next partition. Persist is preserved by normal combined-image generation and
normal `flash-all` behavior.
