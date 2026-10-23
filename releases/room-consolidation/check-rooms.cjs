const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:process.env.CEDAR_BROWSER || undefined,args:['--no-sandbox']});
const checks=[];
for(const width of [1440,390]){
 const page=await browser.newPage({viewport:{width,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file://'+process.cwd()+'/'+(process.argv[2] || 'consolidated.html'));
 await page.waitForSelector('#gallery .tile');
 const options=await page.locator('#zone option').allTextContents();
 for(const old of ['Porch-side bedroom','North bedroom / closets','Pink shower bathroom','Fireplace / living room','Foyer / stairs','Entrance hallway','Hall / tiled bathroom'])if(options.includes(old))throw Error('Duplicate remains: '+old);
 // Programmatic desktop control also drives the same state on narrow screens.
 await page.locator('#zone').selectOption('Bedroom 1',{force:true});
 let count=await page.locator('#gallery .tile').count();if(count!==13)throw Error('Existing Bedroom 1 '+count);
 await page.getByRole('button',{name:'Proposed · Render',exact:true}).evaluate(b=>b.click());
 count=await page.locator('#gallery .tile').count();if(count!==10)throw Error('Render Bedroom 1 '+count);
 await page.locator('#zone').selectOption('Bedroom 2',{force:true});
 count=await page.locator('#gallery .tile').count();if(count!==11)throw Error('Render Bedroom 2 '+count);
 await page.locator('#q').fill('north bedroom',{force:true}); await page.waitForTimeout(250);
 // Legacy names belong to historical photos; searching them under Existing finds that room.
 await page.getByRole('button',{name:'Existing',exact:true}).evaluate(b=>b.click());
 count=await page.locator('#gallery .tile').count();if(count!==16)throw Error('Legacy search '+count);
 await page.locator('#reset').evaluate(b=>b.click());
 if(width===390){
  await page.locator('#roomCrumb').click();
  const names=await page.locator('.chooser-option span:first-child').allTextContents();
  if(names.length!==options.length)throw Error('Mobile/desktop room disagreement');
  await page.locator('#closeSheet').click();await page.waitForTimeout(250);
 }
 if(errors.length)throw Error(errors.join('\n'));
 
 checks.push({width,uniqueRoomChoices:options.length-1,existingBedroom1:13,renderBedroom1:10,renderBedroom2:11,legacySearchBedroom2:16,pageErrors:errors});
 await page.close();
}
await browser.close();fs.writeFileSync('releases/room-consolidation/BROWSER_QA.json',JSON.stringify(checks,null,2));console.log(JSON.stringify(checks));
})().catch(e=>{console.error(e);process.exit(1)});
