#!/usr/bin/env python3
"""
精确拦截：打印所有小红书业务 API 的 URL 和 body 前 500 字
"""
import os, json, time
import warnings
warnings.filterwarnings("ignore")

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

    captured = []

    def on_response(resp):
        url = resp.url
        # 只抓 edith 业务 API (过滤掉 as/apm 等安全/监控API)
        if "edith.xiaohongshu.com/api" in url and resp.status == 200:
            try:
                body = resp.json()
                captured.append({"url": url, "body_snippet": json.dumps(body, ensure_ascii=False)[:500]})
                print(f"\n  ✅ edith API: {url.split('?')[0]}")
                print(f"     body: {json.dumps(body, ensure_ascii=False)[:200]}")
            except:
                pass

    page.on("response", on_response)

    # 先去首页看看登录状态
    print("📌 先去首页...")
    page.goto("https://www.xiaohongshu.com/explore", 
              wait_until="domcontentloaded", timeout=15000)
    time.sleep(5)

    # 检查登录
    login_check = page.evaluate("""() => {
        const loginEl = document.querySelector('[class*="login"], .login-container');
        return {
            hasLoginEl: !!loginEl,
            loginText: loginEl ? loginEl.innerText.substring(0, 100) : '',
            url: location.href
        }
    }""")
    print(f"\n📋 首页状态:")
    print(f"   URL: {login_check['url']}")
    print(f"   有登录弹窗: {login_check['hasLoginEl']}")
    if login_check['hasLoginEl']:
        print(f"   弹窗文字: {login_check['loginText']}")

    # 如果首页就是登录弹窗，那先让用户登录
    if login_check['hasLoginEl']:
        print("\n⚠️ 请扫码登录，完成后按 Enter")
        input()
        time.sleep(3)
        
        # 重新检查
        login_check2 = page.evaluate("""() => {
            const loginEl = document.querySelector('[class*="login"], .login-container');
            return { hasLoginEl: !!loginEl }
        }""")
        print(f"   登录后: {'✅ 已登录' if not login_check2['hasLoginEl'] else '❌ 仍有登录弹窗'}")

    # 清掉之前的请求记录
    captured.clear()
    
    # 搜平山书店
    print(f"\n{'='*60}")
    print(f"🔎 搜索平山书店 (清空拦截记录后重新捕获)")
    print(f"{'='*60}")
    
    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=20000
    )
    time.sleep(8)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # 打印全部捕获的 API
    print(f"\n\n📡 共捕获 {len(captured)} 个 edith API:")
    for i, c in enumerate(captured):
        print(f"\n  [{i+1}] {c['url'][:100]}")
        print(f"      {c['body_snippet'][:300]}")
    
    # 截图
    page.screenshot(path="/Users/lyu/.openclaw/workspace/xhs_probe2.png", full_page=True)
    
    browser.close()
    print(f"\n✅ 完成，截图: xhs_probe2.png")
