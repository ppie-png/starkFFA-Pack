# HUD font `starkffa:hud`

Used in the action bar with MiniMessage: `<font:starkffa:hud>…</font>`.
Bitmap glyphs are **tinted by the text colour** (textures are white/grey) — so colour them
with `<color>` / `<gradient>`. Icons are pre-coloured: wrap them in `<white>`.

| Char | Glyph | Size | Notes |
|---|---|---|---|
| `` | bar cell | 5×7, advance 6 | 10 cells = full cooldown bar |
| `` | small diamond | 3×3 | separator between HUD parts (colour `#5A6070`) |
| `` | wind icon | 9×9 | Wind Dash (Wind Mace) — use `<white>` |
| `` `` `` `` | space | −1 −2 −4 −8 px | pixel nudging |
| `` `` `` `` | space | +1 +2 +4 +8 px | pixel nudging |

Normal text inside the same `<font:starkffa:hud>` tag still works (falls back to `minecraft:default`).

## Cooldown bar (reference rendering)
- Charging: `<white></white> <gradient:#5FB8D6:#A0F0FF>×filled</gradient><#2E3445>×empty</#2E3445> <white>2.0s`
- Ready flash (0.6 s): all 10 cells `<white>`
- Ready: all cells `#9BF6A8` + `ʀᴇᴀᴅʏ` → then the bar hides (see CLAUDE.md F3)
- Extra info after `<#5A6070></#5A6070>`
