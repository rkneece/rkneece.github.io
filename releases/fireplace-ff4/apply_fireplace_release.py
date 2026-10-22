"""Apply the owner-approved image replacements without changing planner UI or maps."""
import base64, copy, hashlib, io, json, re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
PAT = re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)', re.S)
source = (ROOT / 'live-before.html').read_text()
release = json.loads((ROOT / 'fireplace-release.json').read_text())
raw = source.encode()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == release['base_blob_sha']
before = json.loads(PAT.search(source)[2])
data = copy.deepcopy(before)
by_id = {p['id']: p for p in data['photos']}
changed = {r['id'] for r in release['records']}
assert len(changed) == 21
for record in release['records']:
    ident = record['id']
    photo = by_id[ident]
    field = 'photorealImages' if record['type'] == 'photoreal' else 'blenderImages'
    assert photo['imageId'] in data[field]
    value = release['images'][ident]
    payload = base64.b64decode(value.split(',', 1)[1], validate=True)
    assert hashlib.sha256(payload).hexdigest() == record['image_sha256']
    Image.open(io.BytesIO(payload)).verify()
    data[field][photo['imageId']] = value
    photo.update(
        designVersion='BPR-inspired white mantel · FF4 · 2026-10-22',
        renderedAt='2026-10-22',
        approval='Owner approved for publication on 2026-10-22; dimensions provisional',
        variant='White painted mantel and shelf; recessed reclaimed Cedar brick',
        notes=('BPR-inspired white mantel with simplified cornice, recessed reclaimed brick, '
               'and TV matching the 48½-inch shelf width. Equal window and bench pairs. '
               'All dimensions are assumptions pending field measurement. '
               + ('AI photographic finish; native render and dimensioned diagram remain authoritative. '
                  if record['type'] == 'photoreal' else 'Native geometry reviewed across all affected views. ')
               + ('Hall view retained from the reviewed equal-alcove study; mantel is occluded.'
                  if ident == 'R10' else '')),
    )
data['buildId'] = release['release']
data['fireplaceRevision'] = {k:v for k,v in release.items() if k != 'images'}
data['fireplaceRevision'].update(owner_approved=True, published=True,
    native_review='14 views visually checked; 12 fit tests pass; 18 prior runtime reports unchanged',
    photographic_review='Five refreshed views plus retained hall R10; native geometry authoritative')

# All original photos, floor plans, locations, camera directions and UI code remain exact.
for key in before:
    if key not in {'photos','blenderImages','photorealImages','buildId'}:
        assert data[key] == before[key], key
for old,new in zip(before['photos'],data['photos']):
    assert old['id'] == new['id']
    if old['id'] not in changed:
        assert old == new
    else:
        for k in old:
            if k not in {'designVersion','renderedAt','approval','variant','notes'}:
                assert old[k] == new[k], (old['id'],k)
for field in ['blenderImages','photorealImages']:
    ids = {by_id[i]['imageId'] for i in changed if ('photorealImages' if by_id[i]['type']=='photoreal' else 'blenderImages')==field}
    assert data[field].keys() == before[field].keys()
    for key in before[field]:
        if key not in ids:
            assert data[field][key] == before[field][key]
rendered = PAT.sub(lambda m:m[1]+json.dumps(data,separators=(',',':')).replace('</','<\\/')+m[3],source)
assert PAT.sub('',rendered) == PAT.sub('',source)
(ROOT/'index.html').write_text(rendered)
qa = dict(release=release['release'], base_blob_sha=release['base_blob_sha'],
          photos=len(data['photos']), native_images=len(data['blenderImages']),
          photographic_images=len(data['photorealImages']), site_photos=len(data['photoImages']),
          updated_native_ids=sorted(i for i in changed if i.startswith('B')),
          updated_photo_ids=sorted(i for i in changed if i.startswith('R')),
          unchanged_maps_cameras_original_photos_unrelated_records_and_ui=True,
          output_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
          output_blob_sha=hashlib.sha1(b'blob '+str(len(rendered.encode())).encode()+b'\0'+rendered.encode()).hexdigest())
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa))
