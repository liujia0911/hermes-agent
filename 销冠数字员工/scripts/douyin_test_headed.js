const { chromium } = require('playwright');
const path = require('path');
const authFile = path.join(__dirname, 'douyin_auth.json');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const ctx = await browser.newContext({ storageState: authFile });
  const page = await ctx.newPage();
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);
  console.log('TITLE:', await page.title());
  console.log('URL:', page.url());
  const text = await page.evaluate(() => document.body.innerText);
  console.log('Has login form:', text.includes('扫码登录'));
  console.log('Page text (300):', text.substring(0, 300));
  // Keep browser open briefly for inspection
  await page.waitForTimeout(2000);
  await browser.close();
})();
