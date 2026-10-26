"""Refresh only the owner-approved NI1 views; preserve all isolated test content."""
from pathlib import Path
import base64,collections,copy,hashlib,io,json,re
from PIL import Image

root=Path(__file__).resolve().parent
release=json.loads((root/'RELEASE.json').read_text())
site=Path('sites/43cedar/interactive_map/index.html')
text=site.read_text()
assert hashlib.sha256(text.encode()).hexdigest()==release['baseline_html_sha256'],'Live-source baseline moved; rebase before assembly'
pattern=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
match=pattern.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
old={r['id']:r for r in before['photos']};rows={r['id']:r for r in after['photos']}
native={r['id']:r for r in release['native']}
stamp=release['created_at']
protected={r['id'] for r in before['photos'] if r.get('stage')=='Proposed - Tests'}
assert len(protected)>0

def asset(sha):
    p=root/'restored'/sha
    raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha
    with Image.open(io.BytesIO(raw)) as im:
        size=list(im.size);out=io.BytesIO()
        im.convert('RGB').save(out,'JPEG',quality=91,optimize=True,subsampling=0)
    data=out.getvalue()
    return 'data:image/jpeg;base64,'+base64.b64encode(data).decode(),hashlib.sha256(data).hexdigest(),size

def metadata(row,source_sha,source_id,display_hash):
    row.update(updatedAt=stamp,imageSHA256=display_hash,sourceImageSHA256=source_sha,
        sourceSceneSHA256=release['source_scene_sha256'],validatedCombinedSceneSHA256=release['source_scene_sha256'],
        approvedIslandRevision='NI1',designVersion='Approved NI1 north sink/DW + cooking-wall microwave + smooth apron',
        modelCommit=release['model_commit'],sourceRepo='rkneece/43-cedar-blender',
        qaStatus='NI1_NATIVE_AND_PHOTOREAL_REVIEW_PASS',referenceStatus='OWNER APPROVED · NI1',
        approval='Owner approved selected NI1 proposal; exact-source visual QA passed',
        variant='Approved smooth farmhouse sink with adjacent north-face dishwasher',
        notes='Approved NI1: smooth white single-bowl farmhouse apron sink and dishwasher on the island north workface; microwave drawer under the white cooking counter. West plumbing access retained. Fixed post and existing coordinated room geometry retained. Native model dimensions and selected-product installation details remain provisional. AI images illustrate finishes against the linked native camera; hidden fixtures stay hidden.')
    row.setdefault('publishedAt',stamp)
    row['sourceRenderId']=source_id
    row['nativeReferenceSHA256']=native[source_id]['sha256']
    row['sourcePNG_SHA256']=native[source_id]['sha256']

changed=[];published=[]
for ident in release['affected_native_records']:
    source_id=release['aliases'].get(ident,ident);record=native[source_id]
    assert ident in rows and ident not in protected
    uri,sha,size=asset(record['sha256'])
    after['blenderImages'][ident]=uri
    metadata(rows[ident],record['sha256'],source_id,sha)
    rows[ident].update(sourceType='Blender render',source='Approved NI1 integrated native scene',geometryStatus='Reviewed NI1 native geometry',renderedAt=release['native_rendered_on'])
    changed.append(ident);published.append({'id':ident,'kind':'native','source_id':source_id,'source_sha256':record['sha256'],'display_sha256':sha,'dimensions':size})

for record in release['photoreal']:
    ident=record['id'];assert record['review'].startswith('PASS:') and ident in rows and ident not in protected
    uri,sha,size=asset(record['output_sha256'])
    after['photorealImages'][ident]=uri
    metadata(rows[ident],record['output_sha256'],record['native'],sha)
    rows[ident].update(sourceType='AI image edit from exact NI1 Blender reference',source=record['native'],geometryStatus='Reviewed native camera; AI photographic finish is illustrative',generatedAt=record['generated_at'] if 'generated_at' in record else stamp)
    changed.append(ident);published.append({'id':ident,'kind':'photoreal','source_id':record['native'],'source_sha256':record['output_sha256'],'display_sha256':sha,'dimensions':size})

added=[]
for ident,template_id in release['detail_templates'].items():
    assert ident not in rows
    row=copy.deepcopy(old[template_id]);record=native[ident]
    row.update(id=ident,imageId=ident,type='blender',stage=old['B39']['stage'],kind='Approved NI1 native detail',filename=ident+'_approved_native.jpg',viewpointId='NI1-DETAIL-'+ident,modelBranch='main',publishedAt=stamp,updatedAt=stamp)
    uri,sha,size=asset(record['sha256']);after['blenderImages'][ident]=uri
    metadata(row,record['sha256'],ident,sha)
    row.update(sourceType='Blender render',source='Approved NI1 integrated native scene',geometryStatus='Reviewed NI1 native detail',renderedAt=release['native_rendered_on'])
    after['photos'].append(row);rows[ident]=row;added.append(ident)
    published.append({'id':ident,'kind':'native_detail','source_id':ident,'source_sha256':record['sha256'],'display_sha256':sha,'dimensions':size})

assert len(changed)==44+29 and len(added)==5
assert len(after['photos'])==len(before['photos'])+5
assert len(rows)==len(after['photos'])
for ident,row in old.items():
    if ident not in changed:assert rows[ident]==row,('Unexpected record change',ident)
assert all(rows[i]==old[i] for i in protected),'An isolated test record changed'
for key in before:
    if key not in ['photos','blenderImages','photorealImages','counts']:assert before[key]==after[key],key
for group,allowed in [('blenderImages',set(release['affected_native_records'])|set(added)),('photorealImages',{r['id'] for r in release['photoreal']})]:
    for ident,value in before[group].items():
        if ident not in allowed:assert after[group][ident]==value,(group,ident)
after['counts']=dict(collections.Counter(r['floor']+'|'+r['stage'] for r in after['photos']))
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
output=text[:match.start(2)]+payload+text[match.end(2):]
assert json.loads(pattern.search(output)[2])==after
assert output[:match.start(2)]==text[:match.start(2)]
assert output[pattern.search(output).end(2):]==text[match.end(2):]
site.write_text(output)
qa={'status':'PASS','issue':21,'native_existing_replaced':44,'AI_existing_replaced':29,'native_details_added':5,
    'records_before':len(before['photos']),'records_after':len(after['photos']),
    'isolated_test_records_preserved':len(protected),'unaffected_records_preserved':len(old)-len(changed),
    'resources_plans_UI_unchanged':True,'all_new_images_embedded':True,'changed_ids':changed,'added_ids':added,
    'html_sha256':hashlib.sha256(output.encode()).hexdigest(),'published_images':published}
(root/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2))
print(json.dumps({k:v for k,v in qa.items() if k!='published_images'}),flush=True)
