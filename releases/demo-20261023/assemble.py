"""Append October 23 demo photos to the current viewer without changing earlier data."""
from pathlib import Path
import json,re,hashlib,collections,copy
from PIL import Image

root=Path(__file__).resolve().parent
target=Path('sites/43cedar/interactive_map/index.html')
source=target.read_text()
match=re.search(r'(<script[^>]*id="appdata"[^>]*>)(.*?)(</script>)',source,re.S)
data=json.loads(match[2]);before=copy.deepcopy(data)
manifest=json.loads((root/'manifest.json').read_text())
assert len(manifest['photos'])==43
existing={p['id'] for p in data['photos']}
assert not existing.intersection(p['id'] for p in manifest['photos']), 'Batch already applied'
for p in manifest['photos']:
 path=target.parent/p['asset'];assert path.is_file(),path
 assert hashlib.sha256(path.read_bytes()).hexdigest()==p['sha256']
 Image.open(path).verify()
 assert p['floor'] in ['F1','F2'] and p['stage']=='Demo' and not p['confirmed']
 assert 0<=p['mapX']<=100 and 0<=p['mapY']<=100
 data['photos'].append({k:v for k,v in p.items() if k not in ['asset','sha256']})
 data['photoImages'][p['imageId']]=p['asset']
 data['viewpoints'].append(dict(viewpoint_id=p['viewpointId'],short_name=p['looking'],floor=p['floor'],looking_direction=p['facing'],confidence='Approximate'))
data['demo20261023Revision']=dict(siteVisitId='2026-10-23',count=43,floors=dict(collections.Counter(p['floor'] for p in manifest['photos'])),locationConfidence='Estimated from photo landmarks; all new records confirmed=false')
data['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in data['photos']))
data['buildId']=before['buildId']+'__Demo_20261023'
for key,value in before.items():
 if key not in ['photos','photoImages','viewpoints','counts','buildId']:assert data[key]==value,key
assert data['photos'][:len(before['photos'])]==before['photos']
assert data['viewpoints'][:len(before['viewpoints'])]==before['viewpoints']
assert all(data['photoImages'][k]==v for k,v in before['photoImages'].items())
assert len({p['id'] for p in data['photos']})==len(data['photos'])
payload=json.dumps(data,separators=(',',':')).replace('</','<\\/')
output=source[:match.start(2)]+payload+source[match.end(2):]
assert source[:match.start(2)]==output[:match.start(2)]
target.write_text(output)
# Canonical records are importable by the companion photo-labeling workflow.
(root/'labels.json').write_text(json.dumps(dict(schemaVersion=1,siteVisitId='2026-10-23',photos=manifest['photos']),indent=2)+'\n')
report=dict(status='PASS',added_photos=43,total_photos=len(data['photos']),floors=data['demo20261023Revision']['floors'],all_existing_records_and_images_preserved=True,all_new_assets_verified=True,all_new_locations_marked_approximate=True,source_sha256=hashlib.sha256(source.encode()).hexdigest(),output_sha256=hashlib.sha256(output.encode()).hexdigest())
(root/'PUBLISH_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
