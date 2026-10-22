"""Extend the existing viewer with a floor-specific reference section."""
def patch_ui(source):
    source=source.replace('Rev18','Rev20')
    source=source.replace('Photoreal / Build','Photoreal / Resources / Build')
    source=source.replace('const imageFor=p=>',"const imageFor=p=>p.type==='resource'?d.resourceImages[p.imageId]:")
    source=source.replace("'Proposed · Photoreal','Build'","'Proposed · Photoreal','Proposed · Resources','Build'")
    source=source.replace("let floor='F1',stage='Existing',sel='C020'", "let floor='F1',stage=location.hash==='#proposed-resources'?'Proposed · Resources':'Existing',sel='C020'")
    source=source.replace("stage=s;sel='';", "stage=s;history.replaceState(null,'',s==='Proposed · Resources'?'#proposed-resources':location.pathname+location.search);sel='';")
    source=source.replace('function drawMap(){','function drawMap(){if(stage===\'Proposed · Resources\'){return;}')
    source=source.replace("$('status').textContent=p.type==='photoreal'?", "$('status').textContent=p.type==='resource'?'Reference · provisional':p.type==='photoreal'?")
    source=source.replace("$('where').textContent=isRender(p)?", "$('where').textContent=p.type==='resource'?p.source:isRender(p)?")
    source=source.replace("$('heading').textContent=isRender(p)?", "$('heading').textContent=p.type==='resource'?p.referenceStatus:isRender(p)?")
    source=source.replace("function draw(){drawButtons();", "function draw(){const resources=stage==='Proposed · Resources';document.body.classList.toggle('resources-mode',resources);$('catalogTitle').textContent=resources?'Proposed Resources':'Photo & render catalog';$('catalogSub').textContent=resources?'Diagrams, overheads and reference studies. Select Floor 1 or Floor 2 above; open an image for a larger view. Measurements and historical studies retain their stated limits.':'Real photo location markers are user-confirmed. Blender marker locations indicate the nearest comparable existing viewpoint and may not be the exact Blender camera.';drawButtons();")
    source=source.replace("['Proposed · Render','Proposed · Photoreal'].includes(stage)","['Proposed · Render','Proposed · Photoreal','Proposed · Resources'].includes(stage)")
    source=source.replace("if(empty){$('emptyText').textContent=", "if(empty){$('emptyText').textContent=resources?'No proposed reference materials for this location. Choose Floor 1 or Floor 2.':")
    source=source.replace('<h2>Photo & render catalog</h2><div class="sub">','<h2 id="catalogTitle">Photo & render catalog</h2><div class="sub" id="catalogSub">')
    css='''\n.resources-mode .main{grid-template-columns:1fr}.resources-mode .main>section:first-child{display:none}.resources-mode .bigimage{height:min(70vh,900px)}.resources-mode .tile img{object-fit:contain;height:165px;background:#f8fafb}.resources-mode .gallery{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}.resources-mode #hero{cursor:zoom-in}.image-dialog{border:0;padding:12px;border-radius:12px;max-width:98vw;max-height:97vh;background:white}.image-dialog::backdrop{background:#102733dd}.image-dialog img{max-width:94vw;max-height:86vh;object-fit:contain}.image-dialog button{display:block;margin:0 0 8px auto;padding:7px 14px}.intro a{white-space:nowrap}\n'''
    source=source.replace('</style>',css+'</style>',1)
    source=source.replace('<script id="appdata"', '<dialog id="resourceZoom" class="image-dialog"><button type="button" id="closeResourceZoom">Close ×</button><img id="resourceZoomImage" alt="Enlarged reference"></dialog><script id="appdata"',1)
    source=source.replace("$('zone').onchange=draw;", "$('hero').onclick=()=>{if(stage!=='Proposed · Resources')return;const im=$('resourceZoomImage');im.src=$('hero').src;im.alt=$('caption').textContent;$('resourceZoom').showModal();};$('closeResourceZoom').onclick=()=>$('resourceZoom').close();$('resourceZoom').onclick=e=>{if(e.target===$('resourceZoom'))$('resourceZoom').close();};$('zone').onchange=draw;")
    return source
