const { chromium } = require('playwright');
const path = require('path');

const userDataDir = path.join(__dirname, 'douyin_profile');

(async () => {
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    viewport: { width: 1280, height: 800 }
  });
  const page = await ctx.newPage();
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 60000 });
  
  console.log('浏览器已打开，请扫码登录...');
  console.log('登录成功后浏览器会自动关闭。');

  // Wait for login - check every 3 seconds for up to 3 minutes
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(3000);
    const text = await page.evaluate(() => document.body.innerText);
    if (!text.includes('扫码登录') && !text.includes('验证码登录')) {
      console.log('检测到登录成功！');
      await page.waitForTimeout(3000);
      break;
    }
  }
  
  console.log('认证状态已保存到: ' + userDataDir);
  await ctx.close();
})();
