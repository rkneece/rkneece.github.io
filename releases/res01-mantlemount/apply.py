"""Add owner-approved MantelMount pre-drywall notes to RES01 only."""
import copy,datetime,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ADDITION="TV supported by MantelMount inside the stud cavity. Add a receptacle and install the mount before drywall."
path=Path('sites/43cedar/interactive_map/index.html')
raw=path.read_bytes();text=raw.decode()
pattern=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
match=pattern.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
indices=[i for i,x in enumerate(after['photos']) if x['id']=='RES01'];assert len(indices)==1
i=indices[0];row=after['photos'][i];previous=copy.deepcopy(row)
assert 'max two Shaker drawers per side' in row['notes']
assert 'Window casing consistent with the design standard in the rest of the house' in row['notes']
assert 'MantelMount' not in row['notes'], 'Already patched; reconcile current branch before retry'
row['notes']=row['notes']+' '+ADDITION
row['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
restored=copy.deepcopy(after);restored['photos'][i]=previous
assert restored==before,'Change outside RES01 notes/updatedAt'
assert {k:v for k,v in row.items() if k not in ('notes','updatedAt')}=={k:v for k,v in previous.items() if k not in ('notes','updatedAt')}
payload=json.dumps(after,separators=(',',':')).replace('</','<\\/')
output=text[:match.start(2)]+payload+text[match.end(2):]
parsed=pattern.search(output);assert json.loads(parsed[2])==after
assert output[:parsed.start(2)]==text[:match.start(2)] and output[parsed.end(2):]==text[match.end(2):]
path.write_text(output)
qa={'status':'PASS','issue':31,'checked_at':row['updatedAt'],'addition':ADDITION,
'photo_count':len(before['photos']),'only_changed_fields':['photos.RES01.notes','photos.RES01.updatedAt'],
'all_images_unchanged':True,'all_other_appdata_unchanged':True,'viewer_shell_byte_identical':True,
'html_sha256':hashlib.sha256(output.encode()).hexdigest(),'baseline_html_sha256':hashlib.sha256(raw).hexdigest()}
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps(qa),flush=True)
