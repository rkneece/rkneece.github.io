const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const base=__dirname;
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 const errors=[],page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>errors.push(e.message));
 const target=process.argv[2]||'file://'+path.resolve('sites/43cedar/interactive_map/index.html');
 await page.goto(target,{waitUntil:'domcontentloaded'});
 async function stage(label){
  if(await page.locator('#stageCrumb').isVisible()){
   await page.locator('#stageCrumb').click();
   await page.locator('#sheetContent button').filter({hasText:label}).first().click();
  }else{
   await page.locator('#stages button').filter({hasText:label}).first().click();
  }
 }
 await stage('Proposed · Photoreal');
 for(const id of ['R03','R49']){
  const tile=page.locator('[data-photo-id="'+id+'"]');await tile.scrollIntoViewIfNeeded();await tile.click();
  await page.waitForFunction(()=>{const im=document.getElementById('photoImage');return im.complete&&im.naturalWidth>0});
  await page.screenshot({path:path.join(base,id+'-browser.png')});
  await page.locator('#closePhoto').click();
 }
 await stage('Proposed · Render');
 await page.locator('[data-photo-id="NI01"]').scrollIntoViewIfNeeded();
 await page.locator('[data-photo-id="NI01"]').click();
 await page.waitForFunction(()=>{const im=document.getElementById('photoImage');return im.complete&&im.naturalWidth>0});
 await page.locator('#closePhoto').click();
 await page.setViewportSize({width:390,height:844});
 await stage('Proposed - Tests');
 if(await page.locator('#gallery [data-photo-id]').count()<54)throw new Error('Test gallery missing entries');
 await page.screenshot({path:path.join(base,'mobile-tests-browser.png')});
 if(errors.length)throw new Error(errors.join('\n'));
 fs.writeFileSync(path.join(base,'BROWSER_QA.json'),JSON.stringify({status:'PASS',desktop_views:['R03','R49','NI01'],mobile_tests:54,page_errors:errors},null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
