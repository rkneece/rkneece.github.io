import base64, concurrent.futures, json, pathlib, re, sys, urllib.request

SOURCE = 'https://www.zillow.com/homedetails/43-Cedar-Ln-Ogunquit-ME-03907/85037856_zpid/'
# Positions are provisional camera locations on the schematic, not measurements.
VIEWS = [
 (1,'e01fa4ec6e5bb7168dc2af170502526f','Front exterior','Front entrance and cathedral windows',55,83,'W'),
 (2,'da8cff0d1e09be7893ebaef274e277b2','Front exterior','Front house and driveway approach',81,85,'NW'),
 (3,'98b30c06e8fc2d0cbec5ae22012a62e9','Garage / driveway','Path beside garage toward accessory building',83,35,'W'),
 (4,'0ff4fc52edd05a646d1009c7e0cf2f13','Garage / driveway','Driveway toward accessory building and woods',91,62,'W'),
 (5,'b4ad467149fec65b369dd553bc12aa8b','Garage / driveway','Garage door and driveway side of main house',88,78,'NW'),
 (6,'21f56a8035bc4213c2435888f1c731ec','Aerial context','Aerial neighborhood and coastal context',18,18,''),
 (7,'156cc68acd0a07df3a1c78a548fa74b3','Rear deck / yard','Rear deck looking into wooded backyard',39,24,'W'),
 (24,'1395732815e80a0160d79163d481bd7c','Rear deck / yard','Rear deck and screened porch exterior',32,21,'SE'),
 (25,'885902c9569022a09d7afd23d84a6f0b','Rear deck / yard','Deck, woodland and accessory-building connection',51,24,'NW'),
 (26,'ab20185af4601912bd957fef375ae5e6','Accessory building','Accessory building entrance and small landing',79,30,'W'),
 (27,'9ea44d39de16d614eb87ddb98f1e5ec5','Accessory building','Accessory building side elevation and garden',66,13,'N'),
 (28,'c997c64fba05baa84e77ed562ef8ce4c','Accessory building','Accessory building looking back toward main house',70,8,'E'),
]

