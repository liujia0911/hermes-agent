const { chromium } = require('playwright');
const path = require('path');

const authFile = path.join(__dirname, 'douyin_auth.json');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    storageState: authFile
  });
  const page = await ctx.newPage();

  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);

  console.log('TITLE:', await page.title());
  console.log('URL:', page.url());

  const allText = await page.evaluate(() => document.body.innerText);
  console.log('=== PAGE TEXT (first 3000) ===');
  console.log(allText.substring(0, 3000));

  const keywords = ['内容管理','数据中心','数据','作品','视频','创作'];
  for (const kw of keywords) {
    try {
      const btn = page.locator('text=' + kw).first();
      if (await btn.count() > 0) {
        console.log('Clicking ' + kw);
        await btn.click({ timeout: 5000 });
        await page.waitForTimeout(3000);
        console.log('URL:', page.url());
        const text = await page.evaluate(() => document.body.innerText);
        console.log('Text:', text.substring(0, 500));
      }
    } catch (e) {
      console.log('Skip ' + kw + ': ' + e.message.substring(0, 80));
    }
  }

  await browser.close();
})();