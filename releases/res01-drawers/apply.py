"""Guarded RES01-only update; preserve unrelated data and exact viewer shell."""
import base64,copy,datetime,hashlib,json,re
from pathlib import Path
from draw_res01 import ROOT
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
path=Path('sites/43cedar/interactive_map/index.html')
raw=path.read_bytes();s=raw.decode();match=PAT.search(s);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
rows=[(i,x) for i,x in enumerate(after['photos']) if x['id']=='RES01'];assert len(rows)==1
i,row=rows[0];old=copy.deepcopy(row)
assert '152-inch' in row['notes'] and '75-inch' in row['notes']
image=(ROOT/'43_Cedar_Fireplace_Measured_Concept.png').read_bytes()
after['resourceImages']['RES01']='data:image/png;base64,'+base64.b64encode(image).decode()
row.update(source='Measured fireplace concept elevation · updated October 26, 2026',
 designVersion='FF6 · RES01 Rev C · two Shaker drawers per side / Craftsman casing',
 notes='152-inch field-measured total width. Proposed 40/72/40-inch bays; 75-inch TV (approximately 65.4 x 36.8 inches). All-white stepped BPR-inspired mantel and recessed reclaimed brick. Tall privacy-window unit targets approximately 24 x 48 inches; final manufacturer catalog size and rough openings TBD. Matching benches: max two Shaker drawers per side; 18-inch seat height provisional. Window casing consistent with the design standard in the rest of the house: square-edge Craftsman, 3.5–4-inch legs and 5-inch head, flat butt joints, no decorative profiles. Retain vertical tongue and groove across the entire fireplace/south wall and alcoves, painted Benjamin Moore Swiss Coffee at 75% strength, eggshell. Installation heights, appliance clearances and all remaining dimensions require final coordination. TV supported by MantelMount inside the stud cavity. Add a receptacle and install the mount before drywall.',
 updatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'))
restored=copy.deepcopy(after);restored['photos'][i]=old;restored['resourceImages']['RES01']=before['resourceImages']['RES01'];assert restored==before
payload=json.dumps(after,separators=(',',':')).replace('</','<\\/')
result=s[:match.start(2)]+payload+s[match.end(2):]
check=PAT.search(result);assert result[:check.start(2)]==s[:match.start(2)] and result[check.end(2):]==s[match.end(2):]
assert json.loads(check[2])==after
path.write_text(result)
qa={'status':'PASS','issue':31,'checked_at':row['updatedAt'],'photo_count':len(before['photos']),
 'only_changed_record':'RES01','only_changed_image':'resourceImages.RES01','all_other_appdata_unchanged':True,'viewer_shell_byte_identical':True,
 'source_html_blob_sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
 'html_sha256':hashlib.sha256(result.encode()).hexdigest(),'image_sha256':hashlib.sha256(image).hexdigest(),
 'image_size':[1728,1440],'drawers_per_side':2,'drawer_style':'Shaker','window_casing':'House-standard square-edge Craftsman: 3.5–4-inch legs, 5-inch head, flat butt joints',
 'visual_review':'Diagram visually reviewed in active RES01 conversation before commit; exact image hash bound below.'}
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa),flush=True)
