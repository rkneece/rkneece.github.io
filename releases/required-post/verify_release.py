from pathlib import Path
import json,hashlib,re,io
from PIL import Image
root=Path(__file__).resolve().parent
p=Path('sites/43cedar/interactive_map/index.html');b=p.read_bytes()
expected=json.loads((root/'REQUIRED_POST_EXPECTED.json').read_text())
assert hashlib.sha256(b).hexdigest()==expected['html_sha256']
d=json.loads(re.search(rb'<script[^>]*id="appdata"[^>]*>(.*?)</script>',b,re.S)[1])
assert d['buildId']=='P135_East_Biased_Chase'
for rel,digest in expected['assets'].items():
 content=(p.parent/rel).read_bytes();assert hashlib.sha256(content).hexdigest()==digest
 Image.open(io.BytesIO(content)).verify()
assert len(d['requiredPostRevision']['updated_native'])==34
assert len(d['requiredPostRevision']['updated_photoreal'])==23
assert len(d['resourceImages'])==6
print('PASS: reviewed HTML, 60 image assets and stable image mappings')
