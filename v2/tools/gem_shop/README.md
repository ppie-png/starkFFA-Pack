# Gem shop (pack r40, StarkCore r80)

- `gen.py` - shop art: open 5/6-row backgrounds (`bg5`, `bg6`, `bg6t` with rarity row bands), 18 px rarity tiles
  (`tile_<kind>`), state badges (`badge_owned` / `badge_equipped` / `badge_sale`) and the row label fonts
  `starkffa:shop_r0..r5` (the vanilla ascii + nonlatin_european sheets + STARK symbols + icons moved down to a GUI row:
  text top = 23 + 18 * row). Glyphs U+E290-E292 (backgrounds), U+E2A0 + kind*6 + row (tiles), U+E2E0 + badge*6 + row
  (badges) in `starkffa:gui`. Every tile/badge glyph is 18 px wide (advance 19) - StarkCore `ShopArt` relies on it.
- `fontw.py` - glyph advances of the vanilla bitmap fonts (StarkCore `ShopArt.W_ADV` is generated from it).
- `palette.py` - the ONE source of the animated name styles: 8 exact marker colours per style + its shader kind. It
  writes the GLSL table (`STARK_PAL`, `STARK_KIND`) and the Java table (`NameStyle.PALETTE`) - change both together.
- `stark_styles.glsl` - the name-style code that is put into the vanilla text vertex shaders:
  `stark_text_75/assets/minecraft/shaders/core/rendertype_text.vsh` (1.21.11, pack format 75) and
  `stark_text_97/assets/minecraft/shaders/core/text.vsh` (26.3, pack format 97), applied as pack overlays. A glyph in an
  exact marker colour (or the shadow rgb(6, 3, 16 + style)) is animated, every other colour is drawn as before.
- `validate.py` - compiles both shaders with glslang (26.3 = Vulkan 1.2 SPIR-V like the game's shaderc, all define
  variants; 1.21.11 = GLSL 330). A shader that does not compile makes the client drop the WHOLE pack - always run it.
- `build_pack.py` - r39 zip + shop art + overlays -> `starkffa-pack-r40.zip` (sorted, fixed timestamps).
- Tested in real clients (Prism camera): vanilla 26.3 (OpenGL, NVIDIA) and vanilla 1.21.11 (Java 21).
