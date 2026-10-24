"""Append isolated E/G native tests to Resources; preserve all existing data."""
from pathlib import Path
import re,json,copy,hashlib,collections,datetime
ROOT=Path(__file__).resolve().parent
site=Path('sites/43cedar/interactive_map');path=site/'index.html'
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
text=path.read_text();match=PAT.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
manifest=json.loads((ROOT/'TEST_RENDER_MANIFEST.json').read_text())
assert len(manifest['images'])==10
assert not any(p.get('islandTestSet')=='E-G-20261024' for p in before['photos']),'Test set already present'
nums=[int(p['id'][3:]) for p in before['photos'] if re.fullmatch('RES[0-9]+',p['id'])];start=max(nums,default=0)+1
added=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
for i,row in enumerate(manifest['images']):
 ident=f'RES{start+i:02d}';asset=site/row['path'];digest=hashlib.sha256(asset.read_bytes()).hexdigest();assert digest==row['sha256']
 case=row['case'];label=row['label'];notes={'D':'96″ E–W × 54″ N–S, four south stools, island abuts the west face of the post casing. North sink/DW/MW. West datum clearance approximately 35.8″; occupied dining gap approximately 29″ under study assumptions.','E':'96″ E–W × 66″ N–S, four south stools, post integrated in east edge. North sink/DW/MW. Pantry corner and occupied dining clearances remain tight.','G':'84″ E–W × 48″ N–S, three south stools plus one west stool. North sink/DW. Microwave location unallocated. Fourth west stool crosses the active dining-side/left porch-slider approach; shown for owner-requested visual testing.'}[case]
 record=dict(id=ident,imageId=ident,type='resource',stage='Proposed · Resources',floor='F1',zone='Dining Area',kind='Native alternative test render',looking=f'Island option {case} · TEST · {label}',filename=asset.name,source='Isolated native Blender comparison · test/island-E-G',referenceStatus='TEST ONLY · working Dev model unchanged',designVersion=f'Island option {case} · isolated TEST 2026-10-24',variant=f'Option {case} · not selected',notes=notes+' Same test camera positions used across cases. Existing room geometry and furniture retained; only island and stools changed in the test copy. Stools are shown unoccupied; people reduce passage space. Existing pendants remain in their baseline positions. Cabinet proxies and sink/DW same-face arrangement are illustrative; source basin geometry retained. No AI image generation.',publishedAt=now,updatedAt=now,imageSHA256=digest,islandTestSet='D-E-G-20261024',modelBranch='test/island-E-G',sourceSceneSHA256=manifest['source_scene_sha256'],qaStatus='NATIVE_TEST_VISUAL_REVIEW_PASS',approval='Owner requested live publication of isolated D/E/G comparison renders; no design selection or model Dev merge')
 after['photos'].append(record);after['resourceImages'][ident]=row['path'];added.append(ident)
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
restored=copy.deepcopy(after);restored['photos']=[p for p in restored['photos'] if p['id'] not in added]
for ident in added:del restored['resourceImages'][ident]
restored['counts']=before['counts'];assert restored==before,'Existing record, image, plan or metadata changed'
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
output=text[:match.start(2)]+payload+text[match.end(2):];assert json.loads(PAT.search(output)[2])==after
path.write_text(output)
qa=dict(status='PASS',added_resource_ids=added,before_records=len(before['photos']),after_records=len(after['photos']),all_original_records_images_plans_and_ui_unchanged=True,html_sha256=hashlib.sha256(output.encode()).hexdigest(),test_model_branch='test/island-E-G',images=manifest['images'])
(ROOT/'TEST_RENDER_PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
