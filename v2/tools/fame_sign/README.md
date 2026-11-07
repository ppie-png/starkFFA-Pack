# Hall of Fame sign (pack r37)

`fame3d.py` builds the 3D HALL OF FAME sign as ONE item model for an item display (StarkCore `TitlesModule` model
mode, config `titles.list.fame.model`):

- extruded gold letters with a dark rim (counters filled), a jewelled crown, two laurel branches and a red ribbon
  "ALL-TIME KILLS" (text from the vanilla `ascii.png` font, 3x) - greedy-meshed boxes, ~440 elements;
- `textures/item/fame/gold.png` is animated (`gold.png.mcmeta`: 80 ticks idle, then a shine band sweeps over the
  letters in 15 frames of 2 ticks); front faces are mapped planar over the canvas, side faces use `side.png`.

Grid: 240 x 80 half sign pixels, 0.2 model units each (the whole -16..32 model range), front = north. The canvas
grows towards -x because MC maps a north face texture with u0 at the east edge.

    python3 fame3d.py <out-dir>      # writes assets/starkffa/{models/item,items,textures/item/fame}

Needs numpy, scipy, pillow and the vanilla `assets/minecraft/textures/font/ascii.png` (path in `FONT`).
