const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const viewer = pathToFileURL('sites/43cedar/interactive_map/index.html').href;

async function checkViewport(browser, width) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  try {
    await page.goto(viewer, { timeout: 30_000 });
    const data = await page.locator('#appdata').textContent({ timeout: 10_000 });
    const { photos } = JSON.parse(data);
    assert.ok(Array.isArray(photos) && photos.length, 'The viewer has no photo records');

    const firstTile = page.locator('#gallery .tile').first();
    await firstTile.waitFor({ state: 'visible', timeout: 15_000 });
    const image = firstTile.locator('img');
    await image.evaluate(async element => {
      element.loading = 'eager';
      await element.decode();
    }, undefined, { timeout: 15_000 });
    assert.deepEqual(errors, [], 'The viewer raised an uncaught error');
    console.log(`- ${width}px viewport passed with ${photos.length} viewer records and a decoded gallery image.`);
  } finally {
    await page.close();
  }
}

async function main() {
  const browser = await chromium.launch({ executablePath: process.env.CEDAR_BROWSER });
  try {
    await checkViewport(browser, 1440);
    await checkViewport(browser, 390);
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
