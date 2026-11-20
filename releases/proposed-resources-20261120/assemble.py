"""Append issue 38's four supplied resources without altering existing viewer records."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess, sys
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[2]
RELEASE=Path(__file__).resolve().parent
VIEWER=ROOT/'sites/43cedar/interactive_map/index.html'
BASELINE='2dc91fde8d603a5f6c757717a2f23cb4aa9a7ad8'
PATTERN=r'(<script id="appdata" type="application/json">)(.*?)(</script>)'
def sha(b): return hashlib.sha256(b).hexdigest()
def parse(s): return json.loads(re.search(PATTERN,s,re.S).group(2))

def main():
 supplied=Path(sys.argv[1]).resolve()
 baseline=subprocess.check_output(['git','show',BASELINE+':sites/43cedar/interactive_map/index.html'],cwd=ROOT).decode()
 original=parse(baseline); data=deepcopy(original)
 stamp=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
 specifications=[
  ('RES31','43 Cedar - response to mockups 2 of 3.png','F2','Upstairs bathroom','Revised dimensioned bathroom plan','Dimensioned planning diagram','Bathroom layout · Rev D',
   'Owner-supplied revised bathroom plan. 157 × 126-inch room; 66 × 32-inch tub; joined 66-inch double vanity; 12-inch tub buffers at back and left end; 13 inches between tub and vanity; approximately 48 inches toward shower. One bathroom door in the straight right wall, hinged at linen-side jamb. Design concept for drafter review; field dimensions and product clearances require confirmation.'),
  ('RES32','43 Cedar - response to mockups 3 of 3.png','F2','Upstairs bathroom','Scaled bathroom cutaway','Native 3D reference','Bathroom layout · scaled cutaway',
   'Owner-supplied scaled native bathroom cutaway: tub on left and joined double vanity on right, with the approved 12-inch wall buffers. Toilet, shower and linen locations retained. Walls and cabinetry are cut away for visibility; vertical dimensions, window heights and finishes are illustrative. Use the companion dimensioned plan for layout review.'),
  ('RES33','Revision B coastal Craftsman bath(1).png','F2','Upstairs bathroom','Coastal Craftsman bathroom finish visual','Photoreal finish reference','Bathroom finishes · Revision B',
   'Owner-supplied coastal Craftsman finish illustration: freestanding tub, joined oak double vanity, warm white surfaces, bronze fittings and privacy windows. Illustrative finishes and perspective; use the companion plan and native cutaway for geometry and clearances.'),
  ('RES34','43 Cedar - response to mockups 1 of 3.png','EXT','Front exterior','Roof revision instructions for drafter','Annotated exterior reference','Roof revision instructions · November 2026',
   'Owner-supplied exterior design intent: bathroom shed dormer, continued front rake, deeper upper-right eave, coordinated overhangs and roof-edge details, new gutters/downspouts coordinated with existing corner drainage inlets, and two custom roof-following upper windows. Keep the large windowed front gable dominant. Drafter to confirm dimensions, framing, headroom and roof connections; gutters are required but not shown in the illustration.'),
 ]
 additions=[]; assets=[]
 for id,filename,floor,zone,title,kind,revision,notes in specifications:
  assert not any(p['id']==id for p in original['photos']),id
  source=supplied/filename
  payload=source.read_bytes()
  with Image.open(source) as image:
   image.verify()
  with Image.open(source) as image: width,height=image.size
  master=RELEASE/'originals'/f'{id}.png';master.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,master)
  assert sha(master.read_bytes())==sha(payload)
  relative=f'assets/resources/2026-11-20/{id}.webp'
  target=VIEWER.parent/relative;target.parent.mkdir(parents=True,exist_ok=True)
  compression={'lossless':True,'exact':True} if id=='RES31' else {'quality':94}
  with Image.open(source) as image:image.save(target,'WEBP',method=6,**compression)
  with Image.open(target) as compressed:
   assert compressed.size==(width,height)
   if id=='RES31':
    with Image.open(source) as image:assert ImageChops.difference(image.convert('RGBA'),compressed.convert('RGBA')).getbbox() is None
  displayed=target.read_bytes()
  obsolete=VIEWER.parent/f'assets/resources/2026-11-20/{id}.png'
  if obsolete.exists():obsolete.unlink()
  record=dict(id=id,imageId=id,type='resource',stage='Proposed · Resources',floor=floor,zone=zone,kind=kind,looking=title,
   filename=filename,source='Owner-supplied image · November 20, 2026',referenceStatus='Proposed design reference · retain stated assumptions',
   designVersion=revision,notes=notes,publishedAt=stamp,updatedAt=stamp,imageSHA256=sha(displayed),originalImageSHA256=sha(payload),
   qaStatus='Supplied image integrity and floor assignment verified',approval='Owner authorized live resource publication')
  data['photos'].append(record);data['resourceImages'][id]=relative;data['proposedResources']['records'].append(id)
  additions.append(record);assets.append(dict(id=id,path=target.relative_to(ROOT).as_posix(),filename=filename,floor=floor,
   bytes=len(displayed),sha256=sha(displayed),width=width,height=height,sourcePath=master.relative_to(ROOT).as_posix(),
   sourceBytes=len(payload),sourceSHA256=sha(payload),compression='lossless WebP' if id=='RES31' else 'WebP quality 94'))
 data['counts']=dict(Counter(p['floor']+'|'+p['stage'] for p in data['photos']))
 data['resourceRelease38']=dict(issue=38,addedAt=stamp,records=[a['id'] for a in assets],baseline=BASELINE)
 expected=deepcopy(data)
 # Remove only the additive changes and compare the complete pre-existing data structure.
 expected['photos']=expected['photos'][:-4]
 for a in assets: del expected['resourceImages'][a['id']]
 expected['proposedResources']['records']=expected['proposedResources']['records'][:-4]
 expected['counts']=original['counts'];del expected['resourceRelease38']
 assert expected==original,'Existing viewer data was changed'
 result=re.sub(PATTERN,lambda m:m.group(1)+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+m.group(3),baseline,flags=re.S)
 assert re.sub(PATTERN,'APPDATA',result,flags=re.S)==re.sub(PATTERN,'APPDATA',baseline,flags=re.S),'Viewer UI changed'
 VIEWER.write_text(result)
 manifest=dict(issue=38,baseline=BASELINE,assembledAt=stamp,existingRecords=len(original['photos']),totalRecords=len(data['photos']),
  viewerSHA256=sha(result.encode()),assets=assets,addedRecords=additions,
  checks=dict(existingRecordsUnchanged=True,existingMediaMappingsUnchanged=True,viewerUIUnchanged=True,
   floorAssignments={'F2':['RES31','RES32','RES33'],'EXT':['RES34']}))
 (RELEASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:manifest[k] for k in ['issue','existingRecords','totalRecords','viewerSHA256','checks']}))
 print(json.dumps({'sourceBytes':sum(a['sourceBytes'] for a in assets),'displayBytes':sum(a['bytes'] for a in assets),'assets':[{k:a[k] for k in ['id','bytes','sourceBytes','compression']} for a in assets]}))

if __name__=='__main__':main()
