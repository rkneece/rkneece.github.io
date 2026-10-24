# Room consolidation · rooms-2

Canonical first-floor room names follow the owner-approved groupings:

- Porch-side bedroom → Bedroom 1
- North bedroom / closets → Bedroom 2
- Fireplace / living room → Living room
- Primary bathroom and Pink shower bathroom → Bedroom 1 Bath
- Entry / stairs, Foyer / stairs, Entrance hallway and Trim / staircase details → Foyer / Stairs
- Dining area, Kitchen and Kitchen / dining structure → Dining Area
- Laundry closet, Bedroom hallway, Hall / closet details and Hall / kitchen approach → Downstairs Hallway
- Hall / tiled bathroom → Hall bathroom, with individual hall subjects assigned to Downstairs Hallway
- First-floor layout → Whole first floor

`rooms.json` supplies the migration and viewer startup rules. Aliases map directly to the final room name so historical imports do not recreate old categories. Original names remain searchable in `originalZone` and `zoneAliases`.

Run `python releases/room-consolidation/apply.py input.html output.html` against the latest viewer. It preserves all image assets, photo IDs, viewpoint IDs, coordinates, dates and source-render links, patches the retained viewer source and writes `QA.json`. The Chromium checks exercise all four renamed groups across stages at desktop and phone widths, legacy kitchen search and matching mobile/desktop room choices.
