import base64,copy,hashlib,io,json,math,os,re,urllib.request,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path('releases/render40');BASE='https://api.github.com/repos/rkneece/rkneece.github.io'
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def api(p,d=None,method=None):
 with urllib.request.urlopen(urllib.request.Request(BASE+p,headers=headers,data=None if d is None else json.dumps(d).encode(),method=method or ('POST' if d else 'GET'))) as r:return json.load(r)
def sha(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
manifest=json.loads((ROOT/'review.json').read_text());views=manifest['first_20']['views']+manifest['followup_20']['views'];assert len(views)==40
head=api('/git/ref/heads/feature/render40-live')['object']['sha'];assert head==os.environ['GITHUB_SHA']
main=api('/git/ref/heads/main')['object']['sha'];assert main==json.loads((ROOT/'base.json').read_text())['main']
source=urllib.request.urlopen('https://raw.githubusercontent.com/rkneece/rkneece.github.io/'+main+'/sites/43cedar/interactive_map/index.html').read().decode()
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);before=json.loads(pat.search(source)[2]);data=copy.deepcopy(before)
assert sha(source.encode())==json.loads((ROOT/'base.json').read_text())['blob']
want={v['sha256']:v for v in views};images={}
for url in json.loads((ROOT/'downloads.json').read_text()):
 with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url,timeout=90).read())) as z:
  for n in z.namelist():
   if n.endswith('.png') and '43_Cedar_ROOM_' in n:
    b=z.read(n);h=hashlib.sha256(b).hexdigest()
    if h in want:images[h]=b
assert set(images)==set(want),'Missing reviewed image payloads'
reg=json.loads((ROOT/'registration.json').read_text());ids=[];seq=max(p.get('sequence',0) for p in data['photos'])
assert max(int(p['id'][1:]) for p in data['photos'] if re.fullmatch('B[0-9]+',p['id']))==62
for i,v in enumerate(views):
 ident='B'+str(63+i);eye,target=v['eye'],v['target'];coords=[*eye[:2],1]
 def project(key):return [round(sum(a*b for a,b in zip(coords,col)),3) for col in zip(*reg[key])]
 mx,my=project('existing');px,py=project('proposed');im=Image.open(io.BytesIO(images[v['sha256']]));assert im.size==(900,650);buf=io.BytesIO();im.convert('RGB').save(buf,format='JPEG',quality=92,subsampling=0,optimize=True)
 data['blenderImages'][ident]='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode();seq+=1
 run=v.get('run_id',manifest['first_20']['run_id']);photo=dict(id=ident,type='blender',floor='F1',stage='Proposed · Render',zone=v['zone'],kind='Blender room view',filename=v['file'].replace('.png','.jpg'),sequence=seq,standing='Renderer camera; map registration approximate',facing='',looking=v['file'].replace('43_Cedar_ROOM_','').removesuffix('.png')[3:].replace('_',' '),confirmed=False,mapX=mx,mapY=my,proposedMapX=px,proposedMapY=py,proposedMapLocationType='Renderer camera position · approximate map alignment',viewpointId='CEDAR-COVERAGE-'+v['file'].removesuffix('.png'),renderedAt='2026-10-22',milestone='Additional first-floor camera coverage',sourceType='Blender render',designVersion='Reviewed FF5 geometry · 40 additional angles',variant='Geometry-controlled camera view',approval='Native view visually reviewed; finishes remain provisional',relatedPhotos=[],geometryStatus='Native Blender render',source='https://github.com/rkneece/43-cedar-blender/actions/runs/'+str(run),imageId=ident,cameraEyeXY=eye[:2],cameraTargetXY=target[:2],directionSource='Renderer eye and target; map alignment approximate',viewMode='Perspective',mapDirectionDegrees=round(math.degrees(math.atan2(target[0]-eye[0],target[1]-eye[1]))%360,2),notes='Additional reviewed native camera view. Geometry retained. Photoreal counterpart pending.',qaStatus='ACCEPTED_VISUAL_ARCHITECTURAL_REVIEW',sourcePNG_SHA256=v['sha256'])
 data['photos'].append(photo);ids.append(ident)
from collections import Counter
data['counts']=dict(Counter(p['floor']+'|'+p['stage'] for p in data['photos']));data['buildId']='Rev20_FF5_40_Additional_Native_Views';data['nativeCoverage40']={'new_ids':ids,'photoreal':'Pending','mesh_signature':manifest['mesh_signature']}
assert data['photos'][:-40]==before['photos']
for k in before:
 if k not in {'photos','blenderImages','counts','buildId'}:assert data[k]==before[k],k
for k,v in before['blenderImages'].items():assert data['blenderImages'][k]==v
out=pat.sub(lambda m:m[1]+json.dumps(data,separators=(',',':')).replace('</','<\\/')+m[3],source);assert pat.sub('',out)==pat.sub('',source)
qa={'new_renders':40,'new_photoreal':0,'new_ids':ids,'existing_content_preserved':True,'base_blob':sha(source.encode()),'output_blob':sha(out.encode()),'bytes':len(out.encode()),'counts':data['counts']}
blob=api('/git/blobs',{'content':base64.b64encode(out.encode()).decode(),'encoding':'base64'});assert blob['sha']==qa['output_blob']
tree=api('/git/trees',{'base_tree':api('/git/commits/'+head)['tree']['sha'],'tree':[{'path':'sites/43cedar/interactive_map/index.html','mode':'100644','type':'blob','sha':blob['sha']},{'path':'releases/render40/PUBLISH_QA.json','mode':'100644','type':'blob','content':json.dumps(qa,indent=2)},{'path':'releases/render40/downloads.json','mode':'100644','type':'blob','sha':None}]})
commit=api('/git/commits',{'message':'Assemble 40 reviewed native views; preserve all existing map content','tree':tree['sha'],'parents':[head]});assert api('/git/ref/heads/feature/render40-live')['object']['sha']==head
api('/git/refs/heads/feature/render40-live',{'sha':commit['sha'],'force':False},'PATCH');print(json.dumps(qa));print('ASSEMBLED='+commit['sha'])
