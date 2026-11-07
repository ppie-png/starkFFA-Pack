# Statue joints (pack r36)

BetterModel draws every player limb as a hollow shell of pixel quads. When an elbow, knee or the torso bends, the
open ends show a wedge you can see through. `pack_joints.py` post-processes BetterModel's limb models inside the
STARK pack:

- every lower joint piece (forearms, slim forearms, forelegs, waist, chest) gets an octagonal prism around its bending
  axis, tinted with the piece's boundary pixel row (round, so it fills the gap at any angle and hides while straight);
- the side faces of those pieces move 0.02-0.04 px inwards, so overlapping pieces never z-fight.

Only `assets/bettermodel/models/player_limb/<limb>_<n>.json` of those limbs change.

**Run it again after every BetterModel update that regenerates the player limb models:**

    python3 pack_joints.py <pack-in.zip> <pack-out.zip>

It refuses a pack that was already processed. `uvmodels.json` = BetterModel 3.6.0-534 DynamicUV layout
(SkinManagerImpl); a newer BetterModel with a different limb layout needs a fresh extract.
