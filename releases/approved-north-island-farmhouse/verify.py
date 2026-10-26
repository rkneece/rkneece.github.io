"""Verify local or live release bytes, embedded images and preserved records."""
from pathlib import Path
import base64,hashlib,io,json,re,sys,urllib.request
from PIL import Image

root=Path(__file__).resolve().parent
expected=json.loads((root/'VERIFY_EXPECTED.json').read_text())
qa=json.loads((root/'PUBLISH_QA.json').read_text())
source=sys.argv[1] if len(sys.argv)>1 else 'sites/43cedar/interactive_map/index.html'
if source.startswith('https://'):
    with urllib.request.urlopen(urllib.request.Request(source,headers={'Cache-Control':'no-cache'}),timeout=60) as response:raw=response.read()
else:raw=Path(source).read_bytes()
assert hashlib.sha256(raw).hexdigest()==qa['html_sha256'],'Served HTML differs from reviewed release'
match=re.search(r'<script id="appdata" type="application/json">(.*?)</script>',raw.decode(),re.S);assert match
data=json.loads(match[1]);rows={p['id']:p for p in data['photos']};assert len(rows)==len(data['photos'])==460
updated=set(qa['changed_ids'])|set(qa['added_ids'])
unchanged=[p for p in data['photos'] if p['id'] not in updated]
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert fingerprint(unchanged)==expected['unaffected_records_sha256']
protected=[p for p in data['photos'] if p.get('stage')=='Proposed - Tests']
assert len(protected)==54 and fingerprint(protected)==expected['test_records_sha256']
for image in qa['published_images']:
    row=rows[image['id']];group='photorealImages' if image['kind']=='photoreal' else 'blenderImages'
    value=data[group][image['id']];assert value.startswith('data:image/jpeg;base64,')
    b=base64.b64decode(value.split(',',1)[1],validate=True)
    assert hashlib.sha256(b).hexdigest()==image['display_sha256']==row['imageSHA256']
    assert row['approvedIslandRevision']=='NI1' and row['sourceImageSHA256']==image['source_sha256']
    with Image.open(io.BytesIO(b)) as im:im.verify()
report={'status':'PASS','source':source,'html_sha256':qa['html_sha256'],'records':460,
        'updated_images_verified':len(qa['published_images']),'tests_preserved':54,'unaffected_records_preserved':len(unchanged)}
(root/('LIVE_QA.json' if source.startswith('https://') else 'VERIFY_QA.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report),flush=True)
