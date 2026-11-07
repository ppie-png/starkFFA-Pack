# Frost Slam assets (pack r38, StarkCore r75)

`frost_assets.py` writes three things under `<out>/assets/starkffa/`:

- `fx_crystal` - 3D ice crystal shard (5 tapering tiers, alternately turned 45 / 22.5 deg) for item displays:
  the Frost Slam eruption, the freeze cocoon and its shatter (`weapons/Fx.crystal`, `GlacialSlam`).
  Foot at model y 0, centred on x/z 8: StarkCore lifts it by +0.5 so the foot sits on the display origin.
- `fx_frost` - flat frost-crack decal (radial cracks branching at ~60 deg + impact rings + rime), white, tinted by
  custom_model_data colour (Frost Slam ground, Wind Mace sky-smash crater).
- `frost_slam` - the weapon as a 3D ice-crystal mace (steel shaft, cyan grip wrap, silver collar, diamond ice head with
  a glowing core band (`light_emission` 15), crown spike, 4 side spikes, icicles). Display transforms = vanilla
  `handheld_mace` with the z angle -45 (the model stands upright, the vanilla flat mace lies diagonal), the whole
  model sits 2.2 units low so the grip is where the vanilla grip is.

    python3 frost_assets.py <out-dir>

`mcrender.py` (Blender bpy 5.x) renders previews: `compare` (old flat vs new 3D under the same display transforms),
`turn` (4 sides), `crystal`.
