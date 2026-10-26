"""Publish reviewed RES01 Rev D with visible MantelMount instructions."""
import base64,copy,datetime,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
path=Path('sites/43cedar/interactive_map/index.html')
raw=path.read_bytes();text=raw.decode();pattern=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
match=pattern.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
indices=[i for i,x in enumerate(after['photos']) if x['id']=='RES01'];assert len(indices)==1
i=indices[0];row=after['photos'][i];prior=copy.deepcopy(row)
assert 'TV supported by MantelMount inside the stud cavity.' in row['notes']
assert 'install the mount before drywall.' in row['notes']
image=Path('releases/res01-drawers/43_Cedar_Fireplace_Measured_Concept.png').read_bytes()
assert hashlib.sha256(image).hexdigest()=='eda1d19c88de7289a35d8b990b38a9c78723819181424a3259da592f054ef482'
after['resourceImages']['RES01']='data:image/png;base64,'+base64.b64encode(image).decode()
row['designVersion']='FF6 · RES01 Rev D · visible MantelMount / pre-drywall notes'
row['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
assert row['notes']==prior['notes']
restored=copy.deepcopy(after);restored['photos'][i]=prior;restored['resourceImages']['RES01']=before['resourceImages']['RES01'];assert restored==before
payload=json.dumps(after,separators=(',',':')).replace('</','<\\/')
output=text[:match.start(2)]+payload+text[match.end(2):];new=pattern.search(output)
assert json.loads(new[2])==after
assert output[:new.start(2)]==text[:match.start(2)] and output[new.end(2):]==text[match.end(2):]
path.write_text(output)
qa={'status':'PASS','issue':31,'checked_at':row['updatedAt'],'photo_count':len(before['photos']),
'only_changed_record':'RES01','only_changed_image':'resourceImages.RES01','notes_unchanged':True,
'all_other_appdata_unchanged':True,'viewer_shell_byte_identical':True,
'html_sha256':hashlib.sha256(output.encode()).hexdigest(),'baseline_html_sha256':hashlib.sha256(raw).hexdigest(),
'image_sha256':'eda1d19c88de7289a35d8b990b38a9c78723819181424a3259da592f054ef482','image_size':[1728,1560],
'visible_image_callout':['TV MOUNT / BEFORE DRYWALL','TV supported by MantelMount inside the stud cavity.','Add a receptacle and install the mount before drywall.'],
'visual_review':'Exact PNG visually reviewed in active RES01 conversation; drawing geometry unchanged.'}
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps(qa),flush=True)
