"""Verify live/archive evidence, preserve tags and retire only the selected NI1 branches."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,tempfile,urllib.error,urllib.request,zipfile
from datetime import datetime,timezone

plan_path=Path(sys.argv[1]);plan=json.loads(plan_path.read_text());repo=os.environ['GITHUB_REPOSITORY']
assert repo==plan['repository']
base='https://api.github.com/repos/'+repo
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
def api(path,method='GET',body=None):
    request=urllib.request.Request(base+path,headers=headers,method=method,data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response) if response.status!=204 else None
if plan.get('publication_finalize_run'):
    url='https://api.github.com/repos/rkneece/rkneece.github.io/actions/runs/'+str(plan['publication_finalize_run'])
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60) as response:run=json.load(response)
    assert run['conclusion']=='success','Publisher finalization must succeed first'
with urllib.request.urlopen(urllib.request.Request(plan['live_url'],headers={'Cache-Control':'no-cache'}),timeout=60) as response:live=response.read()
assert hashlib.sha256(live).hexdigest()==plan['live_html_sha256'],'Live release bytes changed'
data=json.loads(re.search(r'<script id="appdata" type="application/json">(.*?)</script>',live.decode(),re.S)[1])
assert len(data['photos'])==460
allowed={'rkneece/43-cedar-blender':{'model/approved-north-island-farmhouse','test/island-NW-side-access'},
         'rkneece/rkneece.github.io':{'release/approved-north-island-farmhouse','test/island-NW-side-access'}}
assert {r['name'] for r in plan['branches']}<=allowed[repo]
for branch in plan['branches']:
    assert api('/git/ref/heads/'+branch['name'])['object']['sha']==branch['head'],'Source branch moved; do not delete'
    if branch['merged_required']:
        for target in ['dev','main']:assert api('/compare/'+target+'...'+branch['head'])['ahead_by']==0
with tempfile.TemporaryDirectory() as folder:
    hashes=sorted(set(plan['required_archive_sha256']))
    assert all(re.fullmatch('[a-f0-9]{64}',sha) for sha in hashes)
    urls=['gs://rkneece-43cedar-assets/43cedar/objects/sha256/'+sha[:2]+'/'+sha for sha in hashes]
    subprocess.run(['gcloud','storage','cp',*urls,folder+'/'],check=True)
    for sha in hashes:assert hashlib.sha256((Path(folder)/sha).read_bytes()).hexdigest()==sha
out=plan_path.parent
bundle=out/'FINAL_RELEASE_BUNDLE.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for name in plan['bundle_paths']:
        p=Path(name);assert p.is_file(),p;archive.write(p,str(p))
    archive.writestr('LIVE_HTML_SHA256.txt',hashlib.sha256(live).hexdigest()+'\n')
receipt=out/'FINAL_ARCHIVE_RECEIPT.json'
subprocess.run(['python','ops/cedar-archive/archive.py','--issue','21','--receipt',str(receipt),str(bundle),str(plan_path)],check=True)
archived=json.loads(receipt.read_text());assert all(a['verified'] for a in archived['assets'])
retired=[]
for branch in plan['branches']:
    tag='archive/ni1-20261026/'+branch['name']
    try:api('/git/refs','POST',{'ref':'refs/tags/'+tag,'sha':branch['head']})
    except urllib.error.HTTPError as error:
        if error.code!=422:raise
        assert api('/git/ref/tags/'+tag)['object']['sha']==branch['head']
    assert api('/git/ref/heads/'+branch['name'])['object']['sha']==branch['head']
    api('/git/refs/heads/'+branch['name'],'DELETE')
    retired.append({'branch':branch['name'],'sha':branch['head'],'archive_tag':tag})
report={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'live_html_sha256':plan['live_html_sha256'],
        'verified_existing_archive_objects':len(hashes),'final_bundle_manifest':archived['manifest_uri'],
        'final_bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'retired':retired,
        'other_test_branches_unchanged':True}
proof=out/'FINAL_QA.json';proof.write_text(json.dumps(report,indent=2)+'\n')
subprocess.run(['python','ops/cedar-archive/archive.py','--issue','21','--receipt',str(out/'FINAL_PROOF_RECEIPT.json'),str(proof)],check=True)
print('NI1_FINALIZATION_PASS '+json.dumps(report),flush=True)
