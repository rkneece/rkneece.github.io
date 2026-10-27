"""Release only reviewed production FD2 assets from the exact publisher baseline."""
from pathlib import Path
import base64,copy,hashlib,io,json,re,subprocess,os
from PIL import Image
R=Path(__file__).resolve().parent;M=json.loads((R/'RELEASE.json').read_text());site=Path('sites/43cedar/interactive_map/index.html')
sha=lambda b:hashlib.sha256(b).hexdigest()
text=site.read_text();raw=text.encode();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==M['baseline_html_git_blob'],'Baseline moved'
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);match=pat.search(text);before=json.loads(match[2]);after=copy.deepcopy(before);old={r['id']:r for r in before['photos']};rows={r['id']:r for r in after['photos']}
D=R/'restored';D.mkdir(exist_ok=True);hashes={r['sha256'] for r in M['native']}|{r['output_sha256'] for r in M['photoreal']}
missing=[h for h in sorted(hashes) if not (D/h).exists()]
if missing:
 subprocess.run(['gcloud','storage','cp',*['gs://rkneece-43cedar-assets/43cedar/objects/sha256/'+h[:2]+'/'+h for h in missing],str(D)+'/'],check=True,timeout=180)
for h in hashes:assert sha((D/h).read_bytes())==h
native={r['id']:r for r in M['native']};changes=[];proof=[]
def replace(ident,nid,h,group):
 assert ident in old and old[ident]['stage']=='Proposed - Tests'
 b=(D/h).read_bytes()
 with Image.open(io.BytesIO(b)) as im:
  dims=list(im.size);out=io.BytesIO();im.convert('RGB').save(out,'JPEG',quality=91,optimize=True,subsampling=0)
 data=out.getvalue();after[group][ident]='data:image/jpeg;base64,'+base64.b64encode(data).decode()
 row=rows[ident];row.setdefault('originModelBranch',row.get('modelBranch'));row['modelBranch']='fix/fireplace-res01-drawers';row.update(updatedAt=M['created_at'],imageSHA256=sha(data),sourceImageSHA256=h,sourceSceneSHA256=native[nid]['source_scene_sha256'],validatedCombinedSceneSHA256=native[nid]['source_scene_sha256'],sourceRenderId=nid,nativeReferenceSHA256=native[nid]['sha256'],sourcePNG_SHA256=native[nid]['sha256'],modelCommit=M['model_commit'],fireplaceRevision='RES01 Rev D / FD2 tests',qaStatus='FD2_EXACT_SOURCE_VISUAL_ARCHIVE_PASS')
 row['notes']=row.get('notes','')+' Fireplace benches: exactly two side-by-side Shaker drawers per side in one row, matching RES01 Rev D.'
 changes.append(ident);proof.append(dict(id=ident,native=nid,source_sha256=h,display_sha256=sha(data),dimensions=dims))
for ident,r in native.items():
 replace(ident,ident,r['sha256'],'blenderImages')
 rows[ident].update(renderedAt=M['created_at'],nativeActualDimensions=r['dimensions'],renderSamples=r['samples'],renderDenoise=True,renderEngine='CYCLES')
for ident,nid in M['aliases'].items():replace(ident,nid,native[nid]['sha256'],'blenderImages')
for r in M['photoreal']:
 assert r['review'].startswith('PASS:') and r['source_native_sha256']==native[r['native']]['sha256']
 replace(r['id'],r['native'],r['output_sha256'],'photorealImages')
 rows[r['id']].update(generatedAt=r['callReturnedAt'],generationAttemptId=r['attempt_id'],finishReferenceSHA256=r['finish_reference_sha256'])
assert len(changes)==6 and len(set(changes))==6
for ident,r in old.items():
 if ident not in changes:assert rows[ident]==r,ident
for group in ['blenderImages','photorealImages','resourceImages']:
 assert set(before[group])==set(after[group])
 for ident,v in before[group].items():
  if ident not in changes:assert after[group][ident]==v
for k in before:
 if k not in ['photos','blenderImages','photorealImages']:assert after[k]==before[k],k
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
result=text[:match.start(2)]+payload+text[match.end(2):];assert json.loads(pat.search(result)[2])==after
site.write_text(result)
qa=dict(status='PASS',issue=32,native_unique=3,native_display=3,photoreal=3,changed_ids=changes,photos_before=len(before['photos']),photos_after=len(after['photos']),all_unaffected_records_and_assets_preserved=True,all_other_tests_preserved=True,resources_UI_preserved=True,baseline_blob=M['baseline_html_git_blob'],html_sha256=sha(result.encode()),published_images=proof,pending_test_overlap=M['pending_test_overlap'])
(R/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps({k:v for k,v in qa.items() if k!='published_images'}))
