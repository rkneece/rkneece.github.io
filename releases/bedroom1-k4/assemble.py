"""Guarded K4 viewer assembly; preserve prior IDs, positions and unrelated bytes."""
import copy,collections,hashlib,json,math,re,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
def assemble(source,target,assets=None):
 m=json.loads((ROOT/'REVIEW.json').read_text());raw=Path(source).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==m['base_html_sha256'],'Viewer changed; rebase before assembly'
 text=raw.decode();rx=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);hit=rx.search(text);assert hit
 before=json.loads(hit[2]);d=copy.deepcopy(before);byid={p['id']:p for p in d['photos']}
 assert 'B106' not in byid and 'R71' not in byid,'New ID collision'
 new=copy.deepcopy(byid['B49']);new.update(id='B106',imageId='B106',publishedAt='2026-10-24',filename='43_Cedar_K4_Level_TV_Wall.png',looking='Bedroom 1 Level TV Wall Console And Mirror',sequence=max(p.get('sequence',0) for p in d['photos'])+1,viewpointId='CEDAR-K4-LEVEL-TV-WALL',cameraEyeXY=[28.1,3.8],cameraTargetXY=[33.6,-3.4],mapDirectionDegrees=round(math.degrees(math.atan2(5.5,-7.2))%360,2),proposedMapX=70.404,proposedMapY=19.091,mapX=71.461,mapY=12.902,relatedPhotos=['R71'],sourceType='Native Blender render',viewMode='Perspective')
 new['notes']='Level camera with vertical lens shift; existing room geometry retained. Map registration approximate.'
 photo=copy.deepcopy(new);photo.update(id='R71',imageId='R71',filename='43_Cedar_K4_Level_TV_Wall_Photo.jpg',type='photoreal',stage='Proposed · Photoreal',kind='Photographic finish study',sourceType='AI photographic finish',sourceRenderId='B106',source='B106',sequence=new['sequence']+1,relatedPhotos=['B106'])
 for p in [new,photo]:d['photos'].append(p);byid[p['id']]=p
 changed=set();reviewed=[]
 for row in m['images']:
  p=byid[row['id']];field={'blender':'blenderImages','photoreal':'photorealImages','resource':'resourceImages'}[p['type']]
  asset=(Path(assets)/Path(row['asset_path']).name) if assets else Path(source).parent/row['asset_path']
  b=asset.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'],row['id'];Image.open(asset).verify()
  d[field][p.get('imageId',p['id'])]=row['asset_path']+'?v=K4'
  p.update(updatedAt='2026-10-24',renderedAt='2026-10-24',designVersion='K4 Bedroom 1 king / oak / navy console / art / mirror / papasan',variant='Single combined model; preserved registered camera' if p['id'] not in ['B106','R71'] else 'New level review camera; zero pitch and roll',imageSHA256=row['sha256'],sourceSceneSHA256=m['scene_sha256'],validatedCombinedSceneSHA256=m['scene_sha256'],bedroom1Revision='K4',qaStatus='K4_VISUAL_REVIEW_PASS',approval='Owner authorized coordinated publication after QA',geometryStatus='AI finish illustration; native source governs exact geometry and dimensions' if p['type']=='photoreal' else 'Native combined geometry verified; field dimensions remain provisional')
  p['notes']='K4 Bedroom 1: natural oak king frame/headboard flush west wall and matching18×14in nightstands; ivory/blue/sage bedding and paired coastal art;55in TV,60×18×30in Hale Navy six-drawer console, corridor mirror,39×37×33in papasan beside slider. Chair leaves34.35in slider approach but only3.38in to bed, so that side is entered from the foot. Footstool omitted. Only changes visible from this camera apply. Native model remains dimensional authority; AI surface/perspective details illustrative.'
  if p['type']=='photoreal':p['sourcePNG_SHA256']=row['source_native_png_sha256'];p['source']=p['sourceRenderId']
  else:p['source']='Canonical K4 native Blender model / issue13';p['sourcePNG_SHA256']=row['native_png_sha256']
  changed.add(p['id']);reviewed.append(p['id'])
 d['proposedPlans']['F1']=d['resourceImages']['RES02'];d['proposedPlanInfo']['F1'].update(source='Coordinated base plus K4 Bedroom 1 furnishings native overhead',notes='Current navigation reference including K4 king/console/papasan; field dimensions remain provisional.')
 d['bedroom1Revision']='K4';d['buildId']='K4_Bedroom1_Coordinated';d['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in d['photos']))
 assert len(d['photos'])==len(before['photos'])+2
 for old in before['photos']:
  now=byid[old['id']]
  for key in ['id','floor','stage','zone','mapX','mapY','proposedMapX','proposedMapY','mapDirectionDegrees','cameraEyeXY','cameraTargetXY','viewpointId','sourceRenderId','publishedAt']:assert old.get(key)==now.get(key),(old['id'],key)
  if old['id'] not in changed:assert old==now,old['id']
 for field in ['photoImages','plans','roomTaxonomy']:assert d[field]==before[field],field
 for field in ['blenderImages','photorealImages','resourceImages']:
  for key,value in before[field].items():
   if key not in changed:assert d[field][key]==value,(field,key)
 for p in d['photos']:
  if p['type']=='photoreal':assert p['sourceRenderId'] in byid,p['id']
 result=text[:hit.start(2)]+json.dumps(d,ensure_ascii=False,separators=(',',':'))+text[hit.end(2):];Path(target).write_text(result)
 qa={'status':'PASS','record_count':len(d['photos']),'updated_records':len(changed)-2,'new_ids':['B106','R71'],'reviewed_ids':reviewed,'all_original_ids_positions_links_taxonomy_site_photos_unrelated_records_preserved':True,'output_html_sha256':hashlib.sha256(Path(target).read_bytes()).hexdigest()}
 (ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa))
if __name__=='__main__':
 site=ROOT.parents[1]/'sites/43cedar/interactive_map/index.html'
 assemble(sys.argv[1] if len(sys.argv)>1 else site,sys.argv[2] if len(sys.argv)>2 else site,sys.argv[3] if len(sys.argv)>3 else None)
