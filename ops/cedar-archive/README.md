# 43 Cedar durable asset archive

Project `cedar-assets` (293109622606), private bucket `rkneece-43cedar-assets`, region us-east4.
Setup and receipts: https://github.com/rkneece/43-cedar-blender/issues/18.

GitHub uses direct Workload Identity Federation via
`projects/293109622606/locations/global/workloadIdentityPools/cedar-github/providers/github`.
No service-account key is needed. Both authorized repositories have Object Creator and Object Viewer on this bucket only. The provider restricts numeric owner/repository IDs and trusted event types. These grants do not allow replacing or deleting objects. Owner/project administrators retain their existing rights. The workflow configures a job-scoped URL credential source so Google can request fresh short-lived GitHub tokens during longer batches. This temporary credential file is ignored, restricted to its runner workspace, and removed by the authentication action after the job.

## Save each completed output

Authenticate with `google-github-actions/auth` (id-token: write), install gcloud,
then call the helper immediately after a render/image is saved:

```sh
python ops/cedar-archive/archive.py --issue 16 \
  studies/island-NW-side-access/all-angles/NW01_native.png
```

Pass only explicit output/provenance files; never include credential files. Calls do not edit Git, merge design branches, approve images, or publish the site. In a local workspace, an authenticated gcloud installation is required; GitHub authentication does not automatically grant this chat workspace access.

Files are addressed by SHA256 under `43cedar/objects/sha256/`; original filenames and source commit/ref, issue and run are in a per-file record under `43cedar/records/sha256/` plus a separate immutable batch manifest under `43cedar/manifests/sha256/`. Every upload uses a create-only precondition, then downloads and hashes the remote bytes. If the object already exists, the helper verifies it rather than replacing it. The source is checked for modification during upload. Filenames/camera IDs are preserved in the manifest; archive existing sourceRenderId/prompt/QA JSON alongside images to retain their relationships. Archiving does not certify visual QA.

`cedar-archive-receipt.json` is updated after each verified file; a completed batch also has a remotely verified manifest URI. Save the receipt in the issue and/or as a run artifact. A GitHub artifact is a secondary checkpoint, not the permanent archive.

To restore, download an asset URI from its manifest, give it its recorded original name, and verify the SHA256:

```sh
gcloud storage cp gs://rkneece-43cedar-assets/43cedar/objects/sha256/PREFIX/HASH restored.png
sha256sum restored.png
```

## Workflows and rollout

The archive workflow performs a small upload/read smoke test, then archives tracked 43 Cedar assets from the selected snapshot. Pushes to branches containing this workflow archive the current snapshot when the relevant roots change. Manual runs support `source_ref` and a related model issue number. Website paths are limited to `sites/43cedar` and `releases`; model paths are limited to `cedar_model` and `studies`.

This catches committed outputs. For immediate protection of uncommitted generated images, the generating workflow/thread must call the helper after each saved output. Existing old branches do not acquire new workflows automatically. Do not describe all renderers as protected until each generator has this checkpoint wired in. Before retiring a test branch, archive its completed assets plus source scene, recipes and provenance; preserve the manifest link independently of that branch. Keep Git source history or a source bundle as appropriate; blob archiving alone does not preserve every source-code dependency.

The private archive is separate from public website delivery. Publishing still follows the existing review workflow; the viewer need not fetch private bucket URLs.
