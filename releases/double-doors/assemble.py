"""Append the six approved DD1 images to the latest planner without altering prior work."""
import argparse, base64, collections, copy, hashlib, io, json, math, re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def assemble(input_path,output_path):
    release=json.loads((HERE/'RELEASE.json').read_text())
    raw=Path(input_path).read_bytes()
    assert blob(raw)==release['base_blob_sha'],'Production baseline changed; reconcile before publishing'
    source=raw.decode();match=PAT.search(source);assert match
    before=json.loads(match[2]);data=copy.deepcopy(before)
    ids={p['id'] for p in before['photos']};new_ids=[];dimensions={}
    for rec in release['records']:
        p=rec['photo'];ident=p['id'];assert ident not in ids and ident not in new_ids
        assert p['floor']=='F1' and p['viewMode']=='Perspective'
        assert all(0<=p[k]<=100 for k in ['mapX','mapY','proposedMapX','proposedMapY'])
        assert 0<=p['mapDirectionDegrees']<360
        path=ROOT/rec['asset_path'];image=path.read_bytes()
        assert hashlib.sha256(image).hexdigest()==rec['jpeg_sha256'],ident
        with Image.open(io.BytesIO(image)) as im:dimensions[ident]=list(im.size);im.verify()
        field='blenderImages' if p['type']=='blender' else 'photorealImages'
        assert p['imageId'] not in data[field]
        data[field][p['imageId']]='data:image/jpeg;base64,'+base64.b64encode(image).decode()
        data['photos'].append(p);new_ids.append(ident)
    assert len(new_ids)==6
    by_id={p['id']:p for p in data['photos']}
    for m in release['mappings']:
        b,r=by_id[m['native_id']],by_id[m['photoreal_id']]
        assert r['sourceRenderId']==b['id'] and r['source']==b['id']
        for key in ['mapX','mapY','proposedMapX','proposedMapY','mapDirectionDegrees','viewpointId','cameraEyeXY','cameraTargetXY']:
            assert b[key]==r[key],(r['id'],key)
        x,y=b['cameraEyeXY'];tx,ty=b['cameraTargetXY']
        assert abs(b['mapDirectionDegrees']-math.degrees(math.atan2(tx-x,ty-y))%360)<.011
    data['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in data['photos']))
    data['buildId']=release['release']
    data['doubleDoorRevision']={k:v for k,v in release.items() if k!='records'}
    data['doubleDoorRevision']['image_ids']=new_ids
    data['doubleDoorRevision']['owner_approved']=True
    for k in before:
        if k not in {'photos','counts','buildId','blenderImages','photorealImages'}:
            assert data[k]==before[k],k
    assert data['photos'][:len(before['photos'])]==before['photos'],'Prior photo records changed'
    for field in ['photoImages','blenderImages','photorealImages','resourceImages']:
        for key,value in before[field].items():assert data[field][key]==value,(field,key)
    encoded=json.dumps(data,separators=(',',':')).replace('</','<\\/')
    output=PAT.sub(lambda m:m[1]+encoded+m[3],source)
    assert PAT.sub('',output)==PAT.sub('',source),'Unexpected viewer code or markup change'
    # Existing Source-render links retained a search such as "R68", hiding B103.
    # Explicit cross-view navigation should select its target and reset filters.
    anchor='function populatePhoto(){'
    helper="function openLinked(id){const p=byId[id];if(!p)return;floor=p.floor;stage=p.stage;sel=id;for(const key of ['q','zone','kind','revision'])$(key).value='';draw()}\n"
    old_source="b.onclick=()=>{stage='Proposed · Render';sel=p.sourceRenderId;draw()}"
    old_related="b.onclick=()=>{stage=byId[id]?.stage||'Existing';sel=id;draw()}"
    for old in [anchor,old_source,old_related]:assert output.count(old)==1,old
    output=output.replace(anchor,helper+anchor,1).replace(old_source,'b.onclick=()=>openLinked(p.sourceRenderId)',1).replace(old_related,'b.onclick=()=>openLinked(id)',1)
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    Path(output_path).write_text(output)
    qa={'release':release['release'],'base_blob_sha':release['base_blob_sha'],'output_blob_sha':blob(output.encode()),
        'output_sha256':hashlib.sha256(output.encode()).hexdigest(),'output_bytes':len(output.encode()),
        'new_ids':new_ids,'dimensions':dimensions,'total_records':len(data['photos']),
        'native_images':len(data['blenderImages']),'photoreal_images':len(data['photorealImages']),
        'existing_records_images_plans_and_resources_preserved':True,
        'linked_view_navigation_resets_search_and_filters':True,
        'native_photo_pairs_and_six_directional_mappings_verified':True,'mappings':release['mappings']}
    (HERE/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps(qa,indent=2))
    return qa

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',default=str(ROOT/'sites/43cedar/interactive_map/index.html'))
    parser.add_argument('--output',default=str(ROOT/'sites/43cedar/interactive_map/index.html'))
    args=parser.parse_args();assemble(args.input,args.output)
