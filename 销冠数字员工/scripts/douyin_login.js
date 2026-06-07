// douyin_login.js - 扫码登录抖音创作者后台，保存认证状态
const { chromium } = require('playwright');
const path = require('path');

const AUTH_FILE = path.join(__dirname, 'douyin_auth.json');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  // 抖音创作者后台
  await page.goto('https://creator.douyin.com/', { waitUntil: 'networkidle', timeout: 60000 });

  console.log('浏览器已打开，请扫码登录...');
  console.log('登录成功后脚本会自动保存状态并退出。');

  // 等待登录成功（检测页面跳转到创作者主页）
  try {
    // 等待URL包含 creator 且不再在登录页
    await page.waitForURL('**/creator.douyin.com/**', { timeout: 180000 });
    // 额外等待确保页面加载完成
    await page.waitForTimeout(5000);
    console.log('检测到登录成功，保存认证状态...');
  } catch (e) {
    console.log('登录超时或失败: ' + e.message);
    await browser.close();
    process.exit(1);
  }

  // 保存认证状态
  await context.storageState({ path: AUTH_FILE });
  console.log('认证状态已保存到: ' + AUTH_FILE);
  await browser.close();
})();
