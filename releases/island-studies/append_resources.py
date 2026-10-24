"""Append alternative-study resources while preserving all existing viewer data."""
from pathlib import Path
import re,json,copy,hashlib,collections,datetime,sys
ROOT=Path(__file__).resolve().parent
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
def patch(raw,assets):
 text=raw.decode();m=PAT.search(text);assert m
 before=json.loads(m[2]);after=copy.deepcopy(before)
 numbers=[int(p['id'][3:]) for p in before['photos'] if re.fullmatch('RES[0-9]+',p['id'])]
 start=max(numbers,default=0)+1
 now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
 titles=[('43_Cedar_Proposed_Island_Alternative.svg','Island Plan B · 88 × 48 inches · three south seats','Dimensioned proposed alternative; occupied dining clearance remains conditional'),('43_Cedar_Island_Studies_Summary.svg','Island alternatives A–G · study summary','Comparison studies; E and G are visualization tests, not selected plans')]
 added=[]
 for i,(filename,title,status) in enumerate(titles):
  ident=f'RES{start+i:02d}';asset='assets/island-studies/'+filename
  row=dict(id=ident,imageId=ident,type='resource',stage='Proposed · Resources',floor='F1',zone='Dining Area',kind='Reference diagram',looking=title,filename=filename,source='Separate island-backup dimensional study · 24 October 2026',referenceStatus=status,designVersion='Proposed alternative · Island Studies 2026-10-24',notes='Alternative planning study only. Existing coordinated island/model remains the baseline. Fixed P135 casing retained. Sink and dishwasher share the north workface. Left/dining-side porch slider panel operates; a fourth west stool crosses its approach. Assumed occupied-depth and current table/chair footprints determine the displayed gaps. E/G native comparison tests are isolated on model branch test/island-E-G; no model Dev merge.',publishedAt=now,updatedAt=now,imageSHA256=hashlib.sha256((assets/filename).read_bytes()).hexdigest(),approval='Owner authorized publishing the two alternative-study graphics; not design selection',variant='Proposed Alternative — Planning Study')
  after['photos'].append(row);after.setdefault('resourceImages',{})[ident]=asset;added.append(ident)
 after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
 restored=copy.deepcopy(after);restored['photos']=[p for p in restored['photos'] if p['id'] not in added]
 for ident in added:del restored['resourceImages'][ident]
 restored['counts']=before['counts']
 assert restored==before,'Existing record, image or plan changed'
 payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
 output=(text[:m.start(2)]+payload+text[m.end(2):]).encode()
 assert json.loads(PAT.search(output.decode())[2])==after
 return output,dict(status='PASS',added_resource_ids=added,before_records=len(before['photos']),after_records=len(after['photos']),original_records_images_plans_and_ui_unchanged=True,html_sha256=hashlib.sha256(output).hexdigest(),assets=[dict(path='assets/island-studies/'+f,sha256=hashlib.sha256((assets/f).read_bytes()).hexdigest()) for f,_,_ in titles])
if __name__=='__main__':
 source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('sites/43cedar/interactive_map/index.html')
 assets=Path(sys.argv[2]) if len(sys.argv)>2 else Path('sites/43cedar/interactive_map/assets/island-studies')
 out,qa=patch(source.read_bytes(),assets);source.write_bytes(out)
 dest=Path(sys.argv[3]) if len(sys.argv)>3 else Path('releases/island-studies/PUBLISH_QA.json')
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
