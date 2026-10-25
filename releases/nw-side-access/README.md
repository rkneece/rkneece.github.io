# 43 Cedar — north-facing sink with west-side access

Isolated geometry study on the current proposed island, not a selected design.
Category: Proposed - Tests. Room: Dining Area.

## Result

The existing modeled sink and a 24-inch dishwasher opening fit on the north face of the current 66-inch east-west by 78-inch north-south countertop, with west-side plumbing access. The model retains all four current stool positions and the fixed P135 post.

- Cabinet body width: 51.85 inches.
- Northwest sink compartment outer width: 27.10 inches; clear internal width: 25.60 inches.
- Modeled sink rim envelope: 21.27 inches east-west by 16.43 inches north-south.
- Dishwasher opening: 24 inches, east of the sink, opening north.
- West service opening: approximately 29 inches along the west face by 28.5 inches high. The illustrated door leaf is 28.3 inches wide.
- Sink drain centre: approximately 12.8 inches inward from the interior west plane. This is a geometric reach measure, not a serviceability or installation approval.
- The microwave moves into the rightmost pair of cooking-wall base doors. The modeled bay is 27.57 inches wide. The retained 24-inch appliance proxy fits that bay and the modeled counter depth, with a drawer beneath it.
- West-side drawers occupy space released by moving the old west-facing dishwasher.

## What is shown

43_Cedar_NW_Access_Plan.png: dimensioned plan, north cabinet elevation and west service section.
43_Cedar_NW_Access_Views.jpg: four labelled matched model views.
results/: five full native PNG views, the closed-door editable Blender model and QA.json.

North_Workface: sink at northwest and dishwasher to its east, both used from the cooking aisle.
West_Access: hinged service door opened 90 degrees.
Service_Interior: service panel removed for illustration.
Cooking_Wall: microwave in the rightmost lower cabinet, with drawer beneath.
Pantry_Approach: relationship to the existing pantry passage.

## Limits and next checks

This fit depends on the compact modeled sink. A larger selected sink may need a larger compartment, and its manufacturer minimum cabinet size and mounting method must be verified. Countertop and sink support framing require cabinetmaker/installer detailing independent of the removable door or panel.

The illustrated white drain and red/blue water lines explain access only. Existing rough-in location, drainage, venting, shutoffs, dishwasher connections and final routing have not been surveyed or specified. No disposal, filter or other under-sink accessories are allocated.

The microwave and dishwasher are model proxies. Manufacturer cabinet opening, support, ventilation, electrical, hose routing and opening-sweep requirements remain unverified. Simultaneous dishwasher/oven opening has not been approved.

The service door projects into the west aisle when open. A removable panel could avoid a hinged leaf projecting there during service. This study retains the existing seating arrangement and does not resolve the known middle-east-stool/post circulation conflict, dining circulation or slider access.

## Reproduction and preservation

Source scene SHA256: 1b174865cb84cb2154d6b092b7c8dbe02d0ef4bd288e284bb46c41797b13fdf2.
Official Blender 5.2.2 was used for the native renders. All unrelated original room transforms/bounds/visibility were checked for preservation, except the intended local cooking-wall base cabinet changes. Authoring Dev/main and the live planner were not changed.

Place the supplied source scene as E_original.blend beside test_nw_access.py and run:
blender -b -t 6 --python-exit-code 1 --python test_nw_access.py
Then run python illustrate.py for the plan and comparison sheet.
