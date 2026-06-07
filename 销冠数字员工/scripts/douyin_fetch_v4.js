const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const userDataDir = path.join(__dirname, 'douyin_profile');
const outputFile = path.join(__dirname, 'douyin_data.json');

(async () => {
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: true,
    viewport: { width: 1920, height: 1080 }
  });
  const page = await ctx.newPage();

  await page.goto('https://creator.douyin.com/creator-micro/home', { 
    waitUntil: 'networkidle', timeout: 30000 
  });
  await page.waitForTimeout(5000);

  // Better account name extraction
  const info = await page.evaluate(() => {
    const text = document.body.innerText;
    const result = { account: '未知', douyinId: '', fans: '0', likes: '0', following: '0', hasVideos: false };
    
    // Extract account name (pattern: "账号名\n抖音号：xxx")
    const nameMatch = text.match(/(.+?)\n抖音号[：:]\s*(\S+)/);
    if (nameMatch) {
      result.account = nameMatch[1].trim();
      result.douyinId = nameMatch[2].trim();
    }
    
    // Stats
    const fanMatch = text.match(/粉丝\s*(\d[\d,.]*万?)/);
    if (fanMatch) result.fans = fanMatch[1];
    const likeMatch = text.match(/获赞\s*(\d[\d,.]*万?)/);
    if (likeMatch) result.likes = likeMatch[1];
    const followMatch = text.match(/关注\s*(\d[\d,.]*万?)/);
    if (followMatch) result.following = followMatch[1];
    result.hasVideos = !text.includes('未发布新作品');
    
    return result;
  });

  console.log(JSON.stringify(info));
  fs.writeFileSync(outputFile, JSON.stringify(info, null, 2));
  await ctx.close();
})();
