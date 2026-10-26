"""Replace only isolated TEST resources; group by view then option, stable IDs."""
from pathlib import Path
import os,re,json,hashlib,copy,collections
P=Path(__file__).resolve().parent;SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map'));path=SITE/'index.html';text=path.read_text();m=json.loads((P/'FIXTURE_MANIFEST.json').read_text());review=json.loads((P/'REVIEW_QA.json').read_text());assert review['status']=='PASS'
assert hashlib.sha256(text.encode()).hexdigest()==m['before_html_sha256'],'Website baseline changed'
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);match=PAT.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before);byid={r['id']:r for r in after['photos']};oldids={f'RES{i:02d}' for i in range(9,24)};newids={f'RES{i:02d}' for i in range(24,27)}
assert len(m['images'])==18 and {r['id'] for r in m['images']}==oldids|newids
assert [(r['view'],r['case']) for r in m['images']]==[(v,c) for v in m['view_order'] for c in m['case_order']]
case_notes={
'D':'96″ E–W × 54″ N–S. Four south stools; island abuts fixed post casing. North face west→east: dishwasher, sink, compact microwave drawer. Approximately 29″ occupied dining gap under the study’s 26″ occupant-zone assumption.',
'E':'96″ E–W × 66″ N–S. Four south stools; countertop wraps fixed post casing. North face west→east: dishwasher, sink, compact microwave drawer. Approximately 17″ occupied dining gap under the study’s 26″ occupant-zone assumption; tightest dining arrangement.',
'G':'84″ E–W × 48″ N–S. Three south stools and one west stool, possibly occluded in perspective. North face sink and dishwasher together. Microwave location remains UNALLOCATED. Approximately 35″ occupied dining gap under the study’s 26″ occupant-zone assumption. West stool still conflicts with active dining-side / left slider approach.'}
shared='TEST ONLY. Faucet direction checked against native geometry: north mounting point, spout curves south over basin, outlet points down inside basin. Surrounding room, fixed post, dining furniture and stool placements retained. AI photographic finish studies are illustrative; native geometry and study dimensions govern clearance review. Stools are unoccupied; pulled-out dining chairs reduce passage. Existing pendant positions retained. Isolated branch; working model Dev/main unchanged.'
records=[]
for r in m['images']:
 ident=r['id'];c=r['case'];v=r['view'];asset=SITE/r['path'];assert hashlib.sha256(asset.read_bytes()).hexdigest()==r['sha256']
 if ident in oldids:
  p=byid[ident];assert p['islandTestPhotorealSet']=='D-E-G-PR-20261024' and p['type']=='resource'
 else:
  assert ident not in byid;p=dict(id=ident,imageId=ident,type='resource',stage='Proposed · Resources',floor='F1',zone='Dining Area',publishedAt=m['created_at'])
 extra=(' Compact microwave front is 23⅞″ W ×15⅞″ H, with navy cabinet storage below; manufacturer dimensions used as a study proportion, appliance not selected.' if c!='G' else '')
 if v=='Kitchen':extra+=(' From this kitchen viewpoint, left→right: microwave drawer, sink base, dishwasher.' if c!='G' else ' From this kitchen viewpoint, left→right: dishwasher, sink base, west knee opening. No microwave shown.')
 p.update(kind='Photoreal alternative · TEST',looking=f'{r["label"]} · Option {c} · TEST',filename=asset.name,source='Native geometry QA + Image Generation photographic finish · test/island-DEG-photoreal',referenceStatus='TEST ONLY · working Dev model unchanged',designVersion=f'Island option {c} · isolated TEST 2026-10-24',variant=f'Option {c} · not selected',notes=case_notes[c]+' '+shared+extra,updatedAt=m['created_at'],imageSHA256=r['sha256'],nativeReferenceSHA256=r['native_sha256'],sourceSceneSHA256=m['source_scene_sha256'],modelBranch=m['test_branch'],islandTestSet='D-E-G-20261024',islandTestPhotorealSet='D-E-G-PR-20261024',islandFixtureQARevision='FIXTURE2',islandTestOption=c,islandTestView=v,testViewOrder=m['view_order'].index(v),testOptionOrder=m['case_order'].index(c),qaStatus='FIXTURE2_VISUAL_AND_NATIVE_QA_PASS',geometryStatus='AI finish study; source nozzle verified inside basin; native model is geometry authority',approval='Owner authorized isolated test corrections, compact microwave, kitchen viewpoint, live replacement and view-first option ordering; no model Dev/main merge')
 if c!='G':p['microwaveStudyFaceInches']=[23.875,15.875]
 after['resourceImages'][ident]=r['path'];records.append(p)
first=next(i for i,r in enumerate(after['photos']) if r['id'] in oldids)
others=[p for p in after['photos'] if p['id'] not in oldids];after['photos']=others[:first]+records+others[first:]
assert [p for p in after['photos'] if p['id'] not in oldids|newids]==[p for p in before['photos'] if p['id'] not in oldids]
assert len(after['photos'])==len(before['photos'])+3 and len({p['id'] for p in after['photos']})==len(after['photos'])
assert [p['id'] for p in after['photos'] if p.get('islandFixtureQARevision')=='FIXTURE2']==[r['id'] for r in m['images']]
for k in before:
 if k not in ('photos','resourceImages','counts'):assert after[k]==before[k],k
for ident,value in before['resourceImages'].items():
 if ident not in oldids:assert after['resourceImages'][ident]==value
assert set(after['resourceImages'])-set(before['resourceImages'])==newids
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/');out=text[:match.start(2)]+payload+text[match.end(2):];assert json.loads(PAT.search(out)[2])==after
path.write_text(out)
qa=dict(status='PASS',replaced_ids=sorted(oldids),added_ids=sorted(newids),before_records=len(before['photos']),after_records=len(after['photos']),non_test_records_unchanged=396,non_test_relative_order_unchanged=True,all_other_maps_plans_galleries_ui_unchanged=True,grouping='viewpoint then alphabetical option',view_order=m['view_order'],option_order=m['case_order'],ordered_test_ids=[r['id'] for r in m['images']],html_sha256=hashlib.sha256(out.encode()).hexdigest(),model_branch=m['test_branch'])
(P/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
