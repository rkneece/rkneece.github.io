"""Append one matching pantry-passage TEST view per option; preserve current site."""
from pathlib import Path
import os,json,re,hashlib,copy,collections
P=Path(__file__).resolve().parent;SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map'));M=json.loads((P/'MANIFEST.json').read_text());review=json.loads((P/'REVIEW_QA.json').read_text());assert review['status']=='PASS'
path=SITE/'index.html';text=path.read_text();assert hashlib.sha256(text.encode()).hexdigest()==M['before_html_sha256']
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);match=pat.search(text);assert match;before=json.loads(match[2]);after=copy.deepcopy(before)
oldids={f'RES{i:02d}' for i in range(9,27)};newids={r['id'] for r in M['images']};assert newids=={'RES27','RES28','RES29'};assert not newids.intersection(p['id'] for p in before['photos'])
byid={p['id']:p for p in after['photos']};new=[]
for r in M['images']:
 c=r['case'];q=r['native_qa'];asset=SITE/r['path'];assert hashlib.sha256(asset.read_bytes()).hexdigest()==r['sha256']
 p=copy.deepcopy(next(p for p in after['photos'] if p.get('islandTestOption')==c and p.get('islandTestView')=='Couch'))
 p.update(id=r['id'],imageId=r['id'],looking=f'Pantry passage · kitchen end toward hall · Option {c} · TEST',filename=asset.name,publishedAt=M['created_at'],updatedAt=M['created_at'],imageSHA256=r['sha256'],sourceSceneSHA256=q['scene_sha256'],nativeReferenceSHA256=q['views'][0]['sha256'],islandTestView='Hallway',testViewOrder=2,testOptionOrder='DEG'.index(c),islandFixtureQARevision='HALLWAY1',qaStatus='HALLWAY_NATIVE_AND_VISUAL_QA_PASS',source='Native TEST camera geometry + Image Generation photographic finish · test/island-DEG-photoreal',islandHallwayStudy='PANTRY-HALLWAY-20261024',pantryClosedDoorNearestDistanceInches=q['nearest_plan_distance_to_closed_door_front_inches'],pantryEastWestOffsetInches=q['east_west_offset_to_closed_door_front_inches'],pantryNorthSouthOffsetInches=q['north_south_offset_of_nearest_edges_inches'])
 p['notes']+=f" Matching camera from the kitchen end looking down the pantry passage toward the hall; closed pantry doors on left, island on right. Modeled nearest plan distance from countertop edge to closed pantry door front is {q['nearest_plan_distance_to_closed_door_front_inches']:.1f} inches; east–west offset {q['east_west_offset_to_closed_door_front_inches']:.1f} inches, north–south corner offset {q['north_south_offset_of_nearest_edges_inches']:.1f} inches. Excludes projecting handles and door swing. These are model measurements, not field verification or usable clearance with doors open. Photoreal finish is illustrative."
 after['resourceImages'][r['id']]=r['path']+'?v=HALLWAY1';new.append(p)
for p in after['photos']:
 if p['id'] in oldids:p['testViewOrder']=M['view_order'].index(p['islandTestView'])
index=next(i for i,p in enumerate(after['photos']) if p['id']=='RES09');after['photos'][index:index]=new
assert len(after['photos'])==len(before['photos'])+3==417
assert len({p['id'] for p in after['photos']})==417
assert [p for p in before['photos'] if p['id'] not in oldids]==[p for p in after['photos'] if p['id'] not in oldids|newids]
for a in before['photos']:
 if a['id'] in oldids:
  b=next(p for p in after['photos'] if p['id']==a['id']);aa=copy.deepcopy(a);bb=copy.deepcopy(b);aa.pop('testViewOrder');bb.pop('testViewOrder');assert aa==bb
for k in before:
 if k not in ('photos','resourceImages','counts'):assert before[k]==after[k],k
for ident,value in before['resourceImages'].items():assert after['resourceImages'][ident]==value
ordered=[p for p in after['photos'] if p['id'] in oldids|newids];assert [(p['islandTestView'],p['islandTestOption']) for p in ordered]==[(v,c) for v in M['view_order'] for c in 'DEG']
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/');out=text[:match.start(2)]+payload+text[match.end(2):];assert json.loads(pat.search(out)[2])==after;path.write_text(out)
qa=dict(status='PASS',added_ids=sorted(newids),existing_images_and_resource_paths_unchanged=True,non_test_records_unchanged=396,existing_test_change_only_view_order_metadata=True,other_ui_and_data_unchanged=True,record_count=417,test_image_count=21,ordered_test_ids=[p['id'] for p in ordered],view_order=M['view_order'],html_sha256=hashlib.sha256(out.encode()).hexdigest(),protected_refs=M['protected_refs'])
(P/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
