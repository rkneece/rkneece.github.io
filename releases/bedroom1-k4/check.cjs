const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
(async()=>{
 const file=path.resolve('sites/43cedar/interactive_map/index.html');const data=JSON.parse(fs.readFileSync(file,'utf8').match(/<script id="appdata" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});const reports=[];
 for(const width of [1440,390]){
  const page=await browser.newPage({viewport:{width,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('file://'+file);await page.waitForSelector('#gallery .tile');await page.locator('#zone').selectOption('Bedroom 1',{force:true});
  const counts={};for(const stage of ['Proposed · Render','Proposed · Photoreal']){
   await page.getByRole('button',{name:stage,exact:true,includeHidden:true}).evaluate(b=>b.click());
   const expected=data.photos.filter(p=>p.floor==='F1'&&p.zone==='Bedroom 1'&&p.stage===stage).length;
   const actual=await page.locator('#gallery .tile').count();if(expected!==actual)throw Error(width+' '+stage+' count mismatch');counts[stage]=actual;
  }
  for(const id of ['R13','R71']){
   await page.locator('#gallery [data-photo-id="'+id+'"]').evaluate(b=>b.click());
   await page.waitForFunction(()=>document.querySelector('#photoImage').complete&&document.querySelector('#photoImage').naturalWidth>0);
   const source=data.photos.find(p=>p.id===id).sourceRenderId;
   if(await page.locator('#sourcePhoto').textContent()!=='Source render '+source)throw Error('Source button mismatch');
   await page.locator('#sourcePhoto').evaluate(b=>b.click());
   await page.waitForFunction(src=>document.querySelector('#photoKicker').textContent.startsWith(src),source);
   await page.waitForFunction(()=>document.querySelector('#photoImage').complete&&document.querySelector('#photoImage').naturalWidth>0);
   await page.locator('#returnPhoto').evaluate(b=>b.click());await page.locator('#closePhoto').evaluate(b=>b.click());
  }
  if(errors.length)throw Error(errors.join('\n'));reports.push({width,counts,sourceLinksAndImages:'PASS',pageErrors:errors});await page.close();
 }await browser.close();fs.writeFileSync('releases/bedroom1-k4/BROWSER_QA.json',JSON.stringify({status:'PASS',reports},null,2));console.log(JSON.stringify(reports));
})().catch(e=>{console.error(e);process.exit(1)});