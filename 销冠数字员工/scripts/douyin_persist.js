const { chromium } = require('playwright');
const path = require('path');

const userDataDir = path.join(__dirname, 'douyin_userdata');

(async () => {
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: true,
    viewport: { width: 1920, height: 1080 }
  });
  const page = await ctx.newPage();
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);
  
  console.log('TITLE:', await page.title());
  const text = await page.evaluate(() => document.body.innerText);
  const loggedIn = !text.includes('扫码登录');
  console.log('Logged in:', loggedIn);
  console.log('Text (500):', text.substring(0, 500));
  
  if (loggedIn) {
    // Try to find data
    const nums = await page.evaluate(() => {
      const all = [];
      document.querySelectorAll('*').forEach(el => {
        const t = el.textContent.trim();
        if (/^\d[\d,.]*万?$/.test(t) && t.length < 10) {
          const label = el.parentElement?.textContent?.trim() || '';
          if (label.length < 50) all.push(label);
        }
      });
      return all.slice(0, 20);
    });
    console.log('Numbers found:', nums);
  }
  
  await ctx.close();
})();
