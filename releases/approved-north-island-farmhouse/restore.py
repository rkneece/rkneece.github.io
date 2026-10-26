"""Restore exact approved bytes from the private archive, without GitHub cross-repo credentials."""
from pathlib import Path
import hashlib,json,re,subprocess,time

root=Path(__file__).resolve().parent
release=json.loads((root/'RELEASE.json').read_text())
dest=root/'restored';dest.mkdir(exist_ok=True)
hashes=sorted({r['sha256'] for r in release['native']}|
              {r['output_sha256'] for r in release['photoreal']}|
              set(release['additional_archive_objects']))
assert all(re.fullmatch('[a-f0-9]{64}',sha) for sha in hashes)
for attempt in range(4):
    missing=[sha for sha in hashes if not (dest/sha).exists() or hashlib.sha256((dest/sha).read_bytes()).hexdigest()!=sha]
    if not missing:break
    urls=['gs://rkneece-43cedar-assets/43cedar/objects/sha256/'+sha[:2]+'/'+sha for sha in missing]
    run=subprocess.run(['gcloud','storage','cp',*urls,str(dest)+'/'])
    if run.returncode and attempt<3:time.sleep(2**(attempt+1))
verified=[]
for sha in hashes:
    p=dest/sha
    assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha,('Missing or invalid archive object',sha)
    verified.append({'sha256':sha,'bytes':p.stat().st_size,'verified':True})
report={'status':'PASS','source':'independent private-bucket download and SHA256 readback',
        'objects':verified,'native_images':len(release['native']),
        'photoreal_images':len(release['photoreal'])}
(root/'ASSET_QA.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':'PASS','verified_archive_objects':len(verified),'native':45,'AI':29}),flush=True)
