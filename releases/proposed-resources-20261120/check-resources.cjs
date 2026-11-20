const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
const manifest = require('./manifest.json');
const url = process.env.CEDAR_RESOURCE_URL || pathToFileURL('sites/43cedar/interactive_map/index.html').href;
const ids = ['RES31','RES32','RES33','RES34'];
async function chooseFloor(page, width, name) {
  if (width > 1100) await page.locator('#floorButtons button').filter({hasText:new RegExp('^'+name+'$')}).click();
  else {
    await page.locator('#floorCrumb').click();
    await page.locator('#sheetContent .chooser-option').filter({hasText:new RegExp('^'+name)}).click();
    await page.locator('#filterSheet').waitFor({state:'hidden'});
  }
}
async function check(browser,width) {
  const page=await browser.newPage({viewport:{width,height:900}}), errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  try {
    await page.goto(url+'#proposed-resources',{timeout:30000});
    const data=JSON.parse(await page.locator('#appdata').textContent());
    assert.equal(data.photos.length,manifest.totalRecords);
    for(const a of manifest.assets){const p=data.photos.find(p=>p.id===a.id);assert.equal(p.floor,a.floor);assert.equal(p.type,'resource');assert.equal(p.stage,'Proposed · Resources');assert.equal(p.imageSHA256,a.sha256);}
    for(const [floor,wanted,absent] of [['Floor 2',ids.slice(0,3),['RES34']],['Exterior',['RES34'],ids.slice(0,3)]]) {
      await chooseFloor(page,width,floor);
      for(const id of absent) assert.equal(await page.locator(`.tile[data-photo-id="${id}"]`).count(),0,`${id} leaked into ${floor}`);
      for(const id of wanted) {
        const tile=page.locator(`.tile[data-photo-id="${id}"]`);
        await tile.waitFor({state:'visible'});
        const dimensions=await tile.locator('img').evaluate(async image=>{image.loading='eager';await image.decode();return [image.naturalWidth,image.naturalHeight]});
        const a=manifest.assets.find(a=>a.id===id);assert.deepEqual(dimensions,[a.width,a.height]);
        await tile.click();await page.locator('#photoDialog').waitFor({state:'visible'});
        await page.locator('#photoDialog img').evaluate(async image=>{await image.decode();if(!image.naturalWidth)throw Error('Empty full-size resource')});
        await page.keyboard.press('Escape');await page.locator('#photoDialog').waitFor({state:'hidden'});
      }
    }
    assert.deepEqual(errors,[]);
    console.log(`- ${width}px: all four resources opened and decoded at full resolution; Floor 2 / Exterior assignments and separation passed.`);
  } finally {await page.close();}
}
(async()=>{const browser=await chromium.launch({executablePath:process.env.CEDAR_BROWSER});try{for(const width of [1440,390])await check(browser,width);}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
