"""Create an asset-separated QA copy, keeping the actual single-file build intact.

The managed preview proxy times out transferring the 33 MB production document.
This fixture uses the exact viewer code, records and image bytes, with image data
URLs extracted to local files solely for browser QA. Never publish this fixture.
"""
import base64
import json
from pathlib import Path
import re
import sys
import urllib.request

root = Path(sys.argv[1])
source = (root / 'index.html').read_text()
match = re.search(r'<script id="appdata" type="application/json">(.*?)</script>', source, re.S)
assets = root / 'qa-assets'
assets.mkdir(exist_ok=True)
counter = 0


def extract(value):
    global counter
    if isinstance(value, dict):
        return {key: extract(item) for key, item in value.items()}
    if isinstance(value, list):
        return [extract(item) for item in value]
    if isinstance(value, str) and value.startswith('data:image/'):
        counter += 1
        header, payload = value.split(',', 1)
        name = f'image-{counter}.png' if 'png' in header else f'image-{counter}.jpg'
        (assets / name).write_bytes(base64.b64decode(payload))
        return '/qa-assets/' + name
    return value


original = json.loads(match.group(1))
data = extract(original)
# Exercise the real embedded-data-to-Blob path as well as extracted images.
sample = next(p for p in original['photos'] if p['type'] == 'site')
data['photoImages'][sample['imageId']] = original['photoImages'][sample['imageId']]
# Recent releases also use existing relative JPEG files. Keep those paths in
# the QA copy and fetch the exact published bytes without changing the data.
for key in ['photoImages', 'blenderImages', 'photorealImages', 'resourceImages']:
    for value in original.get(key, {}).values():
        if isinstance(value, str) and value.startswith('assets/'):
            target = root / value
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve('https://richkneece.com/sites/43cedar/interactive_map/' + value, target)
(root / 'qa.html').write_text(source[:match.start(1)] + json.dumps(data, separators=(',', ':')) + source[match.end(1):])
for width, height, name in [(390, 844, 'phone'), (320, 740, 'small'), (844, 390, 'landscape'), (820, 1000, 'tablet')]:
    (root / f'qa-{name}.html').write_text(f'''<!doctype html><html><head><title>43 Cedar {name} QA</title><style>body{{margin:0;background:#d8e2e6;font:14px system-ui;padding:18px}}h1{{font-size:16px;margin:0 0 14px}}iframe{{width:{width}px;height:{height}px;border:0;box-shadow:0 2px 20px #1234;border-radius:14px;background:#fff}}</style></head><body><h1>43 Cedar · {name.title()} layout · {width} × {height}</h1><iframe id="phone" title="Responsive preview" src="/qa.html"></iframe></body></html>''')
print(f'Prepared {counter} identical image assets and four responsive QA fixtures')
