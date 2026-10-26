from pathlib import Path
import json,hashlib,subprocess,os,shutil,urllib.request,time
ROOT=Path(__file__).resolve().parent;SITE=Path('sites/43cedar/interactive_map/index.html')
REQ=json.loads((ROOT/'REQUEST.json').read_text());M=json.loads((ROOT/'RELEASE.json').read_text())
branch='test/option-A-revised-lighting-gallery'
def run(*a,**kw):return subprocess.run(a,check=True,**kw)
def remote(ref):return subprocess.check_output(['git','ls-remote','origin','refs/heads/'+ref],text=True).split()[0]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def commit(paths,message,dest,expected):
 assert remote(dest)==expected,'Branch changed during QA; stop before publishing'
 run('git','add',*map(str,paths))
 run('git','-c','user.name=43 Cedar test gallery','-c','user.email=actions@users.noreply.github.com','commit','-m',message)
 run('git','push','origin','HEAD:'+dest)
if REQ['phase']=='assemble':
 assert remote('main')==M['website_baseline_commit'],'Website baseline changed; rebase assembly'
 restored=ROOT/'restored';restored.mkdir(exist_ok=True)
 for row in M['images']:
  sha=row['sha256'];p=restored/sha
  run('gcloud','storage','cp','gs://rkneece-43cedar-assets/43cedar/objects/sha256/'+sha[:2]+'/'+sha,str(p),'--quiet')
  assert digest(p)==sha
 run('python',str(ROOT/'publish.py'))
 run('node',str(ROOT/'check-browser.cjs'))
 run('python','ops/cedar-archive/archive.py','--issue','25','--receipt',str(ROOT/'STAGED_ARCHIVE_RECEIPT.json'),str(SITE),str(ROOT/'RELEASE.json'),str(ROOT/'PUBLISH_QA.json'),str(ROOT/'BROWSER_QA.json'))
 commit([SITE,ROOT/'PUBLISH_QA.json',ROOT/'BROWSER_QA.json',ROOT/'STAGED_ARCHIVE_RECEIPT.json'],'Stage reviewed Option A revised lighting corrections only [skip ci]',branch,os.environ['GITHUB_SHA'])
elif REQ['phase']=='publish':
 qa=json.loads((ROOT/'PUBLISH_QA.json').read_text());assert qa['status']=='PASS' and qa['html_sha256']==REQ['reviewed_html_sha256']==digest(SITE)
 assert json.loads((ROOT/'BROWSER_QA.json').read_text())['status']=='PASS'
 baseline=M['website_baseline_commit'];assert remote('main')==baseline,'Hosting main moved; reconcile before data-only commit'
 # Save reviewed data and proof, then construct a direct commit from CURRENT main.
 # No test/model/release branch ancestry is merged into production.
 files=[SITE,ROOT/'PUBLISH_QA.json',ROOT/'BROWSER_QA.json',ROOT/'RELEASE.json',ROOT/'STAGED_ARCHIVE_RECEIPT.json']
 saved={str(p):p.read_bytes() for p in files}
 scripts={str(p):p.read_bytes() for p in [ROOT/'check-browser.cjs',ROOT/'execute.py']}
 run('git','fetch','origin','main');run('git','checkout','--detach',baseline)
 for name,data in saved.items():p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 for name,data in scripts.items():Path(name).write_bytes(data)
 commit(files,'Correct Option A revised pendant lighting in Proposed - Tests', 'main',baseline)
 published_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 run('curl','--fail-with-body','-X','POST','-H','Authorization: Bearer '+os.environ['GH_TOKEN'],'-H','Accept: application/vnd.github+json','https://api.github.com/repos/rkneece/rkneece.github.io/pages/builds')
 url='https://rkneece.github.io/sites/43cedar/interactive_map/index.html'
 actual=None
 for _ in range(60):
  try:
   with urllib.request.urlopen(url+'?cw6='+published_commit,timeout=40) as r:raw=r.read()
   actual=hashlib.sha256(raw).hexdigest()
   if actual==qa['html_sha256']:break
  except Exception:pass
  time.sleep(5)
 assert actual==qa['html_sha256'],'Live bytes did not reach reviewed hash; inspect deployment without regenerating'
 run('node',str(ROOT/'check-browser.cjs'),url+'?cw6='+published_commit)
 shutil.copy2(ROOT/'BROWSER_QA.json',ROOT/'LIVE_BROWSER_QA.json')
 live=dict(status='PASS',html_sha256=actual,published_commit=published_commit,replaced_test_records=16,model_branch_not_merged=True,dev_unchanged=True,production_records_unchanged=True,url=url)
 (ROOT/'LIVE_QA.json').write_text(json.dumps(live,indent=2))
 run('python','ops/cedar-archive/archive.py','--issue','25','--receipt',str(ROOT/'FINAL_ARCHIVE_RECEIPT.json'),str(SITE),str(ROOT/'RELEASE.json'),str(ROOT/'PUBLISH_QA.json'),str(ROOT/'LIVE_QA.json'),str(ROOT/'LIVE_BROWSER_QA.json'))
 commit([ROOT/'LIVE_QA.json',ROOT/'LIVE_BROWSER_QA.json',ROOT/'FINAL_ARCHIVE_RECEIPT.json'],'Record exact live Option A revised test-gallery verification and archive [skip ci]','main',published_commit)
else:raise RuntimeError('Unknown release phase')
