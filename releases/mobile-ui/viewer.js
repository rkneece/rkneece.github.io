'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const data = JSON.parse($('appdata').textContent);
  // ROOM NORMALIZATION START
  // Apply the shared floor-scoped taxonomy to legacy/imported records, too.
  const roomRules = data.roomTaxonomy || {"version":"rooms-2","aliases":{"F1":{"Porch-side bedroom":"Bedroom 1","North bedroom / closets":"Bedroom 2","North bedroom":"Bedroom 2","Fireplace / living room":"Living room","Pink shower bathroom":"Bedroom 1 Bath","Hall / tiled bathroom":"Hall bathroom","Hall / closet details":"Downstairs Hallway","Hall / kitchen approach":"Downstairs Hallway","Foyer / stairs":"Foyer / Stairs","Entrance hallway":"Foyer / Stairs","First-floor layout":"Whole first floor","Primary bathroom":"Bedroom 1 Bath","Entry / stairs":"Foyer / Stairs","Trim / staircase details":"Foyer / Stairs","Dining area":"Dining Area","Kitchen":"Dining Area","Kitchen / dining structure":"Dining Area","Laundry closet":"Downstairs Hallway","Bedroom hallway":"Downstairs Hallway"}},"photoOverrides":{"C037":"Downstairs Hallway","C038":"Downstairs Hallway","C039":"Downstairs Hallway","C045":"Downstairs Hallway","C046":"Downstairs Hallway","C047":"Downstairs Hallway","C048":"Downstairs Hallway","C049":"Downstairs Hallway","D20261023-125206":"Downstairs Hallway"}};
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


  const byId = new Map(data.photos.map(p => [p.id, p]));
  const mobile = matchMedia('(max-width:1100px)');
  const floors = [['F1', 'Floor 1'], ['F2', 'Floor 2'], ['EXT', 'Exterior']];
  const stages = ['Existing', 'Demo', 'Proposed · Layout', 'Proposed · Render', 'Proposed · Photoreal', 'Proposed · Resources', 'Build', 'Completed'];
  const bearings = {N:0, NE:45, E:90, SE:135, S:180, SW:225, W:270, NW:315};
  const state = {floor:'F1', stage:location.hash === '#proposed-resources' ? 'Proposed · Resources' : 'Existing', room:'', kind:'', revision:'', query:'', selected:'C020', mode:'gallery'};
  let selectedMarker = [], galleryScroll = 0, dialogScroll = 0, overlay = null, afterClose = null;
  let photoIds = [], photoId = '', sourceStack = [], mapPlanKey = '', clusterSignature = '';
  const mapViews = new Map();
  const isRender = p => p.type === 'blender' || p.type === 'photoreal';
  const isResources = () => state.stage === 'Proposed · Resources';
  const floorName = id => floors.find(f => f[0] === id)?.[1] || id;
  const imageURLs = new Map();
  const imageFor = p => {
    const key=p.type+':'+p.imageId;
    if(imageURLs.has(key))return imageURLs.get(key);
    const value=(p.type === 'resource' ? data.resourceImages : p.type === 'photoreal' ? data.photorealImages : p.type === 'blender' ? data.blenderImages : data.photoImages)?.[p.imageId];
    if(!value?.startsWith('data:image/'))return value;
    // Keep the portable payload embedded once, rather than repeating large Base64
    // strings in every thumbnail, map preview, selected photo and dialog element.
    const comma=value.indexOf(','), mime=value.slice(5,value.indexOf(';'));
    const bytes=Uint8Array.from(atob(value.slice(comma+1)),c=>c.charCodeAt(0));
    const url=URL.createObjectURL(new Blob([bytes],{type:mime}));imageURLs.set(key,url);return url;
  };
  const stageName = s => s === 'Build' ? 'In Progress · Build' : s;
  const values = (list, field) => [...new Set(list.map(p => p[field]).filter(Boolean))].sort();
  const photosFor = (change = {}) => {
    const s = {...state, ...change};
    const q = s.query.trim().toLowerCase();
    return data.photos.filter(p => p.floor === s.floor && p.stage === s.stage && (!s.room || p.zone === s.room) && (!s.kind || p.kind === s.kind) && (!s.revision || p.designVersion === s.revision) && (!q || [p.id, p.zone, p.originalZone, ...(p.zoneAliases || []), p.kind, p.looking, p.notes, p.filename, p.viewpointId, p.designVersion].join(' ').toLowerCase().includes(q)));
  };
  const active = () => data.photos.filter(p => p.floor === state.floor && p.stage === state.stage);
  const makeButton = (label, action, cls = '') => {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.className = cls; b.onclick = action; return b;
  };
  function setImage(img, p) {
    const src = imageFor(p) || '';
    if (img.getAttribute('src') !== src) img.src = src;
    img.alt = p.looking || p.zone || p.id;
  }
  function options(select, list, selected, label) {
    select.replaceChildren(new Option(label, ''), ...list.map(v => new Option(v, v)));
    if (selected && !list.includes(selected)) select.add(new Option(selected + ' (no matches)', selected));
    select.value = selected;
  }
  function syncControls() {
    $('floorCrumb').textContent = floorName(state.floor);
    $('roomCrumb').textContent = state.room || 'All rooms';
    $('stageCrumb').textContent = stageName(state.stage);
    const n = [state.kind, state.revision, state.query.trim()].filter(Boolean).length;
    $('filterBadge').hidden = !n; $('filterBadge').textContent = n;
    $('filterButton').setAttribute('aria-label', 'More filters' + (n ? ', ' + n + ' active' : ''));
    $('galleryMode').setAttribute('aria-pressed', state.mode === 'gallery');
    $('mapMode').setAttribute('aria-pressed', state.mode === 'map');
    $('mapMode').disabled = isResources();
    $('mapMode').title = isResources() ? 'Reference diagrams are available in Gallery' : 'Browse on the floor plan';
    $('floorButtons').replaceChildren(...floors.map(([id, name]) => makeButton(name, () => changeContext({floor:id}), state.floor === id ? 'active' : '')));
    $('stages').replaceChildren(...stages.map(s => makeButton(stageName(s), () => changeContext({stage:s}), state.stage === s ? 'active' : '')));
    options($('zone'), values(data.photos.filter(p => p.floor === state.floor), 'zone'), state.room, 'All rooms');
    options($('kind'), values(active(), 'kind'), state.kind, 'All types');
    options($('revision'), values(active(), 'designVersion'), state.revision, 'All revisions');
    if ($('q').value !== state.query) $('q').value = state.query;
    document.body.dataset.mode = state.mode;
    document.body.classList.toggle('resources-mode', isResources());
    document.body.classList.toggle('layout-stage', state.stage === 'Proposed · Layout');
  }
  function changeContext(change) {
    const oldMapKey = planKey();
    Object.assign(state, change);
    if ('floor' in change && state.room && !data.photos.some(p => p.floor === state.floor && p.zone === state.room)) state.room = '';
    if ('floor' in change || 'stage' in change) {
      const list = active();
      if (state.kind && !list.some(p => p.kind === state.kind)) state.kind = '';
      if (state.revision && !list.some(p => p.designVersion === state.revision)) state.revision = '';
      // Keep a selected room even when a category has no photos for it; show an honest empty state.
    }
    if (isResources()) state.mode = 'gallery';
    selectedMarker = [];
    if (oldMapKey !== planKey()) clusterSignature = '';
    history.replaceState(history.state, '', state.stage === 'Proposed · Resources' ? '#proposed-resources' : location.pathname + location.search);
    render();
  }
  function chooseMode(mode) {
    if (mode === 'map' && isResources()) return;
    if (state.mode === mode) return;
    if (state.mode === 'gallery') galleryScroll = scrollY;
    state.mode = mode;
    syncControls();
    if (mode === 'map') {
      if (mobile.matches) scrollTo({top:document.querySelector('.mobile-toolbar').offsetTop, behavior:'instant'});
      requestAnimationFrame(() => { mapSurface.resize(); drawMap(); });
    } else {
      requestAnimationFrame(() => scrollTo({top:galleryScroll, behavior:'instant'}));
    }
  }
  function renderGallery(list) {
    const box = $('gallery'); box.replaceChildren();
    $('results').textContent = list.length + (list.length === 1 ? ' photo' : ' photos');
    $('catalogTitle').textContent = isResources() ? 'Proposed resources' : state.room || 'Photo gallery';
    $('catalogSub').textContent = isResources() ? 'Diagrams & references · tap to inspect' : stageName(state.stage) + ' · tap to open';
    if (!list.length) {
      const message = document.createElement('div'); message.className = 'emptymsg';
      message.textContent = state.stage === 'Proposed · Layout' ? 'Layout guidance is shown above. Use Map to explore available proposed views.' : 'No photos match this selection. Try another room or category, or clear the filters.';
      if (state.room || state.kind || state.revision || state.query) message.append(makeButton('Show all rooms · clear filters', () => changeContext({room:'', kind:'', revision:'', query:''})));
      box.append(message); return;
    }
    for (const p of list) {
      const tile = makeButton('', () => { selectPhoto(p.id, false); openPhoto(p.id, list.map(p => p.id)); }, 'tile' + (p.id === state.selected ? ' selected' : ''));
      tile.dataset.photoId = p.id;
      tile.setAttribute('aria-label', p.id + ' · ' + (p.looking || p.zone) + ' · open photo');
      const img = document.createElement('img'); img.loading = 'lazy'; img.decoding = 'async'; setImage(img, p);
      const id = document.createElement('span'); id.className = 'tile-id'; id.textContent = p.id;
      const copy = document.createElement('div'); copy.className = 'tile-copy';
      const title = document.createElement('b'); title.textContent = p.looking || p.zone;
      const meta = document.createElement('span'); meta.className = 'tile-meta'; meta.textContent = p.designVersion || p.zone || p.filename;
      copy.append(title, meta); tile.append(img, id, copy); box.append(tile);
    }
  }
  function detailsFor(p, container, linked) {
    container.replaceChildren();
    const dl = document.createElement('dl');
    const entries = [
      ['File / ID', [p.id, p.filename].filter(Boolean).join(' · ')],
      ['Location / viewpoint', [floorName(p.floor), p.zone, p.standing, p.viewpointId, p.facing].filter(Boolean).join(' · ')],
      ['Design revision', p.designVersion],
      ['Source', [p.source, p.sourceType, p.geometryStatus, p.referenceStatus].filter(Boolean).join(' · ')],
      ['Notes / provenance', p.notes],
      ['Review status', [p.approval, p.qaStatus].filter(Boolean).join(' · ')],
      ['Map position', p.type === 'resource' ? 'Reference diagram; no camera marker.' : coordinates(p) ? (p.proposedMapLocationType || p.mapLocationType || (p.confirmed ? 'Photo location confirmed in labeler.' : 'Camera position is approximate.')) : 'This view has no registered camera position.'],
      ['Geometry reference', p.type === 'photoreal' ? 'AI photographic finish study. Use the native source render for architectural geometry; materials and fine details can vary.' : isRender(p) ? 'Native Blender view. Design assumptions and dimensions retain their stated limits.' : '']
    ];
    for (const [label, value] of entries) if (value) { const dt = document.createElement('dt'); dt.textContent = label; const dd = document.createElement('dd'); dd.textContent = value; dl.append(dt, dd); }
    container.append(dl);
    const links = document.createElement('div'); links.className = 'related';
    if (p.sourceRenderId && byId.has(p.sourceRenderId)) links.append(makeButton('Source render ' + p.sourceRenderId, () => linked(p.sourceRenderId)));
    for (const id of p.relatedPhotos || []) if (byId.has(id)) links.append(makeButton('Existing view ' + id, () => linked(id)));
    if (links.childElementCount) container.append(links);
  }
  function selectPhoto(id, redrawMap = true) {
    const p = byId.get(id); if (!p) return;
    const old = $('gallery').querySelector('.selected'); if (old) old.classList.remove('selected');
    state.selected = id;
    const tile = [...$('gallery').children].find(b => b.dataset.photoId === id); tile?.classList.add('selected');
    $('caption').textContent = p.looking || p.zone;
    $('selectedSubtitle').textContent = p.id + ' · ' + floorName(p.floor) + ' · ' + p.zone;
    $('status').textContent = p.type === 'photoreal' ? 'AI photoreal' : p.type === 'blender' ? 'Blender render' : p.type === 'resource' ? 'Reference' : p.stage;
    setImage($('hero'), p);
    detailsFor(p, $('desktopDetails'), id => openPhoto(id, [id]));
    const list = photosFor(), index = list.findIndex(p => p.id === id);
    $('counter').textContent = (index + 1) + ' / ' + list.length;
    $('prev').disabled = index <= 0; $('next').disabled = index < 0 || index >= list.length - 1;
    if (redrawMap) drawMap();
  }
  function render() {
    syncControls();
    const list = photosFor();
    if (!list.some(p => p.id === state.selected)) state.selected = list[0]?.id || '';
    $('viewer').hidden = !list.length || state.stage === 'Proposed · Layout';
    $('emptyStage').hidden = !!list.length || state.stage === 'Proposed · Layout';
    $('emptyText').textContent = 'Choose another room or category, or clear the active filters.';
    $('layoutNotes').hidden = state.stage !== 'Proposed · Layout';
    if (state.stage === 'Proposed · Layout') {
      $('notesList').replaceChildren();
      for (const item of (state.floor === 'F1' ? data.proposalNotes : data.floorProposalNotes?.[state.floor]) || []) {
        const note = document.createElement('div'); note.className = 'note';
        const title = document.createElement('b'); title.textContent = item.area;
        const p = document.createElement('p'); p.textContent = item.detail; note.append(title, p); $('notesList').append(note);
      }
    }
    renderGallery(list);
    if (list.length) selectPhoto(state.selected, false);
    drawMap();
  }

  // A single overlay history entry lets Android/browser Back dismiss the active surface.
  // Photo changes and source comparisons stay inside that entry and leave gallery filters untouched.
  function lockScroll() {
    dialogScroll = scrollY; document.body.style.top = -dialogScroll + 'px'; document.body.classList.add('overlay-open');
  }
  function unlockScroll() {
    document.body.classList.remove('overlay-open'); document.body.style.top = ''; scrollTo({top:dialogScroll, behavior:'instant'});
  }
  function present(kind) {
    if (overlay) return;
    overlay = kind; lockScroll(); history.pushState({...history.state, cedarOverlay:kind}, '');
    (kind === 'photo' ? $('photoDialog') : $('filterSheet')).showModal();
  }
  function dismiss(callback) {
    afterClose = callback || null;
    if (history.state?.cedarOverlay && overlay) history.back(); else finishDismiss();
  }
  function finishDismiss() {
    if (!overlay) return;
    const dialog = overlay === 'photo' ? $('photoDialog') : $('filterSheet');
    overlay = null; dialog.close(); unlockScroll();
    const callback = afterClose; afterClose = null; if (callback) callback();
  }
  addEventListener('popstate', () => {
    if (overlay) finishDismiss();
    // A forward navigation to a retired overlay entry should not trap the next Back press.
    if (history.state?.cedarOverlay) { const s = {...history.state}; delete s.cedarOverlay; history.replaceState(s, ''); }
  });
  for (const id of ['photoDialog', 'filterSheet']) {
    $(id).addEventListener('cancel', e => { e.preventDefault(); dismiss(); });
    $(id).addEventListener('click', e => { if (e.target === $(id)) { const r = $(id).getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dismiss(); } });
  }
  function chooser(type) {
    $('sheetContent').replaceChildren(); $('sheetFooter').hidden = true;
    const copy = document.createElement('p'); copy.className = 'sheet-copy';
    let choices, current;
    if (type === 'floor') {
      $('sheetTitle').textContent = 'Choose a floor'; current = state.floor;
      copy.textContent = 'Your room stays selected when it exists on the chosen floor. Counts reflect the current category.';
      choices = floors.map(([value, label]) => ({value, label, count:photosFor({floor:value, room:'', kind:'', revision:'', query:''}).length}));
    } else if (type === 'room') {
      $('sheetTitle').textContent = 'Choose a room'; current = state.room;
      copy.textContent = floorName(state.floor) + ' · ' + stageName(state.stage);
      choices = ['', ...values(data.photos.filter(p => p.floor === state.floor), 'zone')].map(value => ({value, label:value || 'All rooms', count:photosFor({room:value, kind:'', revision:'', query:''}).length}));
    } else {
      $('sheetTitle').textContent = 'Choose what to view'; current = state.stage;
      copy.textContent = floorName(state.floor) + ' · ' + (state.room || 'All rooms') + '. Counts reflect this location.';
      choices = stages.map(value => ({value, label:stageName(value), count:photosFor({stage:value, kind:'', revision:'', query:''}).length}));
    }
    $('sheetContent').append(copy);
    for (const c of choices) {
      const b = makeButton('', () => dismiss(() => changeContext({[type === 'floor' ? 'floor' : type === 'room' ? 'room' : 'stage']:c.value})), 'chooser-option');
      b.setAttribute('aria-pressed', current === c.value);
      const name = document.createElement('span'); name.textContent = c.label;
      const count = document.createElement('span'); count.className = 'choice-count'; count.textContent = (current === c.value ? '✓  ' : '') + c.count + (c.value === 'Proposed · Layout' ? ' photos · notes' : ' photos');
      b.append(name, count); $('sheetContent').append(b);
    }
    present('sheet');
  }
  function advancedFilters() {
    $('sheetTitle').textContent = 'Filter photos'; $('sheetContent').replaceChildren(); $('sheetFooter').hidden = false;
    const copy = document.createElement('p'); copy.className = 'sheet-copy'; copy.textContent = floorName(state.floor) + ' · ' + (state.room || 'All rooms') + ' · ' + stageName(state.stage); $('sheetContent').append(copy);
    for (const [key, label, field, all] of [['query','Search photos',null,null], ['kind','Image type','kind','All types'], ['revision','Design / render revision','designVersion','All revisions']]) {
      const l = document.createElement('label'); l.textContent = label;
      const control = document.createElement(field ? 'select' : 'input'); control.id = 'sheet-' + key;
      if (field) options(control, values(active(), field), state[key], all);
      else { control.type = 'search'; control.placeholder = 'Room, photo ID, viewpoint, notes…'; control.value = state[key]; }
      l.append(control); $('sheetContent').append(l);
    }
    $('clearAdvanced').onclick = () => { for (const key of ['kind', 'revision', 'query']) $('sheet-' + key).value = ''; };
    $('applyFilters').onclick = () => { const change = Object.fromEntries(['kind', 'revision', 'query'].map(key => [key, $('sheet-' + key).value])); dismiss(() => changeContext(change)); };
    present('sheet');
  }

  class PanZoom {
    constructor(viewport, content, {change = () => {}, swipe = null, max = 6} = {}) {
      this.el = viewport; this.content = content; this.changed = change; this.swipe = swipe; this.max = max;
      this.s = 1; this.x = 0; this.y = 0; this.w = 0; this.h = 0; this.ratio = 1; this.ready = false; this.pointers = new Map(); this.lastTap = 0;
      viewport.addEventListener('pointerdown', e => this.down(e));
      viewport.addEventListener('pointermove', e => this.move(e));
      viewport.addEventListener('pointerup', e => this.up(e));
      viewport.addEventListener('pointercancel', () => { this.pointers.clear(); this.start = null; });
      viewport.addEventListener('wheel', e => { if (!this.ready) return; e.preventDefault(); const r = viewport.getBoundingClientRect(); this.zoom(e.deltaY < 0 ? 1.15 : 1/1.15, e.clientX-r.left, e.clientY-r.top); }, {passive:false});
      new ResizeObserver(() => this.resize()).observe(viewport);
    }
    load(ratio, restored) {
      this.ratio = ratio || 1; this.ready = true;
      this.s = restored?.s || 1; this.cx = restored?.cx ?? .5; this.cy = restored?.cy ?? .5;
      this.w = 0; this.h = 0; this.resize();
    }
    snapshot() {
      return {s:this.s, cx:this.w ? (this.el.clientWidth/2-this.x)/(this.w*this.s) : .5, cy:this.h ? (this.el.clientHeight/2-this.y)/(this.h*this.s) : .5};
    }
    resize() {
      const vw = this.el.clientWidth, vh = this.el.clientHeight;
      if (!this.ready || !vw || !vh) return;
      const old = this.w ? this.snapshot() : {s:this.s, cx:this.cx ?? .5, cy:this.cy ?? .5};
      const pad = this.swipe ? 0 : 18;
      this.w = Math.min(vw-pad*2, (vh-pad*2)*this.ratio); this.h = this.w/this.ratio;
      this.x = vw/2-old.cx*this.w*this.s; this.y = vh/2-old.cy*this.h*this.s;
      this.paint();
    }
    fit() { this.s = 1; this.x = (this.el.clientWidth-this.w)/2; this.y = (this.el.clientHeight-this.h)/2; this.paint(); }
    paint() {
      if (!this.ready || !this.w) return;
      const vw=this.el.clientWidth, vh=this.el.clientHeight, sw=this.w*this.s, sh=this.h*this.s;
      this.x = sw <= vw ? (vw-sw)/2 : Math.max(vw-sw-18, Math.min(18, this.x));
      this.y = sh <= vh ? (vh-sh)/2 : Math.max(vh-sh-18, Math.min(18, this.y));
      this.content.style.width = this.w+'px'; this.content.style.height = this.h+'px';
      this.content.style.transform = `translate(${this.x}px,${this.y}px) scale(${this.s})`;
      this.content.style.setProperty('--pin-scale', 1/this.s);
      this.changed(this);
    }
    zoom(factor, x=this.el.clientWidth/2, y=this.el.clientHeight/2) {
      const before=this.s; this.s=Math.max(1,Math.min(this.max,this.s*factor));
      this.x=x-(x-this.x)*this.s/before; this.y=y-(y-this.y)*this.s/before; this.paint();
    }
    down(e) {
      if (!this.ready || e.target.closest('button')) return;
      this.el.setPointerCapture(e.pointerId); this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
      if (this.pointers.size===1) this.start={x:e.clientX,y:e.clientY,t:performance.now(),s:this.s,moved:false,pinched:false};
      if (this.pointers.size>1 && this.start) this.start.pinched=true;
    }
    move(e) {
      const before=this.pointers.get(e.pointerId); if(!before)return;
      const all=[...this.pointers.entries()];
      this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
      if (this.start && Math.hypot(e.clientX-this.start.x,e.clientY-this.start.y)>8) this.start.moved=true;
      if (all.length===2) {
        const old=all.map(a=>a[1]), next=[...this.pointers.values()];
        const oldDist=Math.hypot(old[1].x-old[0].x,old[1].y-old[0].y), dist=Math.hypot(next[1].x-next[0].x,next[1].y-next[0].y);
        const r=this.el.getBoundingClientRect(), ox=(old[0].x+old[1].x)/2-r.left, oy=(old[0].y+old[1].y)/2-r.top;
        const nx=(next[0].x+next[1].x)/2-r.left, ny=(next[0].y+next[1].y)/2-r.top;
        const s=Math.max(1,Math.min(this.max,this.s*(oldDist?dist/oldDist:1)));
        this.x=nx-(ox-this.x)*s/this.s; this.y=ny-(oy-this.y)*s/this.s; this.s=s; this.paint();
      } else if (all.length===1 && (!this.swipe || this.s>1)) { this.x+=e.clientX-before.x; this.y+=e.clientY-before.y; this.paint(); }
    }
    up(e) {
      if(!this.pointers.has(e.pointerId))return;
      this.pointers.delete(e.pointerId);
      if(this.pointers.size || !this.start)return;
      const start=this.start; this.start=null;
      const dx=e.clientX-start.x, dy=e.clientY-start.y;
      if(!start.pinched && this.swipe && start.s<=1.01 && Math.abs(dx)>60 && Math.abs(dx)>Math.abs(dy)*1.5 && performance.now()-start.t<1000) {this.swipe(dx<0?1:-1); return;}
      if(!start.moved && !start.pinched) {
        const now=performance.now();
        if(now-this.lastTap<300){this.s>1.01?this.fit():this.zoom(2,e.offsetX,e.offsetY);this.lastTap=0;}else this.lastTap=now;
      }
    }
  }
  const mapSurface = new PanZoom($('mapViewport'), $('mapCanvas'), {change:() => {
    $('mapZoomLabel').textContent=Math.round(mapSurface.s*100)+'%';
    if(mapPlanKey)mapViews.set(mapPlanKey,mapSurface.snapshot());
    drawPins();
  }});
  const photoSurface = new PanZoom($('photoViewport'), $('photoImage'), {swipe:delta=>photoStep(delta)});
  function proposed(p) { return p.stage.startsWith('Proposed') && !!data.proposedPlans?.[p.floor]; }
  function planKey() { return state.floor + ':' + (state.stage.startsWith('Proposed') && data.proposedPlans?.[state.floor] ? 'proposed' : 'existing'); }
  function coordinates(p) {
    const x = proposed(p) ? p.proposedMapX : p.mapX, y = proposed(p) ? p.proposedMapY : p.mapY;
    return Number.isFinite(x) && Number.isFinite(y) ? {x,y} : null;
  }
  function mapCandidates() {
    const list=state.stage==='Proposed · Layout' ? data.photos.filter(p=>p.floor===state.floor && p.type==='blender' && (!state.room || state.room===p.zone)) : photosFor();
    return list.map(p=>({p, ...coordinates(p)})).filter(pt=>Number.isFinite(pt.x)&&Number.isFinite(pt.y));
  }
  function drawMap() {
    const prop=state.stage.startsWith('Proposed') && data.proposedPlans?.[state.floor];
    $('mapTitle').textContent=floorName(state.floor)+' · '+(prop?'Proposed reference':'Existing reference');
    $('mapSub').textContent=mobile.matches?'Tap a marker to preview photos · drag or pinch to explore':'Select a marker to view a photo. Drag to pan; zoom for nearby viewpoints.';
    $('mapFoot').textContent=state.floor==='EXT'?'Illustrative site reference, not a survey. Exterior camera positions are approximate. Rear / west is up; driveway / north is right. The aerial marker is an overview, not the drone location.':prop?(data.proposedPlanInfo?.[state.floor]?.notes || 'Blender overhead for navigation; approximate camera alignment. Individual renders retain their design revision. Not a dimensioned construction plan.'):'CubiCasa existing-layout reference. Camera positions come from the photo labeler; markers and viewing directions retain their original confidence. North is to the right on Floor 1.';
    const src=prop || data.plans?.[state.floor];
    $('mapCanvas').hidden=!src; $('noPlan').hidden=!!src;
    if(!src || isResources()){selectedMarker=[];updateMapCard();return;}
    const key=planKey();
    if(mapPlanKey!==key || $('plan').getAttribute('src')!==src){
      if(mapPlanKey && mapSurface.ready)mapViews.set(mapPlanKey,mapSurface.snapshot());
      mapPlanKey=key; clusterSignature='';
      const img=$('plan');
      img.onload=()=>{mapSurface.load(img.naturalWidth/img.naturalHeight,mapViews.get(key));drawPins(true);};
      img.src=src;
      if(img.complete && img.naturalWidth)mapSurface.load(img.naturalWidth/img.naturalHeight,mapViews.get(key));
    }else {mapSurface.resize();drawPins(true);}
    updateMapCard();
  }
  function drawPins(force=false) {
    if(!mapSurface.ready || isResources())return;
    const pts=mapCandidates();
    const signature=[mobile.matches,mapSurface.w.toFixed(0),mapSurface.h.toFixed(0),mapSurface.s.toFixed(2),state.selected,selectedMarker.join(','),pts.map(pt=>pt.p.id).join(',')].join('|');
    if(!force && signature===clusterSignature)return;clusterSignature=signature;
    const clusters=[];
    for(const pt of pts){
      const c=clusters.find(c=> mobile.matches ? Math.hypot((c.x-pt.x)*mapSurface.w*mapSurface.s/100,(c.y-pt.y)*mapSurface.h*mapSurface.s/100)<40 : c.members[0].p.zone===pt.p.zone && Math.hypot(c.x-pt.x,c.y-pt.y)<1.8);
      if(c){c.members.push(pt);c.x=c.members.reduce((sum,p)=>sum+p.x,0)/c.members.length;c.y=c.members.reduce((sum,p)=>sum+p.y,0)/c.members.length;}else clusters.push({x:pt.x,y:pt.y,members:[pt]});
    }
    $('pins').replaceChildren();
    for(const c of clusters){
      const ids=c.members.map(pt=>pt.p.id), p=c.members.find(pt=>pt.p.id===state.selected)?.p || c.members[0].p;
      const selected=ids.some(id=>selectedMarker.includes(id)) || (!selectedMarker.length && ids.includes(state.selected));
      const b=makeButton(c.members.length>1?String(c.members.length):p.id,()=>{
        if(mobile.matches){selectedMarker=ids;state.selected=p.id;drawPins(true);updateMapCard();}
        else {selectedMarker=ids;selectPhoto(p.id);updateMapCard();}
      },'pin'+(isRender(p)?' render':'')+(selected?' selected':''));
      b.style.left=c.x+'%';b.style.top=c.y+'%';
      b.setAttribute('aria-label',(c.members.length>1?c.members.length+' photos: ':'')+c.members.map(pt=>pt.p.id+' '+(pt.p.looking||pt.p.zone)).join('; '));
      b.title=c.members.map(pt=>pt.p.id+' · '+pt.p.zone).join('\n');
      const direction=isRender(p)?p.mapDirectionDegrees:bearings[p.facing]===undefined?null:(bearings[p.facing]+90)%360;
      if(c.members.length===1 && Number.isFinite(direction)) {const arrow=document.createElement('span');arrow.className='viewdir';arrow.style.transform='rotate('+direction+'deg)';arrow.setAttribute('aria-hidden','true');b.append(arrow);}
      else if(c.members.length===1 && isRender(p)){const badge=document.createElement('span');badge.className='viewbadge';badge.textContent=p.viewMode==='Top'?'TOP':'OVERVIEW';b.append(badge);}
      $('pins').append(b);
    }
  }
  function updateMapCard() {
    const ids=selectedMarker.filter(id=>byId.has(id));$('mapCard').hidden=!ids.length;
    if(!ids.length){$('mapCardPhotos').replaceChildren();return;}
    const list=ids.map(id=>byId.get(id));
    $('mapCardTitle').textContent=list.length>1?list.length+' photos at this marker':list[0].zone || list[0].looking;
    $('mapCardNote').textContent=list.length>1?'Tap a preview to view photos. Zoom in to separate nearby viewpoints.':'Camera / room location · approximate unless confirmed. Tap to view.';
    $('mapCardPhotos').replaceChildren(...list.map(p=>{
      const b=makeButton('',()=>openPhoto(p.id,ids),'marker-photo');
      b.setAttribute('aria-label','View photo '+p.id+' · '+(p.looking||p.zone));
      const img=document.createElement('img');img.loading='lazy';setImage(img,p);
      const span=document.createElement('span');span.textContent=p.looking||p.zone;
      const small=document.createElement('small');small.textContent=p.id+' · View photo →';span.append(small);b.append(img,span);return b;
    }));
    requestAnimationFrame(()=>mapSurface.resize());
  }

  function openPhoto(id, ids) {
    if(!byId.has(id))return;
    photoIds=(ids?.length?ids:[id]).filter(id=>byId.has(id));photoId=id;sourceStack=[];
    $('photoDetails').hidden=true;$('photoDetailsButton').setAttribute('aria-expanded','false');
    if(!overlay)present('photo');
    populateDialog();
  }
  function populateDialog() {
    const p=byId.get(photoId);if(!p)return;
    $('photoTitle').textContent=p.looking||p.zone;
    $('photoKicker').textContent=p.id+' · '+floorName(p.floor)+' · '+(p.type==='photoreal'?'AI photoreal':p.type==='blender'?'Blender render':p.type==='resource'?'Reference diagram':p.stage);
    const index=photoIds.indexOf(photoId);
    $('photoCounter').textContent=sourceStack.length?'Source comparison':(index+1)+' / '+photoIds.length;
    $('photoPrev').disabled=sourceStack.length>0 || index<=0;
    $('photoNext').disabled=sourceStack.length>0 || index<0 || index>=photoIds.length-1;
    $('showOnMap').hidden=!coordinates(p) || p.type==='resource';
    $('sourcePhoto').hidden=!p.sourceRenderId || !byId.has(p.sourceRenderId);
    $('sourcePhoto').textContent='Source render '+(p.sourceRenderId||'');
    $('returnPhoto').hidden=!sourceStack.length;
    $('returnPhoto').textContent='← Back to '+(sourceStack.length?sourceStack[sourceStack.length-1]:'photo');
    $('photoTip').textContent=p.type==='resource'?'Pinch to inspect · diagrams retain their stated assumptions':'Swipe to browse · Pinch to zoom';
    detailsFor(p,$('photoDetails'),linkedPhoto);
    const img=$('photoImage');img.onload=()=>photoSurface.load(img.naturalWidth/img.naturalHeight);
    setImage(img,p);
    if(img.complete && img.naturalWidth)photoSurface.load(img.naturalWidth/img.naturalHeight);
    history.replaceState({...history.state,cedarOverlay:'photo',photoId},'');
  }
  function photoStep(delta) {
    if(sourceStack.length)return;
    const index=photoIds.indexOf(photoId),id=photoIds[index+delta];if(!id)return;
    photoId=id;populateDialog();
    // Selection changes do not rebuild the gallery, so closing returns to its exact position.
    if(photosFor().some(p=>p.id===id))selectPhoto(id,false);
  }
  function linkedPhoto(id) {if(!byId.has(id))return;sourceStack.push(photoId);photoId=id;populateDialog();}
  $('sourcePhoto').onclick=()=>linkedPhoto(byId.get(photoId)?.sourceRenderId);
  $('returnPhoto').onclick=()=>{photoId=sourceStack.pop();populateDialog();};
  $('showOnMap').onclick=()=>{
    const p=byId.get(photoId);if(!p || !coordinates(p))return;
    dismiss(()=>{
      if(state.mode==='gallery')galleryScroll=dialogScroll;
      Object.assign(state,{floor:p.floor,stage:p.stage,room:p.zone||'',kind:'',revision:'',query:'',selected:p.id});
      selectedMarker=[p.id];state.mode='map';render();
      if(mobile.matches)scrollTo({top:document.querySelector('.mobile-toolbar').offsetTop,behavior:'instant'});
      requestAnimationFrame(()=>{mapSurface.resize();drawPins(true);});
    });
  };
  $('photoPrev').onclick=()=>photoStep(-1);$('photoNext').onclick=()=>photoStep(1);
  $('closePhoto').onclick=()=>dismiss();$('closeSheet').onclick=()=>dismiss();
  $('photoDetailsButton').onclick=()=>{const open=$('photoDetails').hidden;$('photoDetails').hidden=!open;$('photoDetailsButton').setAttribute('aria-expanded',open);};
  $('openHero').onclick=()=>openPhoto(state.selected,photosFor().map(p=>p.id));
  $('prev').onclick=()=>{const ids=photosFor().map(p=>p.id),i=ids.indexOf(state.selected);if(i>0)selectPhoto(ids[i-1]);};
  $('next').onclick=()=>{const ids=photosFor().map(p=>p.id),i=ids.indexOf(state.selected);if(i>=0&&i<ids.length-1)selectPhoto(ids[i+1]);};
  $('floorCrumb').onclick=()=>chooser('floor');$('roomCrumb').onclick=()=>chooser('room');$('stageCrumb').onclick=()=>chooser('stage');
  $('filterButton').onclick=advancedFilters;
  $('galleryMode').onclick=()=>chooseMode('gallery');$('mapMode').onclick=()=>chooseMode('map');
  $('zone').onchange=e=>changeContext({room:e.target.value});$('kind').onchange=e=>changeContext({kind:e.target.value});$('revision').onchange=e=>changeContext({revision:e.target.value});
  let queryTimer; $('q').oninput=e=>{clearTimeout(queryTimer);queryTimer=setTimeout(()=>changeContext({query:e.target.value}),160);};
  $('reset').onclick=()=>changeContext({room:'',kind:'',revision:'',query:''});
  $('mapZoomIn').onclick=()=>mapSurface.zoom(1.5);$('mapZoomOut').onclick=()=>mapSurface.zoom(1/1.5);$('mapFit').onclick=()=>mapSurface.fit();
  $('photoZoomIn').onclick=()=>photoSurface.zoom(1.5);$('photoZoomOut').onclick=()=>photoSurface.zoom(1/1.5);$('photoFit').onclick=()=>photoSurface.fit();
  $('closeMapCard').onclick=()=>{selectedMarker=[];updateMapCard();drawPins(true);};
  addEventListener('keydown',e=>{
    if(e.target.closest('input,select,textarea') || overlay==='sheet')return;
    if(e.key==='ArrowLeft'){e.preventDefault();overlay==='photo'?photoStep(-1):$('prev').click();}
    if(e.key==='ArrowRight'){e.preventDefault();overlay==='photo'?photoStep(1):$('next').click();}
  });
  mobile.addEventListener('change',()=>{clusterSignature='';syncControls();requestAnimationFrame(()=>{mapSurface.resize();drawPins(true);});});
  new ResizeObserver(entries=>{const h=entries[0].target.getBoundingClientRect().height;if(h)document.documentElement.style.setProperty('--toolbar-h',h+'px');}).observe(document.querySelector('.mobile-toolbar'));
  const count=type=>data.photos.filter(p=>p.type===type).length;
  $('collectionSummary').textContent=count('site')+' site photos · '+count('blender')+' renders · '+count('photoreal')+' photoreal views';
  $('buildSummary').textContent=data.buildId||'Source revisions preserved';
  // Discard only our stale modal marker after a reload; retain any unrelated history fields.
  if(history.state?.cedarOverlay){const s={...history.state};delete s.cedarOverlay;history.replaceState(s,'');}
  render();
})();
