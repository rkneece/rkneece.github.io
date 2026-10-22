const {chromium}=require('playwright');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const p=await browser.newPage({viewport:{width:1400,height:1000}});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto('file:///tmp/cedar-output.html');
await p.getByRole('button',{name:/Exterior.*site photos/}).click();
await p.locator('#plan').evaluate(e=>e.decode());
if(await p.locator('#results').textContent()!=='17 entries')throw Error('Expected 5 site and 12 Zillow exterior photos');
for(const id of ['ZEXT01','ZEXT06','ZEXT28']){
 await p.locator('.tile').filter({hasText:id}).click();
 await p.locator('#hero').evaluate(e=>e.decode());
 if(!(await p.locator('#where').textContent()).match(/Approximate|Aerial overview/))throw Error('Missing estimated placement label');
}
await p.getByLabel(/ZEXT01 —/).click();
if(!(await p.locator('#caption').textContent()).startsWith('ZEXT01'))throw Error('Pin did not open photo');
await p.locator('#zone').selectOption('Accessory building');
if(await p.locator('.tile').count()!==3)throw Error('Accessory filter mismatch');
await p.locator('#reset').click();
for(const name of [/Floor 1.*site photos/,/Floor 2.*site photos/,/Exterior.*site photos/]){
 await p.getByRole('button',{name}).click();
 await p.locator('#plan').evaluate(e=>e.decode());
}
await p.locator('#gallery img').evaluateAll(es=>Promise.all(es.map(e=>{e.loading='eager';return e.decode()})));
if(errors.length)throw Error(errors.join('; '));
console.log('QA_PASS: 17 exterior entries; all 12 embedded Zillow photos; pin clicks, estimates, room filters and three floors.');
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
