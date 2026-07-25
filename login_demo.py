#!/usr/bin/env python3
"""
🦁 小红书登录实验
浏览器会弹出 → 你手机扫码登录 → 然后自动搜平山书店
"""
import os, json, time, sys
import warnings
warnings.filterwarnings("ignore")

COOKIE_FILE = "/Users/lyu/.openclaw/workspace/xhs_cookies.json"
USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 持久化上下文 — cookies 会保存在目录里，下次不用重登
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        locale="zh-CN"
    )
    page = browser.pages[0]

    # 1. 先去 explore 页
    print("🔍 正在打开小红书...")
    page.goto("https://www.xiaohongshu.com/explore", 
              wait_until="domcontentloaded", timeout=15000)
    time.sleep(2)

    # 2. 检查是否已登录
    try:
        page.wait_for_selector('[class*="user"],[class*="avatar"],[class*="login"]', timeout=3000)
        current_url = page.url
        print(f"📌 当前页面: {current_url}")
        
        # 简单判断：看URL里有没有login
        if "login" in current_url.lower():
            print("❌ 未登录，请在浏览器中手动登录")
            print("   → 扫码或用手机号登录")
            print("   → 登录后回来这里会继续进行")
        else:
            print("✅ 已检测到登录态")
    except:
        print("⚠️ 登录状态不确定，请在浏览器中确认")
    
    # 3. 等用户确认已登录
    input("\n✋ 登录完成后，按 Enter 继续搜索...")
    
    # 4. 搜索平山书店
    print("\n🔎 正在搜索: 平山书店")
    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=15000
    )
    time.sleep(3)
    
    # 5. 截图看结果
    search_screenshot = "/Users/lyu/.openclaw/workspace/login_result.png"
    page.screenshot(path=search_screenshot, full_page=True)
    print(f"📸 截图保存: login_result.png")
    
    # 6. 看看页面上有什么
    body_text = page.evaluate("document.body.innerText")
    print(f"📝 页面文字量: {len(body_text)} 字符")
    
    # 7. 提取图片链接
    imgs = page.evaluate("""() => {
        const imgs = document.querySelectorAll('img');
        const results = [];
        imgs.forEach(img => {
            if (img.src && img.src.startsWith('http')) {
                results.push({
                    src: img.src.length > 100 ? img.src.substring(0, 100) + '...' : img.src,
                    alt: img.alt || '',
                    width: img.naturalWidth,
                    height: img.naturalHeight
                });
            }
        });
        return results.slice(0, 10);
    }""")
    print(f"🖼️ 页面图片 (前10张):")
    for i, img in enumerate(imgs):
        print(f"   {i+1}. [{img['width']}x{img['height']}] {img['src']}")
    
    # 8. 保存 cookies
    cookies = browser.cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    print(f"\n💾 Cookies 已保存 ({len(cookies)} 条)")
    
    # 9. 关闭浏览器
    browser.close()
    
    print("\n" + "=" * 60)
    print("✅ 实验完成!")
    print("=" * 60)
    print(f"   截图: login_result.png")
    print(f"   Cookies: xhs_cookies.json")
