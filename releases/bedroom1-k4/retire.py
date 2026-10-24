"""Retire only explicitly named branches after verified live delivery and ancestry checks."""
import json,os,urllib.request,urllib.parse,pathlib
repo=os.environ['GITHUB_REPOSITORY'];base='https://api.github.com/repos/'+repo
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
def call(path,method='GET'):
 with urllib.request.urlopen(urllib.request.Request(base+path,headers=headers,method=method)) as r:
  return json.load(r) if r.status!=204 else None
proof=json.loads(pathlib.Path(os.environ['K4_LIVE_PROOF']).read_text());assert proof['status']=='PASS'
branches=json.loads(os.environ['K4_RETIRE_BRANCHES']);out=[]
for branch in branches:
 try:head=call('/git/ref/heads/'+urllib.parse.quote(branch,safe='/'))['object']['sha']
 except urllib.error.HTTPError as e:
  if e.code==404:out.append({'branch':branch,'status':'already absent'});continue
  raise
 for target in ['dev','main']:assert call('/compare/'+target+'...'+head)['ahead_by']==0,(branch,target)
 assert call('/git/ref/heads/'+urllib.parse.quote(branch,safe='/'))['object']['sha']==head
 call('/git/refs/heads/'+urllib.parse.quote(branch,safe='/'),'DELETE')
 out.append({'branch':branch,'head':head,'status':'retired after live verification and dev/main ancestry check'})
pathlib.Path('K4_RETIREMENT_QA.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
