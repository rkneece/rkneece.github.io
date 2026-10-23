import base64,copy,hashlib,io,json,os,re,urllib.request
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path('releases/photoreal40');BASE='https://api.github.com/repos/rkneece/rkneece.github.io';BRANCH='feature/photoreal40-live'
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
def api(p,d=None,method=None):
 with urllib.request.urlopen(urllib.request.Request(BASE+p,headers=headers,data=None if d is None else json.dumps(d).encode(),method=method or ('POST' if d else 'GET'))) as r:return json.load(r)
def sha(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
head=api('/git/ref/heads/'+BRANCH)['object']['sha'];assert head==os.environ['GITHUB_SHA'];base=json.loads((ROOT/'base.json').read_text());assert api('/git/ref/heads/main')['object']['sha']==base['main']
source=urllib.request.urlopen('https://raw.githubusercontent.com/rkneece/rkneece.github.io/'+base['main']+'/sites/43cedar/interactive_map/index.html').read().decode();assert sha(source.encode())==base['blob']
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);before=json.loads(pat.search(source)[2]);d=copy.deepcopy(before);report=json.loads((ROOT/'REVIEW.json').read_text());assert len(report['records'])==40
assert max(int(p['id'][1:]) for p in d['photos'] if re.fullmatch('R[0-9]+',p['id']))==27
seq=max(p.get('sequence',0) for p in d['photos']);ids=[];native_ids=[]
for r in report['records']:
 bid,rid=r['render_id'],r['photoreal_id'];src=next(p for p in d['photos'] if p['id']==bid);assert src['sourcePNG_SHA256']==r['source_sha256'];payload=Path('sites/43cedar/interactive_map/assets/photoreal/'+rid+'.jpg').read_bytes();assert sha(payload)==r['display_blob_sha'];Image.open(io.BytesIO(payload)).verify();assert rid not in {p['id'] for p in d['photos']}
 d['photorealImages'][rid]='data:image/jpeg;base64,'+base64.b64encode(payload).decode();seq+=1;p=copy.deepcopy(src)
 p.update(id=rid,type='photoreal',stage='Proposed · Photoreal',kind='AI photographic finish study',filename=r['file'],sequence=seq,imageId=rid,source=bid,sourceRenderId=bid,sourceType='AI image edit from Blender reference',relatedPhotos=[bid],variant='Prompt-based photographic material and light study',approval='Visual comparison reviewed; native render remains dimensional authority',geometryStatus='Visual architectural review; not a dimensional or pixel-exact guarantee',qaStatus='ACCEPTED_VISUAL_ARCHITECTURAL_REVIEW',notes='Photographic finish edited from the paired native view and reviewed for framing, room outlines, openings and fixture/furniture placement. Small surface and soft-furnishing variations remain; exterior vegetation is illustrative.',imageSHA256=r['display_sha256'])
 src['relatedPhotos']=list(dict.fromkeys(src.get('relatedPhotos',[])+[rid]));d['photos'].append(p);ids.append(rid);native_ids.append(bid)
assert len(d['photos'])==len(before['photos'])+40
for i,old in enumerate(before['photos']):
 actual=copy.deepcopy(d['photos'][i]);check=copy.deepcopy(old)
 if old['id'] in native_ids:actual.pop('relatedPhotos',None);check.pop('relatedPhotos',None)
 assert actual==check,old['id']
for k in before:
 if k not in {'photos','photorealImages','counts','buildId','nativeCoverage40'}:assert d[k]==before[k],k
for k,v in before['photorealImages'].items():assert d['photorealImages'][k]==v
assert d['blenderImages']==before['blenderImages'];d['counts']=dict(Counter(p['floor']+'|'+p['stage'] for p in d['photos']));d['buildId']='Rev20_FF5_40_Render_Photoreal_Pairs';d['nativeCoverage40']['photoreal']='40 photographic finish studies reviewed and published';d['photorealCoverage40']={'new_ids':ids,'source_render_ids':native_ids,'review_scope':report['review_scope'],'minor_finish_variations':report['minor_finish_variations']}
out=pat.sub(lambda m:m[1]+json.dumps(d,separators=(',',':')).replace('</','<\\/')+m[3],source);assert pat.sub('',out)==pat.sub('',source)
qa={'new_photoreal':40,'existing_records_preserved_except_render_pair_links':True,'all_existing_images_plans_resources_exterior_and_ui_unchanged':True,'source_render_ids':native_ids,'new_ids':ids,'base_blob':base['blob'],'output_blob':sha(out.encode()),'bytes':len(out.encode()),'counts':d['counts']}
blob=api('/git/blobs',{'content':base64.b64encode(out.encode()).decode(),'encoding':'base64'});assert blob['sha']==qa['output_blob'];tree=api('/git/trees',{'base_tree':api('/git/commits/'+head)['tree']['sha'],'tree':[{'path':'sites/43cedar/interactive_map/index.html','mode':'100644','type':'blob','sha':blob['sha']},{'path':'releases/photoreal40/PUBLISH_QA.json','mode':'100644','type':'blob','content':json.dumps(qa,indent=2)}]});commit=api('/git/commits',{'message':'Assemble 40 visually reviewed photographic counterparts for native views','tree':tree['sha'],'parents':[head]});assert api('/git/ref/heads/'+BRANCH)['object']['sha']==head;api('/git/refs/heads/'+BRANCH,{'sha':commit['sha'],'force':False},'PATCH');print(json.dumps(qa));print('ASSEMBLED='+commit['sha'])
