const { chromium } = require('playwright');
const path = require('path');

const AUTH=path.join(__dirname, 'douyin_auth.json');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ 
    viewport: { width: 1920, height: 1080 },
    storageState: AUTH 
  });
  const page = await context.newPage();

  // Go to creator main page first
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Get all clickable links and buttons
  const links = await page.evaluate(() => {
    const result = [];
    const anchors = document.querySelectorAll('a, button, [role="link"], [role="tab"]');
    for (const el of anchors) {
      const text = el.textContent.trim();
      const href = el.getAttribute('href') || '';
      if (text && text.length < 30) {
        result.push({ text, href });
      }
    }
    return result;
  });
  console.log('=== CLICKABLE ELEMENTS ===');
  links.forEach(l => {
    if (l.text) console.log(`  [${l.text}] -> ${l.href}`);
  });

  // Try to find and click "数据中心" or "数据"
  console.log('\n=== TRYING DATA CENTER ===');
  try {
    // Try clicking elements with specific text
    const dataLinks = ['数据中心', '数据', '作品数据', '内容管理', '内容', '视频管理'];
    for (const keyword of dataLinks) {
      const el = page.locator(`text="${keyword}"`).first();
      if (await el.count() > 0) {
        console.log(`Found: "${keyword}", clicking...`);
        await el.click();
        await page.waitForTimeout(3000);
        console.log('URL after click:', page.url());
        
        // Take screenshot
        await page.screenshot({ 
          path: path.join(__dirname, `douyin_${keyword}.png`) 
        });
        
        // Get page text
        const text = await page.evaluate(() => document.body.innerText);
        console.log('Page text (first 1000):', text.substring(0, 1000));
        break;
      }
    }
  } catch (e) {
    console.log('Click error:', e.message);
  }

  // Also try direct navigation to common data URLs
  console.log('\n=== DIRECT NAVIGATION ===');
  const urls = [
    'https://creator.douyin.com/creator-micro/data/overview',
    'https://creator.douyin.com/creator-micro/data/fans',
    'https://creator.douyin.com/creator-micro/content/video',
    'https://creator.douyin.com/creator-micro/content/manage',
  ];
  
  for (const url of urls) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
      await page.waitForTimeout(2000);
      const text = await page.evaluate(() => document.body.innerText);
      console.log(`\n${url}`);
      console.log(text.substring(0, 300));
    } catch (e) {
      console.log(`${url}: ${e.message}`);
    }
  }

  await browser.close();
})();
