#!/usr/bin/env python3
"""
深扒登录后的页面内容
"""
import os, json, time
import warnings
warnings.filterwarnings("ignore")

COOKIE_FILE = "/Users/lyu/.openclaw/workspace/xhs_cookies.json"
USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        locale="zh-CN"
    )
    page = browser.pages[0]

    # 1. 看看当前登录状态
    print("=" * 60)
    print("📋 页面状态诊断")
    print("=" * 60)
    
    page.goto("https://www.xiaohongshu.com/explore", 
              wait_until="domcontentloaded", timeout=15000)
    time.sleep(3)
    
    print(f"\n  URL: {page.url}")
    print(f"  标题: {page.title()}")
    
    info = page.evaluate("""() => {
        return {
            url: window.location.href,
            title: document.title,
            hasLogin: !!document.querySelector('[class*="user"],[class*="avatar"],[class*="login-btn"]'),
            bodyTextLength: document.body.innerText.length,
            imgCount: document.querySelectorAll('img').length,
            visibleImgCount: document.querySelectorAll('img[src]').length,
            scripts: document.querySelectorAll('script').length,
            cookies: document.cookie.length > 0
        }
    }""")
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    # 2. 看看首页能不能看到内容
    print(f"\n  📝 页面可见文字 (前300字):")
    body_text = page.evaluate("document.body.innerText")
    print(f"  {body_text[:300]}")
    
    # 3. 如果首页正常，搜平山书店
    if "login" not in page.url.lower():
        print("\n" + "=" * 60)
        print("🔎 搜索平山书店")
        print("=" * 60)
        
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=平山书店&source=web_search_result_notes",
            wait_until="domcontentloaded", timeout=20000
        )
        time.sleep(5)  # 等 SPA 渲染
        
        print(f"\n  URL: {page.url}")
        print(f"  标题: {page.title()}")
        
        # 看有没有搜索结果
        has_results = page.evaluate("""() => {
            // 多种可能的选择器
            const selectors = [
                '.note-item', '.feeds-page', '.search-result',
                '[class*="note"]', '[class*="feed"]', '[class*="card"]',
                'section', 'main'
            ];
            for (const sel of selectors) {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) return {selector: sel, count: els.length, html: els[0].innerHTML.substring(0, 200)};
            }
            return null;
        }""")
        
        print(f"\n  搜索结果节点:")
        if has_results:
            print(f"    选择器: {has_results['selector']}")
            print(f"    数量: {has_results['count']}")
            print(f"    HTML片段: {has_results['html']}")
        else:
            print("    未找到标准搜索结果容器")
        
        # 看所有 img
        imgs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img'))
                .filter(img => img.src && img.src.startsWith('http'))
                .map(img => ({
                    src: img.src.substring(0, 100),
                    alt: (img.alt || '').substring(0, 50),
                    w: img.naturalWidth || img.width,
                    h: img.naturalHeight || img.height,
                    visible: img.offsetWidth > 0 && img.offsetHeight > 0
                }))
                .slice(0, 5)
        }""")
        print(f"\n  🖼️ 图片 ({len(imgs)}):")
        for img in imgs:
            print(f"     [{img['w']}x{img['h']}{' visible' if img['visible'] else ' hidden'}] {img['src']}")
        
        page.screenshot(path="/Users/lyu/.openclaw/workspace/login_deep.png", full_page=True)
    
    browser.close()
    print("\n✅ 诊断完成")
