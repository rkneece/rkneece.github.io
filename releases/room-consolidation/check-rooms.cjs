const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
const html=fs.readFileSync(process.argv[2] || 'consolidated.html','utf8');
const data=JSON.parse(html.match(/<script[^>]*id="appdata"[^>]*>([\s\S]*?)<\/script>/)[1]);
const groups=['Bedroom 1 Bath','Foyer / Stairs','Dining Area','Downstairs Hallway'];
const retired=['Primary bathroom','Entry / stairs','Trim / staircase details','Dining area','Kitchen','Kitchen / dining structure','Laundry closet','Bedroom hallway','Pink shower bathroom','Porch-side bedroom','North bedroom / closets'];
const stages=['Existing','Demo','Proposed · Render','Proposed · Photoreal','Proposed · Resources'];
const browser=await chromium.launch({headless:true,executablePath:process.env.CEDAR_BROWSER || undefined,args:['--no-sandbox']});
const checks=[];
for(const width of [1440,390]){
 const page=await browser.newPage({viewport:{width,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('file://'+process.cwd()+'/'+(process.argv[2] || 'consolidated.html'));
 await page.waitForSelector('#gallery .tile');
 const options=await page.locator('#zone option').allTextContents();
 for(const old of retired)if(options.includes(old))throw Error('Retired room remains: '+old);
 for(const room of groups)if(!options.includes(room))throw Error('Missing room '+room);
 if(options.length-1!==11)throw Error('Expected 11 floor-one room choices, got '+(options.length-1));
 const counts={};
 for(const room of groups){
  counts[room]={};
  await page.locator('#zone').selectOption(room,{force:true});
  for(const stage of stages){
   await page.getByRole('button',{name:stage,exact:true,includeHidden:true}).evaluate(b=>b.click());
   const expected=data.photos.filter(p=>p.floor==='F1' && p.zone===room && p.stage===stage).length;
   const actual=await page.locator('#gallery .tile').count();
   if(actual!==expected)throw Error(room+' / '+stage+': '+actual+' != '+expected);
   counts[room][stage]=actual;
  }
 }
 await page.locator('#reset').evaluate(b=>b.click());
 await page.getByRole('button',{name:'Existing',exact:true,includeHidden:true}).evaluate(b=>b.click());
 await page.locator('#zone').selectOption('Dining Area',{force:true});
 await page.locator('#q').fill('kitchen',{force:true});await page.waitForTimeout(250);
 const legacyCount=await page.locator('#gallery .tile').count();if(!legacyCount)throw Error('Legacy kitchen search lost');
 await page.locator('#reset').evaluate(b=>b.click());
 if(width===390){
  await page.locator('#roomCrumb').click();
  const names=await page.locator('.chooser-option span:first-child').allTextContents();
  if(names.join('|')!==options.join('|'))throw Error('Mobile/desktop room choices differ');
  await page.locator('#closeSheet').click();await page.waitForTimeout(250);
 }
 if(errors.length)throw Error(errors.join('\n'));
 checks.push({width,uniqueRoomChoices:options.length-1,counts,legacyKitchenSearch:legacyCount,pageErrors:errors});
 await page.close();
}
await browser.close();fs.writeFileSync('releases/room-consolidation/BROWSER_QA.json',JSON.stringify(checks,null,2));console.log(JSON.stringify(checks));
})().catch(e=>{console.error(e);process.exit(1)});
