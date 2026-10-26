"""Replace only current Option A revised image records and assets after exact-hash review."""
from pathlib import Path
import base64,copy,hashlib,io,json,re,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parent
M=json.loads((ROOT/'RELEASE.json').read_text())
site=Path('sites/43cedar/interactive_map/index.html');text=site.read_text()
def sha(raw):return hashlib.sha256(raw).hexdigest()
assert subprocess.check_output(['git','hash-object',str(site)],text=True).strip()==M['baseline_html_blob'],'Main HTML changed; refresh before assembly'
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);match=pat.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
old={r['id']:r for r in before['photos']};updated={r['id'] for r in M['images']}
assert len(updated)==16 and updated=={f'CW6_{kind}{i:02}' for kind in ['N','P'] for i in range(1,9)}
assert len(old)==len(before['photos'])
proof=[]
for row in M['images']:
 ident=row['id'];assert old[ident]['islandTestSet']=='CW6-A-revised' and old[ident]['stage']=='Proposed - Tests'
 assert row['review'].startswith('PASS:')
 raw=(ROOT/'restored'/row['sha256']).read_bytes();assert sha(raw)==row['sha256']
 with Image.open(io.BytesIO(raw)) as im:
  dimensions=list(im.size);buf=io.BytesIO();im.convert('RGB').save(buf,'JPEG',quality=91,subsampling=0,optimize=True)
 data=buf.getvalue();group='blenderImages' if row['type']=='blender' else 'photorealImages'
 after[group][ident]='data:image/jpeg;base64,'+base64.b64encode(data).decode()
 p=next(p for p in after['photos'] if p['id']==ident)
 p.update(modelCommit=M['model_commit'],sourceSceneSHA256=M['source_scene_sha256'],sourceImageSHA256=row['sha256'],imageSHA256=sha(data),updatedAt=M['created_at'],qaStatus='CW6_EW1_EXACT_SOURCE_VISUAL_PASS',lightingRevision='EW1',notes=M['notes'])
 if row['type']=='photoreal':p.update(sourceRenderId=row['native_id'],nativeReferenceSHA256=row['native_sha256'])
 proof.append({'id':ident,'source_sha256':row['sha256'],'display_sha256':sha(data),'dimensions':dimensions})
assert len(after['photos'])==len(before['photos']) and [p['id'] for p in after['photos']]==[p['id'] for p in before['photos']]
for p in after['photos']:
 if p['id'] not in updated:assert p==old[p['id']]
for group in ['blenderImages','photorealImages','resourceImages']:
 assert set(after[group])==set(before[group])
 for ident,asset in before[group].items():
  if ident not in updated:assert after[group][ident]==asset
for key in before:
 if key not in ['photos','blenderImages','photorealImages']:assert after[key]==before[key],key
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
result=text[:match.start(2)]+payload+text[match.end(2):]
assert result[:match.start(2)]==text[:match.start(2)] and result[pat.search(result).end(2):]==text[match.end(2):]
assert json.loads(pat.search(result)[2])==after
site.write_text(result)
qa={'status':'PASS','issue':25,'revision':'EW1','before_records':len(before['photos']),'after_records':len(after['photos']),'replaced_test_records':16,'all_other_records_and_assets_unchanged':True,'measured_plan_unchanged':True,'production_gallery_unchanged':True,'model_branch_not_merged':True,'UI_and_floorplans_unchanged':True,'html_sha256':sha(result.encode()),'updated_ids':sorted(updated),'published_images':proof}
(ROOT/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps({k:v for k,v in qa.items() if k!='published_images'}),flush=True)
