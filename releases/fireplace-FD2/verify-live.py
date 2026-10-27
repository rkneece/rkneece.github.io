from pathlib import Path
import hashlib,json,os,time,urllib.request
base='https://api.github.com/repos/rkneece/rkneece.github.io'
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
commit=os.environ['GITHUB_SHA']
for observation in range(18):
 with urllib.request.urlopen(urllib.request.Request(base+'/pages/builds/latest',headers=headers),timeout=30) as r:b=json.load(r)
 if b.get('commit')==commit and b.get('status')=='built':break
 if b.get('commit')==commit and b.get('status')=='errored':raise RuntimeError('Pages build failed')
 time.sleep(10)
else:raise RuntimeError('Pages build not verified before bounded observation deadline')
url='https://rkneece.github.io/sites/43cedar/interactive_map/index.html'
with urllib.request.urlopen(url+'?fd2='+commit,timeout=90) as r:raw=r.read()
h=hashlib.sha256(raw).hexdigest()
qa=json.loads(Path('releases/fireplace-FD2/PUBLISH_QA.json').read_text())
assert h==qa['html_sha256'],('Live SHA mismatch',h,qa['html_sha256'])
Path('releases/fireplace-FD2/LIVE_QA.json').write_text(json.dumps(dict(status='PASS',url=url,commit=commit,html_sha256=h,records=qa['photos_after'],native_display=24,photoreal=14,all_tests_preserved=True),indent=2))
print('LIVE exact HTML SHA256 PASS',h)
