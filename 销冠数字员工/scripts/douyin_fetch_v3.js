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

  // Go to creator home
  await page.goto('https://creator.douyin.com/creator-micro/home', { 
    waitUntil: 'networkidle', timeout: 30000 
  });
  await page.waitForTimeout(5000);

  // Get account name
  const accountName = await page.evaluate(() => {
    const el = document.querySelector('[class*="name"], [class*="nickname"], [class*="title"]');
    return el ? el.textContent.trim() : '未知账号';
  });
  console.log('Account:', accountName);

  // Get stats from the home page
  const homeStats = await page.evaluate(() => {
    const result = {};
    const text = document.body.innerText;
    
    // Extract follower count
    const fanMatch = text.match(/粉丝\s*(\d[\d,.]*万?)/);
    if (fanMatch) result.fans = fanMatch[1];
    
    // Extract like count
    const likeMatch = text.match(/获赞\s*(\d[\d,.]*万?)/);
    if (likeMatch) result.likes = likeMatch[1];
    
    // Extract following count
    const followMatch = text.match(/关注\s*(\d[\d,.]*万?)/);
    if (followMatch) result.following = followMatch[1];

    // Check for data period
    const periodMatch = text.match(/统计周期[：:]\s*(.+?)[\s（]/);
    if (periodMatch) result.period = periodMatch[1];

    // Check for latest video info
    const videoMatch = text.match(/最新作品[\s\S]*?(\d+)[\s\S]*?(?:发布|条)/);
    const noVideo = text.includes('未发布新作品');
    result.hasVideos = !noVideo;

    return result;
  });

  console.log('Home stats:', JSON.stringify(homeStats));

  // Click "数据中心" then "账号总览" for detailed data
  try {
    // Click "数据中心" in sidebar
    await page.click('text="数据中心"');
    await page.waitForTimeout(3000);
    
    // Try to click "账号总览"
    const overview = page.locator('text="账号总览"').first();
    if (await overview.count() > 0) {
      await overview.click();
      await page.waitForTimeout(5000);
    }

    // Get detailed data
    const detailStats = await page.evaluate(() => {
      const result = {};
      const text = document.body.innerText;
      
      // Recent 7-day data
      const sevenDaySection = text.match(/近7[日天][\s\S]*?(?=近30|$)/);
      if (sevenDaySection) {
        const section = sevenDaySection[0];
        
        // Play count
        const playMatch = section.match(/播放[量数]*\s*(\d[\d,.]*万?)/);
        if (playMatch) result.plays7d = playMatch[1];
        
        // Like count
        const likeMatch = section.match(/点赞[量数]*\s*(\d[\d,.]*万?)/);
        if (likeMatch) result.likes7d = likeMatch[1];
        
        // Comments
        const commentMatch = section.match(/评论[量数]*\s*(\d[\d,.]*万?)/);
        if (commentMatch) result.comments7d = commentMatch[1];
        
        // Shares
        const shareMatch = section.match(/分享[量数]*\s*(\d[\d,.]*万?)/);
        if (shareMatch) result.shares7d = shareMatch[1];
        
        // New followers
        const fanMatch = section.match(/新增粉丝\s*(\d[\d,.]*万?)/);
        if (fanMatch) result.newFans7d = fanMatch[1];
      }
      
      return result;
    });

    console.log('Detail stats:', JSON.stringify(detailStats));
    Object.assign(homeStats, detailStats);
  } catch (e) {
    console.log('Detail fetch error:', e.message);
  }

  // Save to JSON file
  homeStats.account = accountName;
  homeStats.timestamp = new Date().toISOString();
  homeStats.url = page.url();
  
  fs.writeFileSync(outputFile, JSON.stringify(homeStats, null, 2));
  console.log('Data saved to:', outputFile);
  console.log('\n---FINAL_DATA---');
  console.log(JSON.stringify(homeStats));

  await ctx.close();
})();