def build(src, output, cached=None):
 s=pathlib.Path(src).read_text()
 m=re.search(r'(<script[^>]*id="appdata"[^>]*>)(.*?)(</script>)',s,re.S)
 d=json.loads(m[2]); original=list(d['photos'])
 def load(v):
  n,key,*_=v
  url=f'https://photos.zillowstatic.com/fp/{key}-o_a.jpg'
  raw=pathlib.Path(cached,f'{n:02}.jpg').read_bytes() if cached else urllib.request.urlopen(url,timeout=60).read()
  assert raw[:2]==b'\xff\xd8', f'Invalid JPEG: {n}'
  return n,url,'data:image/jpeg;base64,'+base64.b64encode(raw).decode()
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: images={n:(url,data) for n,url,data in pool.map(load,VIEWS)}
 d['photos']=[p for p in d['photos'] if not p['id'].startswith('ZEXT')]
 for n,key,zone,title,x,y,facing in VIEWS:
  id=f'ZEXT{n:02}';url,data=images[n]
  p=dict(id=id,imageId=id,type='site',floor='EXT',stage='Existing',zone=zone,kind='Aerial / context' if n==6 else 'Wide / context',filename=f'Zillow_43_Cedar_{n:02}.jpg',sequence=500+n,standing='Approximate camera location inferred from listing photograph; not field verified' if n!=6 else 'Aerial overview pin; not the drone camera location',facing=facing,looking=title,notes='Source: Zillow / Maine Listings #1665821. Listing reference; capture date unknown. Camera location and bearing estimated from visible landmarks on an illustrative site diagram. '+('Aerial marker denotes context only; drone position is unknown.' if n==6 else ''),confirmed=False,mapX=x,mapY=y,viewpointId=f'EXT-ZILLOW-{n:02}',capturedAt='',milestone='Pre-renovation listing reference',sourceType='Zillow listing photograph',source='Zillow / Maine Listings #1665821',sourceUrl=SOURCE,originalImageUrl=url,designVersion='',variant='',approval='Reference',geometryStatus='Actual listing photograph; provisional camera placement',mapLocationType='Estimated exterior camera position',mapPlacementConfidence='Low' if n in [6,7,24,25,27,28] else 'Medium')
  d['photos'].append(p);d['photoImages'][id]=data
 # Keep the existing schematic and confirmed camera coordinates intact. Add
 # clearly provisional outlines in its previously blank rear-yard space.
 old=d['plans']['EXT']
 if d.get('zillowExteriorRevision'):old=d['zillowExteriorRevision']['originalExteriorPlan']
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="670" viewBox="0 0 900 670"><image href="{old}" width="900" height="670"/>
 <rect x="70" y="18" width="760" height="197" rx="10" fill="#eff5f3"/>
 <text x="90" y="46" font-family="Arial" font-size="21" fill="#285060">EXTERIOR CAMERA REFERENCE · ESTIMATED</text>
 <text x="90" y="70" font-family="Arial" font-size="14" fill="#526967">Illustrative only. Rear structures, camera positions and bearings are provisional.</text>
 <rect x="646" y="84" width="125" height="83" fill="#dae8e8" stroke="#497386" stroke-width="3" stroke-dasharray="7 5"/>
 <text x="659" y="119" font-family="Arial" font-size="15" fill="#285060">ACCESSORY</text><text x="659" y="140" font-family="Arial" font-size="15" fill="#285060">BUILDING</text>
 <rect x="354" y="176" width="140" height="44" fill="#e0e9de" stroke="#74926f" stroke-width="2" stroke-dasharray="6 4"/><text x="374" y="203" font-family="Arial" font-size="15">REAR PORCH</text>
 <path d="M320 175V133H525V220" fill="none" stroke="#9f8b6a" stroke-width="3" stroke-dasharray="6 4"/><text x="368" y="157" font-family="Arial" font-size="14" fill="#715e40">DECK / YARD</text>
 <rect x="80" y="544" width="740" height="84" fill="#eff5f3"/><text x="95" y="572" font-family="Arial" font-size="15" fill="#355967">Click a pin to see a photo. Zillow pins are estimated; original site pins are retained.</text><text x="95" y="598" font-family="Arial" font-size="15" fill="#355967">Schematic orientation: rear / west ↑ · driveway / north → · front / east ↓</text></svg>'''
 d['plans']['EXT']='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
 d['zillowExteriorRevision']=dict(version='zillow-exterior-2026-10-22',sourceUrl=SOURCE,photoIds=[f'ZEXT{v[0]:02}' for v in VIEWS],originalExteriorPlan=old,placement='Provisional camera estimates, not surveyed. Aerial pin is context only.')
 # Avoid a false confirmation message and use exterior-specific navigation text.
 s=s[:m.start(2)]+json.dumps(d,separators=(',',':')).replace('</','<\\/')+s[m.end(2):]
 s=s.replace("p.standing||'Location confirmed on map'", "p.standing||(p.confirmed?'Location confirmed on map':'Approximate location; unverified')")
 s=s.replace("$('mapSub').textContent=proposed?", "$('mapSub').textContent=floor==='EXT'?'Zillow camera pins and dashed rear structures are approximate. Click a pin to open the listing photo; nearby pins may cycle through multiple views.':proposed?")
 s=s.replace("$('mapFoot').textContent=proposed&&floor==='F2'?", "$('mapFoot').textContent=floor==='EXT'?'Illustrative site reference, not a survey. Rear / west is up; driveway / north is right. Aerial pin is an overview, not the drone location.':proposed&&floor==='F2'?")
 assert all(p in d['photos'] for p in original if not p['id'].startswith('ZEXT'))
 assert len({p['id'] for p in d['photos']})==len(d['photos'])
 pathlib.Path(output).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(output).write_text(s)
 print('Added 12 listing exterior photos; preserved all prior photo records.')

if __name__=='__main__':build(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None)
