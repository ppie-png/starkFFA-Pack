# Tooltip styles

Item component `tooltip_style` = `starkffa:<theme>` → the client uses
`textures/gui/sprites/tooltip/<theme>_background.png` + `<theme>_frame.png` (nine-slice, stretched centre).

Paper: `item.setData(DataComponentTypes.TOOLTIP_STYLE, Key.key("starkffa", "wind"))`.

| Theme | Weapon | Background (top → bottom) | Frame (top → bottom) |
|---|---|---|---|
| `wind` | Wind Mace | `#14303F` → `#0B1322` | `#B8F6FF` → `#3F86B4` |
| `hook` | Plunger Grappler | `#3A2318` → `#170D0A` | `#FFC59A` → `#B5542A` |

New theme: add it to `THEMES` in `tools/build_pack.py`, rebuild, push, update sha1.
Without the pack installed the item simply shows the vanilla tooltip.
