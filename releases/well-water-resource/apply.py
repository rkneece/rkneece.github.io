"""Add the reviewed well and accessory-unit water diagram to Proposed Resources."""
import base64
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIEWER = Path("sites/43cedar/interactive_map/index.html")
FILENAME = "43_Cedar_Well_and_Accessory_Water.png"
RESOURCE_ID = "RES30"
COUNT_KEY = "F1|Proposed · Resources"
BASELINE = "2473ba61c4bdd42e26da7eddd5c8aa7cc22293ea7f54b3c6676cf6c433b143a3"
IMAGE = "d1cc3c644de9e79e76142f63518a0e20a6be4f00bcd7bc4ae1d44d2aeacf227f"
STAMP = "2026-11-08T20:36:42Z"
APPDATA = re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)', re.S)

def digest(data):
    return hashlib.sha256(data).hexdigest()

raw = VIEWER.read_bytes()
assert digest(raw) == BASELINE, "Viewer baseline changed. Refresh and revalidate."
page = raw.decode()
match = APPDATA.search(page)
before = json.loads(match[2])
data = json.loads(match[2])
image = (ROOT / FILENAME).read_bytes()
assert digest(image) == IMAGE
assert all(row["id"] != RESOURCE_ID for row in data["photos"])
assert RESOURCE_ID not in data["resourceImages"]
assert RESOURCE_ID not in data["proposedResources"]["records"]
row = {
    "id": RESOURCE_ID,
    "imageId": RESOURCE_ID,
    "type": "resource",
    "stage": "Proposed · Resources",
    "floor": "F1",
    "zone": "Site utilities",
    "kind": "Coordination diagram",
    "looking": "Shared well and accessory-unit water service",
    "filename": FILENAME,
    "source": "Revised boundary survey and crawlspace equipment photos",
    "referenceStatus": "Concept for contractor review · verify underground routes and check valve",
    "designVersion": "Water service concept · November 8, 2026",
    "notes": "A proposed short cold-water branch from the existing well discharge serves the accessory unit. The existing pressure tank and switch stay in the house crawlspace. A local electric tank heater supplies the accessory-unit shower and sink. The well pump, pipe and cable routes, and check valve location require field verification. Use a house-fed cold line if the well-side tee cannot share pressure with the existing switch and tank.",
    "publishedAt": STAMP,
    "updatedAt": STAMP,
    "imageSHA256": IMAGE,
}
data["photos"].append(row)
data["resourceImages"][RESOURCE_ID] = "data:image/png;base64," + base64.b64encode(image).decode()
data["proposedResources"]["records"].append(RESOURCE_ID)
data["counts"][COUNT_KEY] += 1
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
published = page[:match.start(2)] + payload + page[match.end(2):]
after_match = APPDATA.search(published)
after = json.loads(after_match[2])
assert after["photos"].pop() == row
assert base64.b64decode(after["resourceImages"].pop(RESOURCE_ID).split(",", 1)[1], validate=True) == image
assert after["proposedResources"]["records"].pop() == RESOURCE_ID
after["counts"][COUNT_KEY] -= 1
assert after == before
assert page[:match.start(2)] == published[:after_match.start(2)]
assert page[match.end(2):] == published[after_match.end(2):]
output = published.encode()
VIEWER.write_bytes(output)
qa = {
    "status": "PASS",
    "issue": 35,
    "resource_id": RESOURCE_ID,
    "baseline_html_sha256": BASELINE,
    "html_sha256": digest(output),
    "image_sha256": IMAGE,
    "photos_before": len(before["photos"]),
    "photos_after": len(data["photos"]),
    "all_other_records_preserved": True,
    "viewer_shell_byte_identical": True,
}
(ROOT / "PUBLISH_QA.json").write_text(json.dumps(qa, indent=2) + "\n")
print(json.dumps(qa), flush=True)
