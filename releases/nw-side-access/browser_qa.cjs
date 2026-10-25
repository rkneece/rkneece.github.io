const fs=require('fs');const path=require('path');const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CEDAR_BROWSER||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 const url='file://'+path.resolve(process.argv[2])+'#proposed-tests';await page.goto(url);await page.waitForFunction(()=>document.querySelector('#results')?.textContent==='61 photos');
 const qa=await page.evaluate(async()=>{
  const d=JSON.parse(document.querySelector('#appdata').textContent);const rows=d.photos.filter(p=>p.modelBranch==='test/island-NW-side-access');if(rows.length!==31)throw Error('wrong new count');if(rows.some(p=>p.zone!=='Dining Area'||p.stage!=='Proposed - Tests'))throw Error('wrong category');
  let loaded=0;for(const p of rows){const src=d[{blender:'blenderImages',photoreal:'photorealImages',resource:'resourceImages'}[p.type]][p.imageId];const im=new Image();im.src=src;await im.decode();if(!im.naturalWidth)throw Error('image empty');loaded++;}
  return {added_images_decoded:loaded,total_tests:d.proposedTests.display_count,native_photoreal_pairs:rows.filter(p=>p.type==='photoreal').length};
 });
 await page.locator('[data-photo-id="NWP01"]').click();await page.getByRole('button',{name:'Source render NWS01',exact:true}).last().click();await page.waitForFunction(()=>document.querySelector('#photoKicker')?.textContent.includes('NWS01'));qa.source_link_works=true;
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.waitForFunction(()=>document.querySelector('#results')?.textContent==='61 photos');qa.mobile_gallery=true;qa.mobile_no_page_overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);if(!qa.mobile_no_page_overflow)throw Error('mobile overflow');if(errors.length)throw Error(errors.join('\n'));qa.page_errors=errors;qa.status='PASS';fs.writeFileSync('releases/nw-side-access/BROWSER_QA.json',JSON.stringify(qa,null,2));console.log(JSON.stringify(qa));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
