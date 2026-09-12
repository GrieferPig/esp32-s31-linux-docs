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
0xBC0000  HIL scratch (64 KiB)
0xBD0000  root SquashFS
0x1000000 end
```

The kernel and rootfs slots are sized by the parent build. Packaging must reject
an artifact that exceeds its slot rather than truncating or overlapping the
next partition. `flash-all` skips the persist slot. Combined-image generation
does not include a persist filesystem, but flashing the resulting contiguous
file also writes its padding across that slot; it is not a configuration-
preserving update method.

Persist occupies 576 KiB from `0xB30000` to `0xBC0000`; HIL scratch is
a separate 64 KiB partition. Slot-wise updates preserve both.
