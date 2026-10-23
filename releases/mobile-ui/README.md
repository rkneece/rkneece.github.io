# 43 Cedar mobile navigation

Presentation-only release for the existing HTML viewer. Run
`python releases/mobile-ui/apply_mobile_ui.py` against the latest production
development checkout. The assembler preserves the embedded appdata bytes exactly,
including every photo, image, stable ID, coordinate, source revision and approval.

## Behavior

- Up to 1100 px: sticky floor / room / category breadcrumbs, bottom-sheet choices,
  advanced filter sheet and persistent Gallery / Map switch.
- Gallery thumbnails open a full-screen viewer immediately. Closing or browser
  Back restores the browsing position. Previous/next, keyboard arrows, swipe,
  pinch, drag and explicit zoom/fit controls are supported.
- Map uses the available viewport, with pinch/drag/fit, scale-aware grouping of
  nearby viewpoints, marker preview cards and retained view transforms.
- Source-render comparison has a return action and keeps gallery filters intact.
- Details and source information stay available without occupying image space.
- Desktop retains side-by-side map and selected photo, ordinary filters and the
  gallery. Reference resources and the #proposed-resources entry point remain.
- Embedded images use cached in-memory Blob URLs to avoid copying their Base64
  strings into every image element. Existing relative photo asset references are
  retained as well; keep the adjacent assets directory with an offline copy.
- No external JS/CSS libraries, image changes, geometry changes or remapping.

## Verification

`node --check releases/mobile-ui/viewer.js`

`node releases/mobile-ui/test_panzoom.cjs`

The assembler writes ASSEMBLY_QA.json with input/output and embedded data hashes.
See BROWSER_QA.json for reviewed browser behavior and verification limits.

`prepare_qa.py DIST` creates an untracked asset-separated browser fixture for
managed preview, which times out transferring the full 33 MB HTML. This
fixture uses the same JS/CSS, complete photo records and identical image bytes;
it also keeps one real embedded image to exercise Blob decoding. Never publish
the QA fixture or QA assets. Only the assembled index.html is published.
