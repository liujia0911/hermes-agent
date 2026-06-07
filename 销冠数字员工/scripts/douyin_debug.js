const { chromium } = require('playwright');
const path = require('path');

const AUTH = path.join(__dirname, 'douyin_auth.json');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ 
    viewport: { width: 1920, height: 1080 },
    storageState: AUTH 
  });
  const page = await context.newPage();

  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  console.log('TITLE:', await page.title());
  console.log('URL:', page.url());

  await page.screenshot({ path: path.join(__dirname, 'douyin_home.png') });
  console.log('Screenshot saved');

  // Get all visible numbers/statistics
  const stats = await page.evaluate(() => {
    const result = [];
    // Common stat patterns on data dashboards
    const allElements = document.querySelectorAll('*');
    for (const el of allElements) {
      const text = el.textContent.trim();
      // Look for elements containing common metric names
      if (/(播放|点赞|评论|分享|粉丝|获赞|主页访问|视频播放|互动|新增粉丝)/.test(text) && text.length < 50) {
        result.push(text);
      }
    }
    return result.slice(0, 30);
  });
  console.log('\nSTAT ELEMENTS:');
  stats.forEach(s => console.log('  -', s));

  // Try data page
  await page.goto('https://creator.douyin.com/creator-micro/data/content', { 
    waitUntil: 'networkidle', timeout: 15000 
  });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(__dirname, 'douyin_data.png') });

  // Intercept API
  const apiData = [];
  page.on('response', async (resp) => {
    const u = resp.url();
    if (u.includes('statistics') || u.includes('overview') || u.includes('dashboard')) {
      try {
        const b = await resp.text();
        apiData.push({ url: u, body: b.substring(0, 1000) });
      } catch(e) {}
    }
  });

  await page.reload({ waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(3000);

  console.log('\nAPI CALLS:', apiData.length);
  apiData.forEach(d => {
    console.log('  URL:', d.url);
    console.log('  Body:', d.body);
  });

  await browser.close();
})();
