"""Archive changed tracked outputs on a push, excluding infrastructure-only changes."""
import json
import os
from pathlib import Path
import subprocess
import sys

from archive import selected_paths

event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
before = event.get("before", "")
if not before or set(before) == {"0"}:
    # A newly created branch has no previous output delta; use a manual snapshot
    # for backfill rather than repeatedly copying the entire historical model.
    print("New branch: connectivity checked; use snapshot for historical outputs.")
    raise SystemExit(0)
changed = subprocess.run(["git", "diff", "--name-only", "--diff-filter=ACMRT", "-z", before, "HEAD"],
                         capture_output=True, text=True, check=True).stdout.split("\0")
eligible = {p.relative_to(Path.cwd()).as_posix() for p in selected_paths(Path.cwd(), [], True)}
paths = sorted(set(changed) & eligible)
if paths:
    subprocess.run([sys.executable, "ops/cedar-archive/archive.py",
                    "--receipt", "archive-receipts/changed.json", *paths], check=True)
else:
    print("No changed 43 Cedar output/provenance files to archive.")
