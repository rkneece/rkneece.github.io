"""Apply reviewed canvas images to the exact owner-approved live planner."""
from pathlib import Path
import base64,copy,hashlib,io,json,re
from PIL import Image

ROOT=Path(__file__).resolve().parent
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
release=json.loads((ROOT/'canvas-release.json').read_text())
source=(ROOT/'live-before.html').read_text()
raw=source.encode()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert blob(raw)==release['base_blob_sha'],'Live HTML changed before assembly'
before=json.loads(PAT.search(source)[2]);data=copy.deepcopy(before)
photos={p['id']:p for p in data['photos']}
changed=set()
for record in release['records']:
    i=record['id'];p=photos[i];field='photorealImages' if p['type']=='photoreal' else 'blenderImages'
    value=release['images'][record['asset']]
    payload=base64.b64decode(value.split(',',1)[1],validate=True)
    assert hashlib.sha256(payload).hexdigest()==record['sha256']
    Image.open(io.BytesIO(payload)).verify()
    data[field][p['imageId']]=value
    p['designVersion']='Blue coastal canvas + BPR white mantel · 2026-10-22'
    p['renderedAt']='2026-10-22'
    p['approval']='Owner approved canvas size and publication on 2026-10-22; dimensions provisional'
    p['variant']='96 x 36 inch blue coastal gallery-wrapped canvas; existing white BPR mantel and recessed brick'
    p['notes']=p.get('notes','')+' Approved blue abstract canvas on south dining/living wall: 96x36in, center60in AFF, bottom42in, extends approximately19in into living section. '+('AI photographic edit checked against native canvas geometry.' if p['type']=='photoreal' else 'Native Blender canvas geometry; all prior mesh geometry and cameras retained.')
    changed.add(i)
data['buildId']=release['release']
data['canvasRevision']={k:v for k,v in release.items() if k!='images'}
data['canvasRevision'].update(owner_approved=True,published=True)
if 'B08' in changed:
    data['proposedPlans']['F1']=data['blenderImages'][photos['B08']['imageId']]
    data['proposedPlanInfo']['F1']['notes']+=' Approved blue coastal canvas included; prior plan geometry unchanged.'
allowed={'photos','blenderImages','photorealImages','buildId','proposedPlans','proposedPlanInfo'}
for k in before:
    if k not in allowed:assert before[k]==data[k],k
for p,q in zip(before['photos'],data['photos']):
    assert p['id']==q['id']
    if p['id'] not in changed:assert p==q,p['id']
    else:
        for k in p:
            if k not in {'notes','designVersion','renderedAt','approval','variant'}:assert p[k]==q[k],(p['id'],k)
for field in ('blenderImages','photorealImages'):
    assert data[field].keys()==before[field].keys()
    for k in before[field]:
        if k not in {photos[i]['imageId'] for i in changed}:assert data[field][k]==before[field][k]
for floor in before['proposedPlans']:
    if floor!='F1':assert data['proposedPlans'][floor]==before['proposedPlans'][floor]
rendered=PAT.sub(lambda m:m[1]+json.dumps(data,separators=(',',':')).replace('</','<\\/')+m[3],source)
assert PAT.sub('',rendered)==PAT.sub('',source),'UI/scripts changed'
out=rendered.encode();(ROOT/'index.html').write_bytes(out)
qa=dict(release=release['release'],base_blob_sha=release['base_blob_sha'],output_blob_sha=blob(out),
        output_sha256=hashlib.sha256(out).hexdigest(),updated_native_ids=sorted(i for i in changed if i.startswith('B')),
        updated_photo_ids=sorted(i for i in changed if i.startswith('R')),original_site_photos=len(data['photoImages']),
        native_images=len(data['blenderImages']),photoreal_images=len(data['photorealImages']),
        original_photos_plans_camera_positions_viewpoint_ids_unrelated_records_and_UI_preserved=True)
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa))
