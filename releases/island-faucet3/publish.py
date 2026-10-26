"""Publish only the 18 isolated island TEST resources; supports two verified passes."""
from pathlib import Path
import os,json,re,copy,hashlib,datetime
P=Path(__file__).resolve().parent
SITE=Path(os.environ.get('CEDAR_SITE','sites/43cedar/interactive_map'))
M=json.loads((P/'MANIFEST.json').read_text());PASS=(P/'PASS.txt').read_text().strip()
assert PASS in ('A','B')
path=SITE/'index.html';text=path.read_text()
assert hashlib.sha256(text.encode()).hexdigest()==M['expected_before_sha256'][PASS], 'Website baseline changed'
PAT=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)
match=PAT.search(text);assert match
before=json.loads(match[2]);after=copy.deepcopy(before)
ids={r['id'] for r in M['images']};assert ids=={f'RES{i:02d}' for i in range(9,27)}
assert [(r['view'],r['case']) for r in M['images']]==[(v,c) for v in M['view_order'] for c in M['case_order']]
byid={r['id']:r for r in after['photos']}
wrong='north mounting point, spout curves south over basin, outlet points down inside basin'
correct='far/south mounting lip, spout curves north toward the kitchen operator, downward outlet inside basin'
for r in M['images']:
 p=byid[r['id']];assert p['type']=='resource' and p['islandTestPhotorealSet']=='D-E-G-PR-20261024'
 asset=SITE/r['path'];assert hashlib.sha256(asset.read_bytes()).hexdigest()==r['sha256']
 if PASS=='A':assert wrong in p['notes']
 p['notes']=p['notes'].replace(wrong,correct)
 if r['view']=='Plan' and r['case'] in ('D','G') and 'fully occludes' not in p['notes']:
  p['notes']+=' In this overhead view the retained pendant fully occludes the correctly mounted faucet; inspect the kitchen and side views for fixture orientation.'
 p.update(filename=asset.name,imageSHA256=r['sha256'],nativeReferenceSHA256=r['native_sha256'],sourceSceneSHA256=M['scene_sha256'][r['case']],updatedAt=M['created_at'],islandFixtureQARevision='FAUCET3'+PASS,qaStatus='FAUCET3_MOUNT_SIDE_SPOUT_DIRECTION_VISUAL_QA_PASS',geometryStatus='AI finish study; native faucet mounted on south/far lip, spout toward north work side, nozzle inside basin; native model is geometry authority',islandFaucetPublicationPass=PASS)
 after['resourceImages'][r['id']]=r['path']+'?v=FAUCET3'+PASS
assert [p['id'] for p in after['photos'] if p['id'] in ids]==[r['id'] for r in M['images']]
assert len(before['photos'])==len(after['photos'])==414
assert [p for p in before['photos'] if p['id'] not in ids]==[p for p in after['photos'] if p['id'] not in ids]
for key in before:
 if key not in ('photos','resourceImages'):assert before[key]==after[key],key
for ident,value in before['resourceImages'].items():
 if ident not in ids:assert after['resourceImages'][ident]==value
assert before.keys()==after.keys() and before['resourceImages'].keys()==after['resourceImages'].keys()
payload=json.dumps(after,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
out=text[:match.start(2)]+payload+text[match.end(2):]
assert out[:match.start(2)]==text[:match.start(2)] and out[-len(text[match.end(2):]):]==text[match.end(2):]
assert json.loads(PAT.search(out)[2])==after
path.write_text(out)
qa=dict(status='PASS',publication_pass=PASS,root_cause=M['root_cause'],reviewed_images=18,record_count=414,non_test_records_unchanged=396,stable_resource_ids=True,all_other_data_and_ui_unchanged=True,view_first_option_order_preserved=True,ordered_ids=[r['id'] for r in M['images']],html_sha256=hashlib.sha256(out.encode()).hexdigest(),protected_model_refs=M['protected_model_refs'],test_branch=M['test_branch'])
(P/('PUBLISH_QA_'+PASS+'.json')).write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
