"""Apply only coordinator-reviewed assets to the exact reviewed viewer."""
from pathlib import Path
import copy,hashlib,json,re
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent if ROOT.parent.name=='releases' else ROOT
SITE=REPO/'sites/43cedar/interactive_map'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assemble(site=SITE,release=ROOT):
 manifest=json.loads((release/'REVIEW.json').read_text())
 path=site/'index.html';raw=path.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==manifest['base_html_sha256'],'Viewer changed: rebase and review before publishing'
 text=raw.decode();pattern=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
 before=json.loads(pattern.search(text)[2]);data=copy.deepcopy(before);byid={x['id']:x for x in data['photos']}
 changed=set()
 for row in manifest['images']:
  p=byid[row['id']];asset=release/row['release_path'];assert sha(asset)==row['sha256'];Image.open(asset).verify()
  target=site/row['asset_path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(asset.read_bytes())
  field={'blender':'blenderImages','photoreal':'photorealImages','resource':'resourceImages'}[p['type']]
  data[field][p.get('imageId',p['id'])]=row['asset_path']+'?v=COORD9'
  p.update(designVersion='Coordinated FF6 / P135 / unified beam / PL2 / CW1 / PD1',variant='Combined approved model and preserved stable camera',updatedAt=manifest['updated_at'],imageSHA256=row['sha256'],coordinatedRevision='COORD9',geometryStatus='Native combined model verified; AI imagery is an illustrative finish study' if p['type']=='photoreal' else 'Coordinated native geometry; dimensions remain provisional',qaStatus='COORDINATOR_VISUAL_REVIEW_PASS',approval='Owner authorized coordinated publication; coordinator visual QA passed')
  p['notes']=('Current coordinated proposal: 152-inch fireplace alcove and 75-inch TV, retained painted tongue-and-groove; P135 east-biased post and unified dining-to-hall line; PL2 double pantry / single linen door; CW1 counter-wall closure; PD1 primary door. Only visible changes apply to each view. Native model remains geometry authority. Existing map registration retained; dimensions and AI materials remain illustrative.')
  p['renderedAt']=row['created_date'];p['sourceSceneSHA256']=row['actual_scene_sha256'];p['validatedCombinedSceneSHA256']=manifest['combined_scene_sha256']
  if p['type']=='photoreal':p['sourcePNG_SHA256']=row['source_native_sha256'];p['source']=p['sourceRenderId']
  else:p['source']='Coordinated native Blender model / issue #9'
  changed.add(p['id'])
 data['proposedPlans']['F1']=data['resourceImages']['RES02']
 data['proposedPlanInfo']['F1'].update(source='Coordinated FF6/P135/straight-line/PL2/CW1/PD1 native overhead',notes='Current navigation reference; dimensions remain provisional.')
 data['coordinatedRevision']='COORD9';data['buildId']='COORD9_FF6_P135_PL2_CW1_PD1'
 for key in ['photoImages','plans','roomTaxonomy','demo20261023Revision','primaryDoorBedroomPairRevision']:assert data[key]==before[key],key
 assert len(data['photos'])==len(before['photos'])
 for old,new in zip(before['photos'],data['photos']):
  assert old['id']==new['id']
  for key in ['mapX','mapY','proposedMapX','proposedMapY','cameraEyeXY','cameraTargetXY','mapDirectionDegrees','viewpointId','sourceRenderId','floor','zone','type','publishedAt']:assert old.get(key)==new.get(key),(old['id'],key)
  if old['id'] not in changed:assert old==new,old['id']
 for field in ['blenderImages','photorealImages','resourceImages']:
  for ident,v in before[field].items():
   if ident not in changed:assert data[field][ident]==v,(field,ident)
 for ident in ['RES01','B100','R65']:
  assert byid[ident]==next(x for x in before['photos'] if x['id']==ident)
 result=text[:pattern.search(text).start(2)]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+text[pattern.search(text).end(2):]
 path.write_text(result)
 qa=dict(status='PASS',changed_ids=sorted(changed),record_count=len(data['photos']),output_html_sha256=sha(path),stable_ids_positions_links_and_unrelated_content_preserved=True,already_live_RES01_B100_R65_preserved=True)
 (release/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
 print(json.dumps(qa))
if __name__=='__main__':assemble()
