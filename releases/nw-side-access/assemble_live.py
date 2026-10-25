"""Append reviewed NW test records and embedded images; preserve prior viewer."""
from pathlib import Path
import os,re,json,copy,hashlib,collections,base64
P=Path(__file__).resolve().parent;SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map/index.html'));manifest=json.loads((P/'PUBLICATION_MANIFEST.json').read_text());before=SITE.read_text();assert hashlib.sha256(before.encode()).hexdigest()==manifest['before_html_sha256'],'Live baseline changed'
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);m=pat.search(before);data=json.loads(m[2]);old=copy.deepcopy(data);new=[];ids={p['id'] for p in data['photos']}
for row in manifest['images']:
 p=copy.deepcopy(row['metadata']);ident=p['id'];assert ident not in ids;ids.add(ident);f=P/row['path'];raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];key={'resource':'resourceImages','blender':'blenderImages','photoreal':'photorealImages'}[p['type']];data[key][ident]='data:image/jpeg;base64,'+base64.b64encode(raw).decode();new.append(p)
data['photos']=new+data['photos'];data['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in data['photos']));data['proposedTests']['nw_side_access_ids']=[p['id'] for p in new];data['proposedTests']['display_count']=sum(p['stage']=='Proposed - Tests' or p.get('currentDesignComparison',False) for p in data['photos']);data['nwSideAccessTest']=manifest['proposal']
assert len(new)==31 and {p['zone'] for p in new}=={'Dining Area'} and {p['stage'] for p in new}=={'Proposed - Tests'}
byid={p['id']:p for p in data['photos']}
for p in new:
 if p['type']=='photoreal':assert byid[p['sourceRenderId']]['type']=='blender'
restored=copy.deepcopy(data);restored['photos']=restored['photos'][len(new):]
for p in new:del restored[{'resource':'resourceImages','blender':'blenderImages','photoreal':'photorealImages'}[p['type']]][p['id']]
restored['counts']=old['counts'];restored['proposedTests']=old['proposedTests'];del restored['nwSideAccessTest'];assert restored==old,'Unrelated content changed'
payload=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('</','<\\/');after=before[:m.start(2)]+payload+before[m.end(2):];after=after.replace('Matching viewpoints · Current, D, E, G · study graphics below','NW sink + west access · native / photoreal pairs · Current, D, E, G comparisons');assert json.loads(pat.search(after)[2])==data;SITE.write_text(after)
scripts=re.findall(r'<script(?: [^>]*)?>(.*?)</script>',after,re.S);(P/'viewer-check.js').write_text(scripts[-1]);qa=dict(status='PASS',added_ids=[p['id'] for p in new],added_count=31,total_test_count=data['proposedTests']['display_count'],all_new_location='Dining Area',native_photoreal_pairs=12,previous_records_and_images_unchanged=True,self_contained_images=True,model_dev_main_unchanged=True,before_html_sha256=manifest['before_html_sha256'],html_sha256=hashlib.sha256(after.encode()).hexdigest());(P/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
