"""Append-only, hash-verified archive of explicitly selected 43 Cedar outputs.

Requires an authenticated gcloud CLI. This never deletes remote files or changes Git.
"""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

BUCKET = "gs://rkneece-43cedar-assets"


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


# Each archive process owns its credential cache. Keep the auth action's refreshable
# credential-source file intact; never copy a token or change IAM to recover a batch.
_AUTH_CACHE = None
_AUTH_REFRESHES = 0
_MAX_AUTH_REFRESHES = 2


def reset_auth_cache():
    global _AUTH_CACHE
    if _AUTH_CACHE is not None:
        _AUTH_CACHE.cleanup()
    _AUTH_CACHE = tempfile.TemporaryDirectory(prefix="cedar-gcloud-auth-")
    atexit.register(_AUTH_CACHE.cleanup)


def command(args, check=True):
    global _AUTH_REFRESHES
    is_storage = args[:2] == ["gcloud", "storage"]
    credential_file = os.environ.get("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE")
    isolated_auth = is_storage and credential_file and Path(credential_file).is_file()
    if isolated_auth and _AUTH_CACHE is None:
        reset_auth_cache()
    while True:
        env = os.environ.copy()
        if isolated_auth:
            env["CLOUDSDK_CONFIG"] = _AUTH_CACHE.name
        result = subprocess.run(args, check=False, capture_output=True, text=True,
                                env=env, timeout=120 if is_storage else None)
        # Only this specific inactive-session signal can reset the cache.
        # Permission, provider, checksum and ordinary transport failures stop.
        if (result.returncode and isolated_auth
                and "InactiveCredentialsError" in result.stderr
                and _AUTH_REFRESHES < _MAX_AUTH_REFRESHES):
            _AUTH_REFRESHES += 1
            print(json.dumps({
                "stage": "archive_authentication",
                "event": "inactive_credentials_cache_reset",
                "attempt": _AUTH_REFRESHES,
                "limit": _MAX_AUTH_REFRESHES,
                "at": datetime.now(timezone.utc).isoformat(),
            }), flush=True)
            reset_auth_cache()
            continue
        if check and result.returncode:
            raise subprocess.CalledProcessError(result.returncode, args,
                                                result.stdout, result.stderr)
        return result


def put_verified(path, uri):
    """Create without replacing; on a retry, validate the existing object instead."""
    expected = digest(path)
    upload = command([
        "gcloud", "storage", "cp", str(path), uri,
        "--if-generation-match=0", "--quiet",
    ], check=False)
    with tempfile.TemporaryDirectory(prefix="cedar-verify-") as scratch:
        downloaded = Path(scratch) / "object"
        read = command(["gcloud", "storage", "cp", uri, str(downloaded), "--quiet"], check=False)
        if read.returncode:
            raise RuntimeError("Archive upload/read failed: " + upload.stderr + read.stderr)
        if digest(downloaded) != expected:
            raise RuntimeError("Archive checksum mismatch: " + uri)
    # Verify the source did not change while being uploaded.
    if digest(path) != expected:
        raise RuntimeError("Source changed during upload: " + str(path))
    return expected


def selected_paths(root, paths, tracked):
    if tracked:
        roots = (["cedar_model", "studies"] if os.environ.get("GITHUB_REPOSITORY", "").endswith("/43-cedar-blender")
                 else ["sites/43cedar", "releases"])
        names = command(["git", "-C", str(root), "ls-files", "-z", "--", *roots]).stdout.split("\0")
        suffixes = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".blend", ".glb", ".gltf", ".pdf", ".json", ".txt", ".html", ".py"}
        paths = [root / name for name in names if name and Path(name).suffix.lower() in suffixes]
    found = []
    for value in paths:
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        if path.is_symlink():
            raise ValueError("Symlinks are not archive inputs: " + str(path))
        path = path.resolve()
        path.relative_to(root)
        if not path.is_file():
            raise ValueError("Expected an existing file: " + str(path))
        if path.name.startswith("gha-creds-") or ".git" in path.relative_to(root).parts:
            raise ValueError("Credential or Git-internal path rejected")
        found.append(path)
    return sorted(set(found))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--tracked", action="store_true", help="Archive eligible tracked files under 43 Cedar roots")
    parser.add_argument("--issue", type=int, help="Related issue in rkneece/43-cedar-blender")
    parser.add_argument("--receipt", type=Path, default=Path("cedar-archive-receipt.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    paths = selected_paths(root, args.paths, args.tracked)
    if not paths:
        parser.error("No archive inputs selected")
    repo = os.environ.get("GITHUB_REPOSITORY", "local")
    commit = command(["git", "-C", str(root), "rev-parse", "HEAD"], check=False).stdout.strip() or None
    manifest = {
        "schema": "43cedar-archive-v1", "repository": repo, "source_commit": commit,
        "source_ref": os.environ.get("CEDAR_SOURCE_REF", os.environ.get("GITHUB_REF")),
        "issue": f"https://github.com/rkneece/43-cedar-blender/issues/{args.issue}" if args.issue else None,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "run_url": (f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
                    if os.environ.get("GITHUB_RUN_ID") else None),
        "approval": "archive-only; no design approval or publication implied", "assets": [],
    }
    for path in paths:
        sha = digest(path)
        uri = f"{BUCKET}/43cedar/objects/sha256/{sha[:2]}/{sha}"
        put_verified(path, uri)
        asset = {"path": path.relative_to(root).as_posix(), "sha256": sha,
                 "bytes": path.stat().st_size, "uri": uri, "verified": True}
        # Preserve filename/provenance remotely per output, even if a later batch fails.
        descriptor = {k: v for k, v in manifest.items() if k != "assets"}
        descriptor["asset"] = dict(asset)
        with tempfile.TemporaryDirectory(prefix="cedar-record-") as scratch:
            record = Path(scratch) / "record.json"
            record.write_text(json.dumps(descriptor, indent=2) + "\n")
            record_uri = f"{BUCKET}/43cedar/records/sha256/{digest(record)}.json"
            put_verified(record, record_uri)
        asset["record_uri"] = record_uri
        manifest["assets"].append(asset)
        # Keep a recoverable local receipt after every verified output, before the next upload.
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(manifest, indent=2) + "\n")
        print("Verified " + path.relative_to(root).as_posix(), flush=True)
    with tempfile.TemporaryDirectory(prefix="cedar-manifest-") as scratch:
        source = Path(scratch) / "manifest.json"
        source.write_text(json.dumps(manifest, indent=2) + "\n")
        sha = digest(source)
        uri = f"{BUCKET}/43cedar/manifests/sha256/{sha}.json"
        put_verified(source, uri)
    receipt = dict(manifest, manifest_uri=uri, manifest_sha256=sha)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Archived and verified {len(paths)} files. Manifest: {uri}", flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as stream:
            stream.write(f"\n43 Cedar archive: **{len(paths)} verified files**\n\nManifest: `{uri}`\n")


if __name__ == "__main__":
    main()

