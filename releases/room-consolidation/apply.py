"""Consolidate room names on the latest viewer without replacing imagery or mappings."""
import collections, copy, json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parent
RULES = json.loads((ROOT / 'rooms.json').read_text())
ANCHOR = "  const data = JSON.parse($('appdata').textContent);"
START, END = '  // ROOM NORMALIZATION START', '  // ROOM NORMALIZATION END'

def normalize(data):
    changes = []
    for p in data['photos']:
        old = p.get('zone', '')
        new = RULES['photoOverrides'].get(p['id'], RULES['aliases'].get(p.get('floor'), {}).get(old, old))
        if new != old:
            p.setdefault('originalZone', old)
            p['zoneAliases'] = list(dict.fromkeys(p.get('zoneAliases', []) + [old]))
            p['zone'] = new
            changes.append({'id': p['id'], 'from': old, 'to': new})
    data['roomTaxonomy'] = RULES
    return changes

def patch_js(js):
    if START in js:
        js = re.sub(re.escape(START)+r'.*?'+re.escape(END)+'\n', '', js, flags=re.S)
    block = '''  // ROOM NORMALIZATION START
  // Apply the shared floor-scoped taxonomy to legacy/imported records, too.
  const roomRules = data.roomTaxonomy || RULES_JSON;
  for (const p of data.photos) {
    const old = p.zone || '';
    const room = roomRules.photoOverrides[p.id] || roomRules.aliases[p.floor]?.[old] || old;
    if (room !== old) {
      p.originalZone ||= old;
      p.zoneAliases = [...new Set([...(p.zoneAliases || []), old])];
      p.zone = room;
    }
  }
  // ROOM NORMALIZATION END
'''.replace('RULES_JSON', json.dumps(RULES, ensure_ascii=False, separators=(',', ':')))
    assert ANCHOR in js
    js = js.replace(ANCHOR, ANCHOR+'\n'+block, 1)
    # Preserve searches for legacy room names after consolidation.
    js = js.replace('[p.id, p.zone, p.kind,', '[p.id, p.zone, p.originalZone, ...(p.zoneAliases || []), p.kind,')
    return js

def apply(source, target):
    html = pathlib.Path(source).read_text()
    m = re.search(r'(<script[^>]*id="appdata"[^>]*>)(.*?)(</script>)', html, re.S)
    assert m
    before = json.loads(m[2]); after = copy.deepcopy(before)
    changes = normalize(after)
    # Only room labels, their provenance and the shared taxonomy may change.
    assert before.keys() <= after.keys()
    for key in before:
        if key not in ('photos','roomTaxonomy'): assert before[key] == after[key], key
    for old, new in zip(before['photos'], after['photos']):
        assert {k:v for k,v in old.items() if k not in ('zone','originalZone','zoneAliases')} == {k:v for k,v in new.items() if k not in ('zone','originalZone','zoneAliases')}
    html = html[:m.start(2)] + json.dumps(after, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + html[m.end(2):]
    script = re.search(r'<script>\s*\x27use strict\x27;(.*?)</script>', html, re.S)
    assert script
    oldjs = script[0][len('<script>'):-len('</script>')]
    html = html[:script.start()]+'<script>'+patch_js(oldjs)+'</script>'+html[script.end():]
    pathlib.Path(target).write_text(html)
    source_js = pathlib.Path('releases/mobile-ui/viewer.js')
    if source_js.exists(): source_js.write_text(patch_js(source_js.read_text()))
    audit = {'taxonomyVersion': RULES['version'], 'photoCount':len(after['photos']), 'changedPhotoCount':len(changes), 'changes':changes,
             'roomsBefore':{f:sorted({p['zone'] for p in before['photos'] if p['floor']==f}) for f in ['F1','F2','EXT']},
             'roomsAfter':{f:sorted({p['zone'] for p in after['photos'] if p['floor']==f}) for f in ['F1','F2','EXT']},
             'preserved':'All image assets, photo IDs, camera/viewpoint IDs, coordinates, dates, revisions and source-render links verified unchanged.'}
    (ROOT/'QA.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['changes','roomsBefore','roomsAfter']}))
if __name__ == '__main__':
    apply(sys.argv[1],sys.argv[2])
