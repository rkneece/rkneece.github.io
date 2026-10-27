import json,urllib.request,datetime,time
BASE='https://raw.githubusercontent.com/rkneece/43-cedar-blender/main/ops/cedar-recovery/claims/'
expected={"25":"ready-lighting-25-1793109145585","34":"ready-lighting-34-1793109150085"}
for issue,token in expected.items():
 with urllib.request.urlopen(BASE+issue+'.json?check='+str(time.time_ns()),timeout=30) as response:claim=json.load(response)
 assert claim['token']==token and not claim.get('released_at'),'Publisher claim changed'
 assert datetime.datetime.fromisoformat(claim['expires_at'].replace('Z','+00:00'))>datetime.datetime.now(datetime.timezone.utc),'Publisher claim expired'
print('25/34 owner tokens and lease verified')
