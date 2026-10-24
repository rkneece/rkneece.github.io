"""Retire only the exact integrated heads recorded for this release."""
import json,os,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent
data=json.loads((root/'RETIRE.json').read_text())
api='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
def call(path,method='GET'):
 with urllib.request.urlopen(urllib.request.Request(api+path,headers=headers,method=method)) as r:
  return json.load(r) if r.status!=204 else None
for row in data:
 branch=row['branch'];head=call('/git/ref/heads/'+branch)['object']['sha']
 assert head==row['sha'],'Branch changed: '+branch
 for base in ['dev','main']:assert call('/compare/'+base+'...'+head)['ahead_by']==0,(branch,base)
 assert call('/git/ref/heads/'+branch)['object']['sha']==head
 call('/git/refs/heads/'+branch,'DELETE');print('Retired integrated branch',branch)
