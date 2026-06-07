const { chromium } = require('playwright');
const path = require('path');

const userDataDir = path.join(__dirname, 'douyin_profile');

(async () => {
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: true,
    viewport: { width: 1920, height: 1080 }
  });
  const page = await ctx.newPage();
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(5000);

  console.log('TITLE:', await page.title());
  console.log('URL:', page.url());

  const text = await page.evaluate(() => document.body.innerText);
  const loggedIn = !text.includes('扫码登录');
  console.log('Logged in:', loggedIn);
  console.log('=== Page text (first 1500) ===');
  console.log(text.substring(0, 1500));

  if (loggedIn) {
    // Try to navigate via the side menu
    console.log('\n=== Trying navigation ===');
    
    // Look for data-related links in the actual logged-in page
    const allLinks = await page.evaluate(() => {
      const links = [];
      document.querySelectorAll('a, [role="tab"], [class*="menu"] span, [class*="nav"] span').forEach(el => {
        const t = el.textContent.trim();
        const h = el.getAttribute('href') || el.closest('a')?.getAttribute('href') || '';
        if (t && t.length < 20) links.push({ text: t, href: h });
      });
      return links;
    });
    
    const uniqueLinks = [];
    const seen = new Set();
    for (const l of allLinks) {
      if (!seen.has(l.text)) {
        seen.add(l.text);
        uniqueLinks.push(l);
      }
    }
    console.log('Links found:', uniqueLinks.length);
    uniqueLinks.slice(0, 30).forEach(l => console.log(`  [${l.text}] ${l.href}`));
    
    // Try click common nav items
    const navTargets = ['内容管理', '数据中心', '作品管理', '视频管理', '数据'];
    for (const target of navTargets) {
      try {
        const el = page.locator(`text="${target}"`).first();
        if (await el.count() > 0) {
          console.log(`\nClicking "${target}"...`);
          await el.click({ timeout: 5000 });
          await page.waitForTimeout(5000);
          console.log('New URL:', page.url());
          const newText = await page.evaluate(() => document.body.innerText);
          console.log('New text:', newText.substring(0, 500));
        }
      } catch (e) {
        console.log(`  "${target}": ${e.message.substring(0, 60)}`);
      }
    }
  }

  await ctx.close();
})();
