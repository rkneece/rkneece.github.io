# 43 Cedar agent instructions

Applies to 43 Cedar work in this repository. In the website repository, this is scoped to 43 Cedar; unrelated websites are unaffected.

For every thread involving 43 Cedar native rendering, AI photoreal generation and/or live publishing, create or reuse one GitHub tracking issue before execution. Use the central register in `rkneece/43-cedar-blender` and link all affected repositories/branches/PRs/runs. Search for an existing issue first; one thread doing rendering plus publishing normally uses one issue.

Read and follow the full [43 Cedar issue and branch workflow](https://github.com/rkneece/43-cedar-blender/blob/main/cedar_model/BRANCH_WORKFLOW.md), especially “Required issue for every rendering or live publishing thread.”

Keep the issue body current with scope, execution owner, status, source/branch heads, completed/expected outputs, blockers, next action and publishing destination. Add timestamped comments for significant events, errors/retries, saved checkpoints, pauses, handoffs, merges and verified publication. Update before pausing or ending a work turn. Record job IDs and durable source/output manifests when available; distinguish reported status from verified facts and say when runtime state is unknown.

Check related open issues before shared rendering or publishing. Coordinate overlapping geometry/cameras/live HTML through one integration owner. Preserve current user constraints, particularly isolated test branches and no-merge instructions. A tracking issue does not authorize additional rendering, merging or deployment.

Close completed issues with validation/live verification as applicable. Close stale, superseded, duplicate or abandoned issues only after checking current activity, preserving useful work and recording the reason/successor. Inactivity alone does not mean success. Reuse/reopen an issue when the same scope resumes.

Updates are made during execution. Never infer active runtime from an old start comment. The completed NW test is #16; the approved island release is #21; the fast-workflow rollout is #22. Read the latest issue comments as well as its summary.

## Central asset archive

Use the private Google Cloud archive described in [ops/cedar-archive/README.md](ops/cedar-archive/README.md). Save each completed render, photoreal, source-scene snapshot and its provenance promptly with the authenticated helper; record the verified object/manifest URI in its workstream issue. Temporary workspace files and disposable branches are not the archive. Before branch retirement, verify that the required outputs and provenance have independent archive receipts. Archival copies do not approve designs or authorize publication. New workflows archive changed committed 43 Cedar outputs; older branches and uncommitted local generation require explicit checkpoint integration. Do not claim coverage until it has been verified.

## Fast rendering and consistent updates

Read and follow the owner-approved [rendering and status policy](https://github.com/rkneece/43-cedar-blender/blob/main/cedar_model/RENDER_WORKFLOW.md) before new or resumed rendering, AI photoreal or publishing work. Routine native references default to 900px width / 12 samples with denoising; higher quality is view-specific. Preserve validated completed images. Start each matching AI edit when its own current native reference is reviewed and saved; do not wait for unrelated batch completion.

Every rendering, photoreal AND publishing thread must use a central tracking issue. During active work, update the issue at least every 10 minutes, and immediately on observed errors/blockers. Use the same timestamp, stage, verified generated/reused/reviewed/archived/published counts, last checkpoint, blocker and next action in chat and the issue. If evidence is stale or inaccessible, say runtime unknown or paused. A separate hourly health-check task covers between-turn checks; it is not a promise of 10-minute background chat updates.

## Stalled-job recovery

Before starting or resuming 43 Cedar work, read the canonical [bounded recovery and takeover policy](https://github.com/rkneece/43-cedar-blender/blob/main/cedar_model/RENDER_WORKFLOW.md#bounded-recovery-and-execution-takeover) and any central `ops/cedar-recovery/claims/ISSUE.json` on model main. Honor another owner's unexpired claim; recheck ownership before shared writes or new jobs. The hourly health task may claim and recover already-authorized stalled work, preserving completed outputs, retry limits, explicit pauses and all test/no-merge restrictions. An uncertain imagegen attempt cannot be treated as stopped merely because it is stale. Preserve late returns as separate candidates. Follow the shared retry ledger and stop repeated authentication failures until configuration is corrected.

## Commit viewer candidates before QA

- Work on an isolated `release/*` branch and record its current production baseline in the central issue. Commit and push the assembled viewer before browser QA. Record the full candidate commit SHA immediately so another session can resume from it.
- Version the viewer source, assembly scripts and small release manifests in Git. Archive original media and generated masters in the private Cedar bucket and keep the verified manifest or receipt in the tracking issue. Use the viewer's public asset paths for display derivatives. Keep private source media and private archive URLs out of the public viewer.
- Run **43 Cedar viewer candidate QA** against the committed candidate. It runs automatically when viewer files change on a release branch. For an existing candidate, dispatch on the release branch with the workflow installed and confirm that the run's commit is the expected SHA. Record the Actions URL alongside the commit in the issue.
- The shared browser check covers desktop/mobile startup and a decoded gallery image. Run release-specific checks for the affected records, mappings and controls. Record their results and the archive readback before promotion. If the candidate changes, verify the replacement commit before merging. Record the production commit and verify the live viewer after deployment.
- Keep chat and issue updates compact. Run assembly and verification on files directly. Report hashes, counts and links without pasting generated HTML, embedded images or bulk metadata. A handoff should name the issue, branch, candidate SHA, archive receipt, QA run, pending step and release owner.
