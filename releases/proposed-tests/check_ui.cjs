const {chromium}=require('playwright');const fs=require('fs');const path=require('path');const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CEDAR_BROWSER||'/usr/bin/google-chrome',args:['--no-sandbox']});const results=[],errors=[];const qa=JSON.parse(fs.readFileSync(path.join(__dirname,'PUBLISH_QA.json')));
 for(const mobile of [false,true]){
  const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1365,height:900},isMobile:mobile,hasTouch:mobile});const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://127.0.0.1:8765/#proposed-tests',{waitUntil:'domcontentloaded'});await page.locator('#gallery .tile').nth(29).waitFor();assert.equal(await page.locator('#catalogTitle').innerText(),'Proposed-Tests');assert.deepEqual(await page.locator('#gallery .tile').evaluateAll(es=>es.map(e=>e.dataset.photoId)),qa.test_ids);
  assert.equal(await page.locator('#mapMode').isDisabled(),true);assert.equal(await page.locator('#kind option').filter({hasText:'Proposed-Tests'}).count(),0);
  if(mobile){assert.equal(await page.locator('#stageCrumb').innerText(),'Proposed-Tests');await page.locator('#stageCrumb').click();await page.locator('#sheetContent .chooser-option').filter({hasText:/^Proposed · Resources/}).click();await page.locator('#filterSheet').waitFor({state:'hidden'});}
  else await page.getByRole('button',{name:'Proposed · Resources',exact:true}).click();
  assert.equal(await page.locator('#catalogTitle').innerText(),'Proposed resources');assert.deepEqual(new Set(await page.locator('#gallery .tile').evaluateAll(es=>es.map(e=>e.dataset.photoId))),new Set(['RES01','RES02','RES03','RES06',...qa.current_reference_ids]));
  await page.locator('#gallery [data-photo-id="CUR03"]').click();await page.locator('#photoDialog').waitFor({state:'visible'});assert.match(await page.locator('#photoTitle').innerText(),/CURRENT PROPOSED/);await page.locator('#photoImage').evaluate(i=>i.decode());assert.ok(await page.locator('#photoImage').evaluate(i=>i.complete&&i.naturalWidth>1000));await page.locator('#closePhoto').click();await page.locator('#photoDialog').waitFor({state:'hidden'});
  if(mobile){await page.locator('#stageCrumb').click();const opt=page.locator('#sheetContent .chooser-option').filter({hasText:/^Proposed-Tests/});assert.match(await opt.innerText(),/30 photos/);await opt.click();await page.locator('#filterSheet').waitFor({state:'hidden'});}
  else await page.getByRole('button',{name:'Proposed-Tests',exact:true}).click();
  assert.equal(await page.locator('#gallery .tile').count(),30);
  if(!mobile){await page.locator('#kind').selectOption({label:'Photoreal alternative · TEST'});assert.equal(await page.locator('#gallery .tile').count(),21);await page.locator('#reset').click();assert.equal(await page.locator('#gallery .tile').count(),30);await page.locator('#q').fill('Pantry passage');await page.waitForFunction(()=>document.querySelectorAll('#gallery .tile').length===4);await page.locator('#reset').click();}
  results.push({surface:mobile?'mobile 390x844':'desktop 1365x900',status:'PASS',category:'Proposed-Tests',comparison_items:30,floor1_resources:11,viewpoint_order_current_D_E_G:true,category_not_image_type:true,current_reference_opens:true,navigation_counts:true});await context.close();
 }
 assert.deepEqual(errors,[]);await browser.close();fs.writeFileSync(path.join(__dirname,'BROWSER_QA.json'),JSON.stringify({status:'PASS',results,page_errors:errors},null,2));console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
