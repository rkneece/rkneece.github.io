"""Owner-approved B100/R65 image-only publication; preserve current viewer."""
from pathlib import Path
import json,re,copy,base64,hashlib,io
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PAGE=ROOT/'sites/43cedar/interactive_map/index.html'
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
release=json.loads((HERE/'RELEASE.json').read_text())
raw=PAGE.read_bytes();assert blob(raw)==release['base_blob_sha'],'Viewer changed: reconcile publication first'
source=raw.decode();match=PAT.search(source);assert match
before=json.loads(match[2]);data=copy.deepcopy(before)
by_id={p['id']:p for p in data['photos']};assert set(release['scope_ids'])=={'B100','R65'}
dimensions={}
for asset in release['assets']:
    ident=asset['id'];assert ident in {'B100','R65'}
    p=by_id[ident];image=(ROOT/asset['asset_path']).read_bytes()
    assert hashlib.sha256(image).hexdigest()==asset['sha256'],ident
    with Image.open(io.BytesIO(image)) as im:dimensions[ident]=list(im.size);im.verify()
    field='blenderImages' if ident=='B100' else 'photorealImages'
    data[field][p['imageId']]='data:image/jpeg;base64,'+base64.b64encode(image).decode()
    p['designVersion']='PD1 · primary privacy door · bedroom-facing view'
    p['primaryDoorRevision']='PD1_Bedroom_Pair_Only'
    p['updatedAt']=release['updated_at']
    p.setdefault('publishedAt','2026-10-22')
    p['sourcePNG_SHA256']=release['source_native_png_sha256']
    p['publishedImageSHA256']=asset['sha256']
    p['qaStatus']='ACCEPTED_VISUAL_ARCHITECTURAL_REVIEW'
    p['notes']='Closed primary-bedroom privacy door in existing opening. From bedroom looking out: hinges LEFT; opens INWARD along bathroom wall, clear of RIGHT-side closets. Five panels remain provisional. Camera and room geometry retained.'
    if ident=='B100':p['source']=release['native_run']
    else:
        p['source']='B100';p['sourceRenderId']='B100'
        p['imageSHA256']=asset['sha256'];p['imageHashEncoding']='published JPEG'
        p['generationReferenceNativePNG_SHA256']=release['photoreal_reference_native_png_sha256']
        p['notes']+=' Photographic finish study; paired native render remains geometry authority.'
for key in ['viewpointId','cameraEyeXY','cameraTargetXY','mapX','mapY','proposedMapX','proposedMapY','mapDirectionDegrees']:
    assert by_id['B100'][key]==by_id['R65'][key],key
assert by_id['R65']['sourceRenderId']=='B100'
data['primaryDoorBedroomPairRevision']=release
data['buildId']=before['buildId']+'__PD1_Bedroom_Pair'
for old in before['photos']:
    now=by_id[old['id']]
    if old['id'] not in {'B100','R65'}:assert now==old,old['id']
    else:
        for key in ['id','imageId','type','floor','stage','zone','filename','sequence','looking','viewpointId','cameraEyeXY','cameraTargetXY','mapX','mapY','proposedMapX','proposedMapY','mapDirectionDegrees','relatedPhotos','postCoordinationRevision','postInView']:
            assert now.get(key)==old.get(key),(old['id'],key)
assert len(data['photos'])==len(before['photos'])
for key in before:
    if key not in {'photos','blenderImages','photorealImages','buildId'}:assert data[key]==before[key],key
for field in ['blenderImages','photorealImages']:
    assert set(data[field])==set(before[field])
    for ident,value in before[field].items():
        if ident not in {'B100','R65'}:assert data[field][ident]==value,(field,ident)
encoded=json.dumps(data,separators=(',',':')).replace('</','<\\/')
output=PAT.sub(lambda m:m[1]+encoded+m[3],source)
assert PAT.sub('',output)==PAT.sub('',source),'Viewer code or markup changed'
PAGE.write_text(output)
qa={'release':release['release'],'scope_ids':['B100','R65'],'base_blob_sha':blob(raw),'output_blob_sha':blob(output.encode()),'output_sha256':hashlib.sha256(output.encode()).hexdigest(),'records':len(data['photos']),'dimensions':dimensions,'all_other_records_images_plans_resources_dates_room_labels_and_viewer_code_preserved':True,'camera_locations_directions_and_source_link_preserved':True,'R09_and_coordinated_work_unchanged':True}
(HERE/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa,indent=2))
