"""Replace only the ten island TEST resources and append five missing TEST angles."""
from pathlib import Path
import os,re,json,copy,hashlib,collections
ROOT=Path(__file__).resolve().parent
SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map'))
path=SITE/'index.html';text=path.read_text();manifest=json.loads((ROOT/'PHOTOREAL_MANIFEST.json').read_text())
assert hashlib.sha256(text.encode()).hexdigest()==manifest['before_html_sha256'],'Publication baseline changed'
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);m=PAT.search(text);assert m
before=json.loads(m[2]);after=copy.deepcopy(before);byid={p['id']:p for p in after['photos']}
expected={f'RES{i:02d}' for i in range(9,19)};replaced=set();added=set()
assert len(manifest['images'])==15
assert collections.Counter(r['case'] for r in manifest['images'])=={'D':5,'E':5,'G':5}
for c in 'DEG':assert {r['view'] for r in manifest['images'] if r['case']==c}=={'Couch','Dining','Porch','Post','Plan'}
for row in manifest['images']:
 ident=row['id'];c=row['case'];asset=SITE/row['path'];assert hashlib.sha256(asset.read_bytes()).hexdigest()==row['sha256']
 if ident in expected:
  p=byid[ident];assert p['type']=='resource' and p['islandTestSet']=='D-E-G-20261024';replaced.add(ident)
 else:
  assert ident not in byid;p=dict(id=ident,imageId=ident,type='resource',stage='Proposed · Resources',floor='F1',zone='Dining Area');after['photos'].append(p);added.add(ident)
 p.update(kind='Photoreal alternative · TEST',looking=f'Island option {c} · TEST · {row["label"]}',filename=asset.name,source='Photoreal image edit from isolated native Blender test; test/island-DEG-photoreal',referenceStatus='TEST ONLY · working Dev model unchanged',designVersion=f'Island option {c} · isolated TEST 2026-10-24',variant=f'Option {c} · not selected',notes=manifest['case_notes'][c]+' '+manifest['shared_notes']+' '+('Standing close to the living-room couch; eye height 67.2 inches. Identical camera used across D/E/G.' if row['view']=='Couch' else 'Same comparison camera used across D/E/G for this angle.'),publishedAt=manifest['created_at'],updatedAt=manifest['created_at'],imageSHA256=row['sha256'],islandTestSet='D-E-G-20261024',islandTestPhotorealSet='D-E-G-PR-20261024',modelBranch='test/island-DEG-photoreal',sourceSceneSHA256=manifest['source_scene_sha256'],nativeReferenceSHA256=row['native_png_sha256'],geometryStatus='AI photographic finish study; native model is geometry authority; not a measured clearance image',qaStatus='TEST_PHOTOREAL_VISUAL_REVIEW_PASS',approval='Owner requested live replacement of isolated test renders with photoreal, all comparison angles and couch viewpoint; no design selection or model Dev merge')
 after['resourceImages'][ident]=row['path']
assert replaced==expected and len(added)==5
assert len({p['id'] for p in after['photos']})==len(after['photos'])
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
restored=copy.deepcopy(after);old={p['id']:p for p in before['photos']}
restored['photos']=[copy.deepcopy(old[p['id']]) if p['id'] in replaced else p for p in restored['photos'] if p['id'] not in added]
for ident in replaced:restored['resourceImages'][ident]=before['resourceImages'][ident]
for ident in added:del restored['resourceImages'][ident]
restored['counts']=before['counts'];assert restored==before,'Non-test content changed'
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
output=text[:m.start(2)]+payload+text[m.end(2):];assert json.loads(PAT.search(output)[2])==after
assert text[:m.start(2)]==output[:m.start(2)] and text[m.end(2):]==output[output.index('</script>',m.start(2)):]
path.write_text(output)
qa=dict(status='PASS',replaced_ids=sorted(replaced),added_ids=sorted(added),test_options=dict(collections.Counter(r['case'] for r in manifest['images'])),before_records=len(before['photos']),after_records=len(after['photos']),non_test_records_plans_galleries_and_ui_unchanged=True,working_model_not_modified=True,html_sha256=hashlib.sha256(output.encode()).hexdigest(),photoreal_limit='Visually checked illustrative finish images; native model remains geometry authority')
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
