"""Build the approved Oct–Nov viewer release from local files."""

import argparse
import base64
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from zipfile import ZipFile

from PIL import Image


APP_DATA = re.compile(r'(<script[^>]*id="appdata"[^>]*>)(.*?)(</script>)', re.S)
FLOOR_LIST = "['F2', 'Floor 2'], ['EXT', 'Exterior']"
IMAGE_FIELDS = (
    'photoImages', 'blenderImages', 'photorealImages', 'resourceImages',
    'plans', 'proposedPlans', 'zillowExteriorRevision',
)
IMAGE_SUFFIXES = {'jpeg': 'jpg', 'png': 'png', 'webp': 'webp', 'svg+xml': 'svg'}
ASSET_DIR = 'assets/content'


def labeler_value(source, name):
    declaration = re.search(rf'\bconst\s+{name}\s*=\s*', source)
    if declaration is None:
        raise ValueError(f'Missing labeler declaration: {name}')
    return json.JSONDecoder().raw_decode(source, declaration.end())[0]


def externalize(data, output, asset_base):
    manifest = {}
    for field in IMAGE_FIELDS:
        for key, value in data.get(field, {}).items():
            if not isinstance(value, str) or not value.startswith('data:image/'):
                continue
            header, encoded = value.split(',', 1)
            mime = header.removeprefix('data:image/').removesuffix(';base64')
            if mime not in IMAGE_SUFFIXES or header != f'data:image/{mime};base64':
                raise ValueError(f'Unsupported image format at {field}/{key}')
            raw = base64.b64decode(encoded, validate=True)
            digest = sha256(raw).hexdigest()
            name = f'{digest}.{IMAGE_SUFFIXES[mime]}'
            path = output / ASSET_DIR / name
            if not path.exists():
                path.write_bytes(raw)
            if sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Asset content mismatch: {path}')
            data[field][key] = f'{asset_base}{ASSET_DIR}/{name}'
            manifest[name] = {'bytes': len(raw), 'sha256': digest, 'type': f'image/{mime}'}
    return manifest


def check_batch(photos, images, originals):
    counts = Counter(p['stage'] for p in photos)
    if counts != {'Demo': 49, 'Existing': 14}:
        raise ValueError(f'Unexpected approved stages: {counts}')
    if Counter(p['floor'] for p in photos) != {'EXT': 35, 'F1': 15, 'ADU': 13}:
        raise ValueError('Unexpected approved areas')
    if len({p['id'] for p in photos}) != 63 or {p['id'] for p in photos} != images.keys():
        raise ValueError('Approved IDs and labeler image IDs do not match')
    with ZipFile(originals) as archive:
        members = [entry for entry in archive.infolist() if not entry.is_dir()]
        filenames = Counter(Path(entry.filename).name for entry in members)
        if filenames != Counter(p['filename'] for p in photos):
            raise ValueError('ZIP members and approved filenames do not match')
        damaged = archive.testzip()
        if damaged:
            raise ValueError(f'ZIP member failed integrity check: {damaged}')
    for photo in photos:
        if not (photo['confirmed'] and photo['facing'] and
                0 <= photo['mapX'] <= 100 and 0 <= photo['mapY'] <= 100):
            raise ValueError(f'Unconfirmed camera mapping: {photo["id"]}')
        image = images[photo['id']]
        if not image.startswith('data:image/jpeg;base64,'):
            raise ValueError(f'Expected a JPEG display copy for {photo["id"]}')
        with Image.open(BytesIO(base64.b64decode(image.split(',', 1)[1], validate=True))) as display:
            if display.format != 'JPEG' or display.getexif():
                raise ValueError(f'Unexpected display image format or metadata: {photo["id"]}')
            display.verify()


def build(args):
    source = args.baseline.read_bytes().decode('utf-8')
    match = APP_DATA.search(source)
    if match is None or source.count(FLOOR_LIST) != 1:
        raise ValueError('Viewer structure changed; inspect the current baseline')
    data = json.loads(match[2])
    labeler = args.labeler.read_text(encoding='utf-8')
    images = labeler_value(labeler, 'IMAGES')
    adu_plan = labeler_value(labeler, 'PLANS')['ADU']
    photos = json.loads(args.labels.read_bytes())['photos']
    check_batch(photos, images, args.originals)

    if {p['id'] for p in data['photos']} & images.keys() or 'ADU' in data['plans']:
        raise ValueError('Baseline already contains release data')
    existing_count = len(data['photos'])
    for photo in photos:
        data['photos'].append(dict(photo, type='site', imageId=photo['id'],
                                   source='October–November 2026 site photos',
                                   geometryStatus='Actual site photograph'))
    data['photoImages'].update(images)
    data['plans']['ADU'] = adu_plan
    data['counts'] = Counter(f'{p["floor"]}|{p["stage"]}' for p in data['photos'])
    data['buildId'] += '__Site_202610_11'

    (args.output / ASSET_DIR).mkdir(parents=True, exist_ok=True)
    manifest = externalize(data, args.output, args.asset_base)
    payload = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    viewer = (source[:match.start(2)] + payload + source[match.end(2):]).replace(
        FLOOR_LIST, FLOOR_LIST + ", ['ADU', 'Accessory Unit']", 1)
    (args.output / 'index.html').write_bytes(viewer.encode('utf-8'))
    (args.output / 'external-media.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'existing_records': existing_count, 'added_records': len(photos),
                      'viewer_bytes': len(viewer.encode('utf-8')),
                      'external_assets': len(manifest),
                      'viewer_sha256': sha256(viewer.encode('utf-8')).hexdigest()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('baseline', 'labels', 'labeler', 'originals', 'output'):
        parser.add_argument(f'--{argument}', required=True, type=Path)
    parser.add_argument('--asset-base', default='', help='Optional HTTPS origin and path for extracted assets')
    args = parser.parse_args()
    if args.asset_base:
        url = urlsplit(args.asset_base)
        if url.scheme != 'https' or not url.hostname or url.username or url.query or url.fragment:
            parser.error('--asset-base must be an HTTPS URL with no credentials, query or fragment')
        args.asset_base = args.asset_base.rstrip('/') + '/'
    build(args)


if __name__ == '__main__':
    main()
