// douyin_fetch_data.js - 使用已保存的认证状态抓取数据
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const AUTH_FILE = path.join(__dirname, 'douyin_auth.json');

async function fetchAccountData(page, accountName) {
  try {
    // 导航到数据中心
    await page.goto('https://creator.douyin.com/creator-micro/data/content', { 
      waitUntil: 'networkidle', 
      timeout: 30000 
    });
    await page.waitForTimeout(3000);

    // 尝试获取概览数据
    // 抖音创作者后台的数据结构可能变化，这里提取常见的指标
    const data = {};
    
    // 尝试多种选择器
    const selectors = {
      playCount: [
        '[data-e2e="play-count"]',
        '.play-count', 
        'text=/播放.*?[0-9]+/',
      ],
      likeCount: [
        '[data-e2e="like-count"]', 
        '.like-count',
        'text=/点赞.*?[0-9]+/',
      ],
      commentCount: [
        '[data-e2e="comment-count"]',
        '.comment-count',
        'text=/评论.*?[0-9]+/',
      ],
      shareCount: [
        '[data-e2e="share-count"]',
        '.share-count',
        'text=/分享.*?[0-9]+/',
      ],
      followerCount: [
        '[data-e2e="follower-count"]',
        '.follower-count',
        'text=/粉丝.*?[0-9]+/',
      ],
    };

    for (const [key, selList] of Object.entries(selectors)) {
      for (const sel of selList) {
        try {
          const el = await page.locator(sel).first();
          if (await el.count() > 0) {
            const text = await el.textContent();
            const num = text.match(/[0-9.]+万?/);
            if (num) {
              data[key] = num[0];
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }
      if (!data[key]) data[key] = 'N/A';
    }

    // 尝试通过API接口获取数据（更可靠）
    try {
      const apiResponse = await page.evaluate(async () => {
        const res = await fetch('/creator-micro/data/statistics/overview', {
          headers: { 'Content-Type': 'application/json' }
        });
        return res.json();
      });
      console.log('API数据:', JSON.stringify(apiResponse, null, 2));
    } catch (e) {
      console.log('API方式未获取到数据，使用页面解析结果');
    }

    return data;
  } catch (e) {
    console.error(`获取${accountName}数据失败:`, e.message);
    return null;
  }
}

(async () => {
  if (!fs.existsSync(AUTH_FILE)) {
    console.log('未找到认证文件，请先运行 douyin_login.js');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ 
    viewport: { width: 1280, height: 800 },
    storageState: AUTH_FILE 
  });
  const page = await context.newPage();

  console.log('开始抓取数据...');
  const data = await fetchAccountData(page, '默认账号');
  
  if (data) {
    console.log('\n===== 抖音数据 =====');
    console.log(`播放量: ${data.playCount}`);
    console.log(`点赞: ${data.likeCount}`);
    console.log(`评论: ${data.commentCount}`);
    console.log(`分享: ${data.shareCount}`);
    console.log(`粉丝: ${data.followerCount}`);
    console.log('====================');
    
    // 输出JSON供后续处理
    console.log('\n---JSON_DATA---');
    console.log(JSON.stringify(data));
  }

  await browser.close();
})();
