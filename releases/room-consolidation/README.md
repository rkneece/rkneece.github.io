# Room consolidation

`rooms.json` is the floor-scoped room taxonomy shared by the data migration and viewer startup normalization. Legacy names remain searchable in `originalZone` / `zoneAliases`. Stable photo IDs, viewpoint IDs, dates, original and proposed coordinates, image payloads and render links are unchanged.

- Porch-side bedroom → Bedroom 1
- North bedroom / closets → Bedroom 2
- Fireplace / living room → Living room
- Pink shower bathroom → Primary bathroom
- Hall / tiled bathroom → Hall bathroom, with hall / closet subjects individually assigned to Bedroom hallway
- Hall / closet details and Hall / kitchen approach → Bedroom hallway
- Entrance hallway and Foyer / stairs → Entry / stairs
- First-floor layout → Whole first floor

Keep distinct spaces and cross-room subjects separate: laundry, screened porch, living/dining transition, kitchen/dining structure, second-floor rooms and second-floor roof. Mixed trim detail records retain their category rather than assigning an unsupported location.

Run `python releases/room-consolidation/apply.py input.html output.html` against the latest viewer. It verifies that only room labels and their provenance change, patches the live inline script and the retained mobile viewer source, and writes `QA.json`. `check-rooms.cjs` checks both desktop and phone room controls, cross-stage filtering and legacy-name search using Playwright.
