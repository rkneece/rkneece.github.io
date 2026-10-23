"""Apply reviewed P135 images to a current planner, preserving stable identities."""
from pathlib import Path
import re,json,base64,io,hashlib,argparse,copy,collections
from PIL import Image
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output');parser.add_argument('--external-assets',action='store_true');args=parser.parse_args()
source=Path(args.input).read_text();match=re.search(r'(<script[^>]*id="appdata"[^>]*>)(.*?)(</script>)',source,re.S)
data=json.loads(match.group(2));original=copy.deepcopy(data)
native=json.loads((root/'REQUIRED_POST_CAMERA_AUDIT.json').read_text())
photo=json.loads((root/'REQUIRED_POST_PHOTO_QA.json').read_text())
assert photo['status']=='ACCEPTED_VISUAL_REVIEW'
byid={p['id']:p for p in data['photos']}
source_commit=json.loads((root/'REQUIRED_POST_REVIEWED.json').read_text())['source_code_commit']
source_url='https://github.com/rkneece/43-cedar-blender/commit/'+source_commit
data['sourceRun']=source_url
if source_url not in data['sourceRuns']:data['sourceRuns'].append(source_url)
def encoded(path):
 if not path.exists():path=path.with_suffix('.jpg')
 if path.suffix.lower()=='.jpg':return 'data:image/jpeg;base64,'+base64.b64encode(path.read_bytes()).decode()
 im=Image.open(path).convert('RGB');b=io.BytesIO();im.save(b,format='JPEG',quality=94,subsampling=0)
 return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
changed_native=[];changed_photo=[]
note=' Required post P135: structural center 135 inches from west wall; provisional chase builds mostly east. Island unchanged; seating/bench coordination deferred.'
for row in native['cameras']:
 p=byid[row['id']]
 if row['render_required']:
  data['blenderImages'][row['id']]=encoded(root/'post_renders'/(row['id']+'.png'))
  p.update(designVersion='P135 required post / east-biased chase',geometryStatus='Native post at 135-inch structural center; all unrelated geometry and cameras retained',renderedAt='2026-10-23')
  p['notes']=p.get('notes','')+note;p['source']=source_url;changed_native.append(p['id'])
 p['postCoordinationRevision']='P135'
 p['postInView']=row['render_required']
for row in photo['photos']:
 p=byid[row['id']]
 assert p.get('sourceRenderId')==row['sourceRenderId']
 if row['changed']:
  assert row['accepted']
  data['photorealImages'][p['id']]=encoded(root/'post_photoreal'/(p['id']+'.png'))
  p.update(designVersion='P135 AI photographic post coordination',renderedAt='2026-10-23',qaStatus='ACCEPTED_VISUAL_POST_COORDINATION')
  p['notes']=p.get('notes','')+note;changed_photo.append(p['id'])
 p['postCoordinationRevision']='P135'
data['resourceImages']['RES03']=encoded(root/'post_diagrams'/'43_Cedar_P135_CubiCasa_Coordination.png')
byid['RES03'].update(looking='Kitchen / dining · required post at 135 inches',designVersion='P135 post coordination',notes='Required structural center 135 inches from west. East-biased provisional chase. Island retained. Roof notch extension recorded as intent; exact bay width and beam section pending.')
byid['RES03']['source']='Owner-directed P135 coordination overlay on original CubiCasa geometry'
data['resourceImages']['RES02']=encoded(root/'post_renders'/'B34.png')
byid['RES02'].update(designVersion='P135 required-post overhead',source='Reviewed P135 furnished native model',notes=byid['RES02'].get('notes','')+note)
data['proposedPlans']['F1']=data['resourceImages']['RES02']
data['proposedPlanInfo']['F1']['notes']+=' Required post / east-biased chase P135. Island unchanged.'
if 'RES06' not in byid:
 p=dict(id='RES06',imageId='RES06',type='resource',stage='Proposed · Resources',floor='F1',zone='Kitchen / dining structure',kind='Coordination diagram',looking='Post / east-biased chase dimension detail',filename='43_Cedar_P135_Chase_Detail.png',source='Owner direction / P135 native model',referenceStatus='135-inch owner-directed structural center; chase dimensions provisional',designVersion='P135 required post',notes=note.strip())
 data['photos'].append(p)
data['resourceImages']['RES06']=encoded(root/'post_diagrams'/'43_Cedar_P135_Chase_Detail.png')
if 'RES06' not in data['proposedResources']['records']:data['proposedResources']['records'].append('RES06')
data['proposalNotes'].append(dict(area='Required post / P135',detail=note.strip()))
data['floorProposalNotes'].setdefault('F2',[]).append(dict(area='Dining roof / upstairs primary bath',detail='Fill the dining roof notch one framing bay to align a single straight beam. The upstairs primary bathroom gains space. Exact bay width and final roof/beam geometry pending; current upstairs navigation remains a baseline study.'))
data['requiredPostRevision']=dict(release='P135_East_Biased_Chase',structural_center_from_west_inches=135,chase_dimensions_provisional=[10,8],chase_west_finish_from_west_inches=131.75,chase_east_finish_from_west_inches=141.75,updated_native=changed_native,updated_photoreal=changed_photo,island_changed=False)
data['buildId']='P135_East_Biased_Chase'
data['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in data['photos']))
# Keep source site photos, established IDs, camera registration and unrelated imagery.
assert data['photoImages']==original['photoImages']
assert data['plans']==original['plans']
assert [p for p in data['photos'] if p['type']=='site']==[p for p in original['photos'] if p['type']=='site']
for before in original['photos']:
 after=next(p for p in data['photos'] if p['id']==before['id'])
 for key in ['mapX','mapY','proposedMapX','proposedMapY','cameraEyeXY','cameraTargetXY','viewpointId','sourceRenderId']:
  assert after.get(key)==before.get(key),(before['id'],key)
asset_root=Path(args.output).parent/'assets'
for key,folder,ids in [('blenderImages','renders',changed_native),('photorealImages','photoreal',changed_photo),('resourceImages','resources',['RES02','RES03','RES06'])]:
 (asset_root/folder).mkdir(parents=True,exist_ok=True)
 for id in ids:
  (asset_root/folder/(id+'.jpg')).write_bytes(base64.b64decode(data[key][id].split(',',1)[1]))
  if args.external_assets:data[key][id]='assets/'+folder+'/'+id+'.jpg?v=P135'
if args.external_assets:data['proposedPlans']['F1']=data['resourceImages']['RES02']
payload=json.dumps(data,separators=(',',':')).replace('</','<\\/')
output=source[:match.start(2)]+payload+source[match.end(2):]
Path(args.output).write_text(output)
report=dict(release='P135_East_Biased_Chase',updated_native=changed_native,updated_photoreal=changed_photo,
 source_html_sha256=hashlib.sha256(source.encode()).hexdigest(),output_html_sha256=hashlib.sha256(output.encode()).hexdigest(),
 original_site_photos_and_maps_preserved=True,all_existing_ids_and_camera_registration_preserved=True,
 island_geometry_changed=False,resource_count=len(data['resourceImages']))
(root/'REQUIRED_POST_PUBLISH_QA.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(native=len(changed_native),photoreal=len(changed_photo),bytes=len(output.encode()),sha256=hashlib.sha256(output.encode()).hexdigest())))

