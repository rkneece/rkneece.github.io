# 43 Cedar agent instructions

Applies to 43 Cedar work in this repository. In the website repository, this is scoped to 43 Cedar; unrelated websites are unaffected.

For every thread involving 43 Cedar native rendering, AI photoreal generation and/or live publishing, create or reuse one GitHub tracking issue before execution. Use the central register in `rkneece/43-cedar-blender` and link all affected repositories/branches/PRs/runs. Search for an existing issue first; one thread doing rendering plus publishing normally uses one issue.

Read and follow the full [43 Cedar issue and branch workflow](https://github.com/rkneece/43-cedar-blender/blob/main/cedar_model/BRANCH_WORKFLOW.md), especially “Required issue for every rendering or live publishing thread.”

Keep the issue body current with scope, execution owner, status, source/branch heads, completed/expected outputs, blockers, next action and publishing destination. Add timestamped comments for significant events, errors/retries, saved checkpoints, pauses, handoffs, merges and verified publication. Update before pausing or ending a work turn. Record job IDs and durable source/output manifests when available; distinguish reported status from verified facts and say when runtime state is unknown.

Check related open issues before shared rendering or publishing. Coordinate overlapping geometry/cameras/live HTML through one integration owner. Preserve current user constraints, particularly isolated test branches and no-merge instructions. A tracking issue does not authorize additional rendering, merging or deployment.

Close completed issues with validation/live verification as applicable. Close stale, superseded, duplicate or abandoned issues only after checking current activity, preserving useful work and recording the reason/successor. Inactivity alone does not mean success. Reuse/reopen an issue when the same scope resumes.

Updates are made during execution; do not imply background monitoring. Current “Investigate Island Thread” work is tracked in https://github.com/rkneece/43-cedar-blender/issues/17.

## Central asset archive

Use the private Google Cloud archive described in [ops/cedar-archive/README.md](ops/cedar-archive/README.md). Save each completed render, photoreal, source-scene snapshot and its provenance promptly with the authenticated helper; record the verified object/manifest URI in its workstream issue. Temporary workspace files and disposable branches are not the archive. Before branch retirement, verify that the required outputs and provenance have independent archive receipts. Archival copies do not approve designs or authorize publication. New workflows archive changed committed 43 Cedar outputs; older branches and uncommitted local generation require explicit checkpoint integration. Do not claim coverage until it has been verified.
