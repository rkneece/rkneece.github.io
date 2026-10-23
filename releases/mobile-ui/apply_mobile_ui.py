"""Assemble the mobile viewer around the current, byte-preserved embedded data.

Run against the latest development checkout, never an older release HTML. This
changes only the presentation shell; photos, IDs, mappings, provenance and image
payloads are not rewritten. No third-party runtime or online dependency is added.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
DATA = re.compile(r'<script id="appdata" type="application/json">(.*?)</script>', re.S)


def assemble(source, output):
    before = source.read_text()
    matches = DATA.findall(before)
    if len(matches) != 1:
        raise ValueError('Expected exactly one embedded appdata record')
    payload = matches[0]
    data = json.loads(payload)
    ids = [p['id'] for p in data['photos']]
    if len(ids) != len(set(ids)):
        raise ValueError('Photo IDs must be unique')
    css = (ROOT / 'viewer.css').read_text()
    js = (ROOT / 'viewer.js').read_text()
    shell = (ROOT / 'shell.html').read_text()
    result = shell.replace('/* CEDAR_UI_CSS */', css).replace('/* CEDAR_UI_JS */', js).replace('/* CEDAR_APPDATA */', payload)
    assert DATA.search(result).group(1) == payload, 'Embedded data must be byte-preserved'
    assert len(re.findall(r'<script', result)) == 2, 'Unexpected script injection'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result)
    report = {
        'ui': 'mobile-v1',
        'input_sha256': hashlib.sha256(before.encode()).hexdigest(),
        'output_sha256': hashlib.sha256(result.encode()).hexdigest(),
        'appdata_sha256': hashlib.sha256(payload.encode()).hexdigest(),
        'embedded_data_byte_preserved': True,
        'photo_count': len(ids),
        'photo_ids_sha256': hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
        'all_images_and_mappings_preserved': True,
        'external_runtime_dependencies': 0,
    }
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', nargs='?', default='sites/43cedar/interactive_map/index.html')
    parser.add_argument('--output')
    parser.add_argument('--report', default=str(ROOT / 'ASSEMBLY_QA.json'))
    args = parser.parse_args()
    source = Path(args.source)
    report = assemble(source, Path(args.output) if args.output else source)
    Path(args.report).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
