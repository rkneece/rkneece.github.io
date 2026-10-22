"""Apply the owner-approved image replacements and add Proposed Resources while preserving unrelated content."""
import base64, copy, hashlib, io, json, re
from pathlib import Path
from PIL import Image
from patch_resources_ui import patch_ui

ROOT = Path(__file__).parent
PAT = re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)', re.S)
source = (ROOT / 'live-before.html').read_text()
release = json.loads((ROOT / 'fireplace-release.json').read_text())
raw = source.encode()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == release['base_blob_sha']
before = json.loads(PAT.search(source)[2])
data = copy.deepcopy(before)
assert set(release.get('required_exterior_ids',[])) <= {p['id'] for p in before['photos']}, 'Concurrent exterior release is not present'
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
        designVersion='65-inch TV / symmetric alcoves · FF5 · 2026-10-22',
        renderedAt='2026-10-22',
        approval='Owner approved for publication on 2026-10-22; dimensions provisional',
        variant='BPR white mantel; recessed reclaimed brick; 65-inch TV; equal 39-inch cabinets',
        notes=('Provisional 144-inch alcove: 39 / 66 / 39-inch allocation, equal 24 × 54-inch single-pane windows, '
               '65-inch-class TV and white mantel shelf each 56.7 inches wide. Reclaimed brick recessed behind '
               'the white mantel frame. All dimensions are assumptions pending field measurement; selected '
               'gas-unit installation clearances still require confirmation. '
               + ('AI photographic finish; native render and dimensioned diagram remain authoritative.'
                  if record['type'] == 'photoreal' else 'Native geometry reviewed across all affected views.')),
    )
data['buildId'] = release['release']
data['proposedPlans']['F1'] = release['images']['B08']
data['proposedPlanInfo']['F1'].update(source='FF5 reviewed furnished first-floor overview',
    notes='144-inch assumed alcove, white mantel, 65-inch TV and equal window/cabinet pairs. Navigation reference; all measurements remain provisional.')
data['fireplaceRevision'] = {k:v for k,v in release.items() if k not in {'images','resourceImages'}}
data['fireplaceRevision'].update(owner_approved=True, published=True,
    native_review='14 views visually checked; 12 fit tests pass; 18 prior runtime reports unchanged',
    photographic_review='Six refreshed views visually checked; native geometry authoritative')

# Reference images are catalog entries, never camera locations.
data['resourceImages'] = release['resourceImages']
for resource in release['resources']:
    assert resource['id'] not in by_id
    assert resource['floor'] in {'F1','F2'}
    assert resource['stage']=='Proposed · Resources' and resource['type']=='resource'
    assert not any(k in resource for k in ['mapX','mapY','proposedMapX','proposedMapY'])
    Image.open(io.BytesIO(base64.b64decode(data['resourceImages'][resource['imageId']].split(',',1)[1]))).verify()
    data['photos'].append(resource)
data['proposedResources']={'section':'proposed-resources','records':[r['id'] for r in release['resources']],
    'notes':'Historical references retain their stated date and assumptions; field measurements remain outstanding.'}

# All original photos, floor plans, locations, camera directions and UI code remain exact.
for key in before:
    if key not in {'photos','blenderImages','photorealImages','buildId','proposedPlans','proposedPlanInfo','fireplaceRevision'}:
        assert data[key] == before[key], key
for key in before['proposedPlans']:
    if key != 'F1':
        assert data['proposedPlans'][key] == before['proposedPlans'][key]
        assert data['proposedPlanInfo'][key] == before['proposedPlanInfo'][key]
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
rendered=patch_ui(rendered)
(ROOT/'index.html').write_text(rendered)
qa = dict(release=release['release'], base_blob_sha=release['base_blob_sha'],
          photos=len(data['photos']), native_images=len(data['blenderImages']),
          photographic_images=len(data['photorealImages']), site_photos=len(data['photoImages']),
          updated_native_ids=sorted(i for i in changed if i.startswith('B')),
          updated_photo_ids=sorted(i for i in changed if i.startswith('R')),
          unchanged_existing_plans_cameras_original_photos_and_unrelated_records=True,
          resources_section_added=True, exterior_photo_ids_preserved=[p['id'] for p in before['photos'] if p['id'].startswith('ZEXT')], resource_ids=[r['id'] for r in release['resources']],
          proposed_first_floor_navigation_overhead_updated=True,
          output_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
          output_blob_sha=hashlib.sha1(b'blob '+str(len(rendered.encode())).encode()+b'\0'+rendered.encode()).hexdigest())
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa))

# Owner-authorized production assembly retry after branch integration, 2026-10-22.
