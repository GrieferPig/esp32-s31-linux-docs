# Adding an Overlay

Create `esp32s31-overlay-NAME.dtso` in the kernel DTS directory. Give it a
unique `espressif,overlay-name` and declare every exclusive block through
`espressif,resource-claims`. Declare fixed pad ownership through
`espressif,gpio-claims`.

Route-bearing nodes use `espressif,route-name` or
`espressif,route-names`. A configurable scalar uses one
`espressif,param-name` and an explicit `espressif,param-values` allowlist. The
manager rejects values outside the allowlist.

An overlay must enable a complete functional dependency set: controller,
pinctrl route, clocks, resets, DMA channels, PHY or regulator references, and
child nodes. It must not overwrite base-tree provider ownership or silently
share a resource claim with another overlay.

Update the overlay catalog and validate DT syntax, binding schemas, list/routes/
parameters output, apply, device binding, removal behavior, persistence, and
conflict rejection.
