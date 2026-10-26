const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 const errors=[],page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>errors.push(e.message));
 const target=process.argv[2]||'file://'+path.resolve('sites/43cedar/interactive_map/index.html');
 await page.goto(target,{waitUntil:'domcontentloaded'});
 async function stage(label){
  if(await page.locator('#stageCrumb').isVisible()){
   await page.locator('#stageCrumb').click();await page.locator('#sheetContent button').filter({hasText:label}).first().click();
  }else await page.locator('#stages button').filter({hasText:label}).first().click();
 }
 await stage('Proposed - Tests');
 const ids=Array.from({length:8},(_,i)=>'CW6_N'+String(i+1).padStart(2,'0')).concat(Array.from({length:8},(_,i)=>'CW6_P'+String(i+1).padStart(2,'0')),['CW6_PLAN01']);
 for(const id of ids){
  const tile=page.locator('[data-photo-id="'+id+'"]');await tile.scrollIntoViewIfNeeded();await tile.click();
  await page.waitForFunction(()=>{const im=document.getElementById('photoImage');return im.complete&&im.naturalWidth>0});
  if(['CW6_P02','CW6_N03'].includes(id))await page.screenshot({path:path.join(__dirname,id+'-browser.png')});
  await page.locator('#closePhoto').click();
 }
 await page.setViewportSize({width:390,height:844});await stage('Proposed - Tests');
 await page.locator('[data-photo-id="CW6_P01"]').scrollIntoViewIfNeeded();await page.locator('[data-photo-id="CW6_P01"]').click();
 await page.waitForFunction(()=>{const im=document.getElementById('photoImage');return im.complete&&im.naturalWidth>0});
 await page.screenshot({path:path.join(__dirname,'mobile-test.png')});await page.locator('#closePhoto').click();
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2))throw Error('Mobile page overflow');
 if(errors.length)throw Error(errors.join('\n'));
 fs.writeFileSync(path.join(__dirname,'BROWSER_QA.json'),JSON.stringify({status:'PASS',desktop_opened:ids,mobile_opened:'CW6_P01',page_errors:errors,target},null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
