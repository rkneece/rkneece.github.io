"""Append Option A revised records only; never merge model/test branch history."""
from pathlib import Path
import base64,collections,copy,hashlib,io,json,re,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parent
M=json.loads((ROOT/'RELEASE.json').read_text())
site=Path('sites/43cedar/interactive_map/index.html');text=site.read_text()
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(text.encode())==M['baseline_html_sha256'],'Current live source changed; refresh baseline before assembling'
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);match=pat.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before);old={p['id']:p for p in before['photos']};assert len(old)==len(before['photos'])
assert not any(p.get('islandTestSet')=='CW6-A-revised' for p in before['photos']),'Already added; do not duplicate'
published=[]
for row in M['images']:
 ident=row['id'];assert ident not in old
 assert row['review'].startswith('PASS:'),'Only exact visually accepted outputs may publish'
 file=ROOT/'restored'/row['sha256'];raw=file.read_bytes();assert sha(raw)==row['sha256']
 with Image.open(io.BytesIO(raw)) as im:
  size=list(im.size);out=io.BytesIO();im.convert('RGB').save(out,'JPEG',quality=91,optimize=True,subsampling=0)
 data=out.getvalue();uri='data:image/jpeg;base64,'+base64.b64encode(data).decode();display_sha=sha(data)
 kind=row['type'];group={'blender':'blenderImages','photoreal':'photorealImages','resource':'resourceImages'}[kind];after[group][ident]=uri
 p=dict(id=ident,imageId=ident,type=kind,stage='Proposed - Tests',floor='F1',zone='Dining Area',kind={'blender':'Option A revised · native render','photoreal':'Option A revised · AI photoreal','resource':'Option A revised · measured plan'}[kind],looking='Option A revised · '+row['label'],filename=ident+'.jpg',sourceRepo='rkneece/43-cedar-blender',modelBranch='test/island-C-west6',modelCommit=M['model_commit'],sourceSceneSHA256=M['source_scene_sha256'],designVersion='Option A revised · 84×54 · 6 inches west · three south seats',variant='Option A revised · isolated test',islandTestOption='A revised',islandTestSet='CW6-A-revised',islandTestView=row['key'],sourceImageSHA256=row['sha256'],imageSHA256=display_sha,qaStatus='CW6_EXACT_SOURCE_VISUAL_PASS',referenceStatus='TEST ONLY · approved production design unchanged',publishedAt=M['created_at'],updatedAt=M['created_at'],notes=M['notes'])
 if kind=='photoreal':p.update(sourceRenderId=row['native_id'],nativeReferenceSHA256=row['native_sha256'],source='AI photographic finish edit from '+row['native_id'],geometryStatus='Illustrative finishes matched to linked native geometry')
 elif kind=='blender':p.update(source='Isolated Option A revised Blender scene',comparisonCameraId=row.get('comparison_camera_id'),geometryStatus='Measured test geometry; selected sink installation details provisional')
 else:p.update(source='Programmatic measured plan from saved scene geometry; no AI',geometryStatus='Scaled planning exhibit; field verification remains required')
 after['photos'].append(p);published.append(dict(id=ident,type=kind,display_sha256=display_sha,source_sha256=row['sha256'],dimensions=size))
assert len(published)==17 and len(after['photos'])==len(before['photos'])+17
assert len({p['id'] for p in after['photos']})==len(after['photos'])
# Every original record, embedded image and unrelated data field must survive exactly.
assert after['photos'][:len(before['photos'])]==before['photos']
for k in ['blenderImages','photorealImages','resourceImages']:
 for ident,v in before[k].items():assert after[k][ident]==v
for k in before:
 if k not in ['photos','blenderImages','photorealImages','resourceImages','counts']:assert after[k]==before[k],k
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
result=text[:match.start(2)]+payload+text[match.end(2):];assert json.loads(pat.search(result)[2])==after
assert result[:match.start(2)]==text[:match.start(2)] and result[pat.search(result).end(2):]==text[match.end(2):]
site.write_text(result)
qa=dict(status='PASS',issue=25,label='Option A revised',before_records=len(before['photos']),after_records=len(after['photos']),new_test_records=len(published),all_original_records_and_images_unchanged=True,production_gallery_unchanged=True,UI_and_floorplans_unchanged=True,all_new_images_embedded=True,html_sha256=sha(result.encode()),new_ids=[p['id'] for p in published],published_images=published,model_branch_not_merged=True)
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps({k:v for k,v in qa.items() if k!='published_images'}),flush=True)
