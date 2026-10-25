"""HTML-only Proposed-Tests category, existing current/reference images reused."""
from pathlib import Path
import os,json,re,copy,hashlib,collections
P=Path(__file__).resolve().parent;SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map'));M=json.loads((P/'MANIFEST.json').read_text());path=SITE/'index.html';text=path.read_text();assert hashlib.sha256(text.encode()).hexdigest()==M['before_html_sha256']
pat=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S);mt=pat.search(text);before=json.loads(mt[2]);after=copy.deepcopy(before);byid={p['id']:p for p in after['photos']};moved={f'RES{i:02d}' for i in range(7,30)};assert len(before['photos'])==417 and moved.issubset(byid)
for ident in moved:
 p=byid[ident];assert p['stage']=='Proposed · Resources';p['stage']='Proposed-Tests'
current={};kind=next(p['kind'] for p in before['photos'] if p['type']=='photoreal')
for r in M['images']:
 assert r['id'] not in byid;f=SITE/r['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
 p=dict(id=r['id'],imageId=r['id'],type='photoreal',stage='Proposed · Resources',floor='F1',zone='Dining Area',kind=kind,looking=r['label']+' · CURRENT PROPOSED',filename=f.name,designVersion='Current proposed · matching island viewpoints',variant='Current proposed reference',currentDesignComparison=True,currentDesignView=r['view'],source='Existing current-design photographic reference · authoritative K4 scene',sourceRepo='rkneece/43-cedar-blender',sourceRef=M['model_source_ref'],sourceSceneSHA256=M['source_scene_sha256'],imageSHA256=r['sha256'],referenceStatus='CURRENT PROPOSED DIRECTION · unchanged model',geometryStatus='Photographic finish illustration; authoritative K4 source geometry unchanged',qaStatus='CURRENT_REFERENCE_VISUAL_QA_REVIEWED',publishedAt=M['created_at'],updatedAt=M['created_at'],notes='Current proposed design in the matching '+r['view']+' viewpoint. Original island, post-side seating, sink, dishwasher, microwave, pantry, doors and furniture retained from the authoritative K4 scene. This current reference is also included beside isolated alternatives in Proposed-Tests for comparison. Image reused without further rendering or generation.')
 current[r['view']]=p;after['photorealImages'][r['id']]=r['path']+'?v=CURRENT1'
block=[]
for v in M['view_order']:
 block.append(current[v]);block.extend(next(p for p in after['photos'] if p.get('islandTestView')==v and p.get('islandTestOption')==c) for c in 'DEG')
block.extend(byid[x] for x in ['RES07','RES08']);first=min(i for i,p in enumerate(before['photos']) if p['id'] in moved)
after['photos']=[p for p in after['photos'][:first] if p['id'] not in moved]+block+[p for p in after['photos'][first:] if p['id'] not in moved]
assert len(after['photos'])==424 and len({p['id'] for p in after['photos']})==424
assert [p for p in after['photos'] if p['id'] not in moved and not p.get('currentDesignComparison')]==[p for p in before['photos'] if p['id'] not in moved]
for p in before['photos']:
 if p['id'] in moved:
  a=copy.deepcopy(p);b=copy.deepcopy(byid[p['id']]);a.pop('stage');b.pop('stage');assert a==b
for k in before:
 if k not in ('photos','photorealImages','counts','proposedResources'):assert before[k]==after[k],k
for k,v in before['photorealImages'].items():assert after['photorealImages'][k]==v
assert after['resourceImages']==before['resourceImages']
after['counts']=dict(collections.Counter(p['floor']+'|'+p['stage'] for p in after['photos']))
after['proposedResources']['records']=[f'RES{i:02d}' for i in range(1,7)]+[current[v]['id'] for v in M['view_order']]
after['proposedTests']={'section':'proposed-tests','label':'Proposed-Tests','moved_ids':sorted(moved),'current_reference_ids':[current[v]['id'] for v in M['view_order']],'view_order':M['view_order'],'comparison_order':['Current','D','E','G'],'display_count':30}
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/');out=text[:mt.start(2)]+payload+text[mt.end(2):]
changes=[
 ("'Proposed · Photoreal', 'Proposed · Resources', 'Build'", "'Proposed · Photoreal', 'Proposed · Resources', 'Proposed-Tests', 'Build'"),
 ("stage:location.hash === '#proposed-resources' ? 'Proposed · Resources' : 'Existing'", "stage:['#proposed-tests','#tests'].includes(location.hash) ? 'Proposed-Tests' : location.hash === '#proposed-resources' ? 'Proposed · Resources' : 'Existing'"),
 ("const isResources = () => state.stage === 'Proposed · Resources';", "const isTests = () => state.stage === 'Proposed-Tests';\n  const isResources = () => isTests() || state.stage === 'Proposed · Resources';\n  const matchesStage = (p, stage) => p.stage === stage || (stage === 'Proposed-Tests' && !!p.currentDesignComparison);"),
 ("p.floor === s.floor && p.stage === s.stage", "p.floor === s.floor && matchesStage(p, s.stage)"),
 ("p.floor === state.floor && p.stage === state.stage", "p.floor === state.floor && matchesStage(p, state.stage)"),
 ("state.stage === 'Proposed · Resources' ? '#proposed-resources' : location.pathname + location.search", "isTests() ? '#proposed-tests' : state.stage === 'Proposed · Resources' ? '#proposed-resources' : location.pathname + location.search"),
 ("isResources() ? 'Proposed resources' : state.room || 'Photo gallery'", "isTests() ? 'Proposed-Tests' : isResources() ? 'Proposed resources' : state.room || 'Photo gallery'"),
 ("isResources() ? 'Diagrams & references · tap to inspect' : stageName(state.stage) + ' · tap to open'", "isTests() ? 'Matching viewpoints · Current, D, E, G · study graphics below' : isResources() ? 'Current proposed directions · tap to inspect' : stageName(state.stage) + ' · tap to open'")]
for old,new in changes:
 assert out.count(old)==1,(old,out.count(old));out=out.replace(old,new,1)
assert json.loads(pat.search(out)[2])==after;path.write_text(out)
(P/'viewer.js').write_text(re.findall(r'<script(?: [^>]*)?>(.*?)</script>',out,re.S)[-1])
tests=[p for p in after['photos'] if p['stage']=='Proposed-Tests' or p.get('currentDesignComparison')];resources=[p for p in after['photos'] if p['stage']=='Proposed · Resources'];assert len(tests)==30 and len(resources)==13
assert [(p.get('currentDesignView') or p.get('islandTestView'),'Current' if p.get('currentDesignComparison') else p.get('islandTestOption')) for p in tests[:28]]==[(v,c) for v in M['view_order'] for c in ['Current','D','E','G']]
qa=dict(status='PASS',category='Proposed-Tests',html_sha256=hashlib.sha256(out.encode()).hexdigest(),no_rerenders=True,original_image_paths_and_bytes_unchanged=True,existing_image_types_and_kind_filters_unchanged=True,moved_ids=sorted(moved),current_reference_ids=[current[v]['id'] for v in M['view_order']],test_ids=[p['id'] for p in tests],comparison_items=30,alternatives=21,study_graphics=2,current_references=7,floor1_resources=11,total_resources=13,total_records=424,unrelated_original_records_unchanged=394,model_dev_main_unchanged=True)
(P/'PUBLISH_QA.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
