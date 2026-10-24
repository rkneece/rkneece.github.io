"""Publish the approved RES01 replacement only, with a guarded live-map patch."""
import base64, copy, datetime, hashlib, json, os, re, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PATTERN=re.compile(r'(<script id="appdata" type="application/json">)(.*?)(</script>)',re.S)

def patch(raw, image, updated_at):
    text=raw.decode('utf-8');match=PATTERN.search(text);assert match
    before=json.loads(match[2]);after=copy.deepcopy(before)
    row=next(x for x in after['photos'] if x['id']=='RES01')
    previous=copy.deepcopy(row)
    after['resourceImages']['RES01']='data:image/png;base64,'+base64.b64encode(image).decode()
    row.update(filename='43_Cedar_Fireplace_Measured_Concept.png',
        source='Measured fireplace concept elevation · updated October 23, 2026',
        referenceStatus='152-inch total field confirmed; remaining dimensions provisional',
        designVersion='FF6 · measured 152-inch alcove / 75-inch TV',
        notes='152-inch field-measured total width. Proposed 40/72/40-inch bays; 75-inch TV (approximately 65.4 x 36.8 inches). All-white stepped BPR-inspired mantel and recessed reclaimed brick. Tall privacy-window unit targets approximately 24 x 48 inches; final manufacturer catalog size and rough openings TBD. Matching benches with four drawers each (2 x 2); 18-inch seat height provisional. Retain vertical tongue and groove across the entire fireplace/south wall and alcoves, painted Benjamin Moore Swiss Coffee at 75% strength, eggshell. Installation heights, appliance clearances and all remaining dimensions require final coordination.',
        publishedAt=row.get('publishedAt','2026-10-22T21:49:50Z'),updatedAt=updated_at)
    restored=copy.deepcopy(after)
    restored['resourceImages']['RES01']=before['resourceImages']['RES01']
    restored['photos'][next(i for i,x in enumerate(restored['photos']) if x['id']=='RES01')]=previous
    assert restored==before,'Attempted change outside RES01'
    payload=json.dumps(after,separators=(',',':')).replace('</','<\\/')
    result=text[:match.start(2)]+payload+text[match.end(2):]
    check=json.loads(PATTERN.search(result)[2]);assert check==after
    return result.encode('utf-8')

def main():
    release=json.loads((ROOT/'PUBLISH_READY.json').read_text())
    image=(ROOT/'43_Cedar_Fireplace_Measured_Concept.png').read_bytes()
    assert hashlib.sha256(image).hexdigest()==release['image_sha256']
    path=Path('sites/43cedar/interactive_map/index.html')
    raw=path.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==release['base_blob_sha']
    output=patch(raw,image,datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'))
    path.write_bytes(output)
    print('RES01-only patch verified. Every other record, image, plan and UI unchanged.')

if __name__=='__main__':main()
