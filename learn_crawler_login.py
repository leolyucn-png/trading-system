#!/usr/bin/env python3
"""
🦁 爬虫学习 — 登录后能做什么？
用一个真实的 Playwright 登录流程来展示
"""

import os, json, time
import warnings
warnings.filterwarnings("ignore")

COOKIE_FILE = "/Users/lyu/.openclaw/workspace/xhs_cookies.json"
USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"

def save_cookies(cookies, path=COOKIE_FILE):
    with open(path, "w") as f:
        json.dump(cookies, f)
    print(f"   💾 Cookies 已保存 ({len(cookies)} 条)")

def load_cookies(path=COOKIE_FILE):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def demo_login_flow():
    """
    演示 Playwright 的两种登录方式
    """
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("🦁 登录流程示范")
    print("=" * 60)

    with sync_playwright() as p:
        # 用持久化浏览器上下文 (不会每次都清 cookie)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  # 显示浏览器窗口，方便你手动登
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )
        page = browser.pages[0]
        
        # Step 1: 看有没有已有登录态
        print("\n📌 Step 1: 检查是否有已保存的登录态...")
        page.goto("https://www.xiaohongshu.com/explore", 
                  wait_until="domcontentloaded", timeout=15000)
        
        is_logged_in = False
        try:
            page.wait_for_selector('div[class*="user"]', timeout=3000)
            # 检查有没有用户头像/昵称元素
            user_element = page.query_selector('div[class*="avatar"], span[class*="nickname"]')
            if user_element:
                is_logged_in = True
                print("   ✅ 已有登录态！")
        except:
            pass
        
        if not is_logged_in:
            print("   ⚠️ 未登录。浏览器窗口已打开，请手动登录 →")
            print("     1. 浏览器会自动打开小红书")
            print("     2. 扫码或用手机号登录")
            print("     3. 登录成功后，回到这里按 Enter 继续")
            input("\n     按 Enter 继续...")
            
            # 确认是否真的登录了
            page.goto("https://www.xiaohongshu.com/explore",
                      wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            
            page.screenshot(path="/Users/lyu/.openclaw/workspace/login_check.png")
            print("   📸 截图已保存: login_check.png")
        
        # Step 2: 登录后试试搜索
        print("\n📌 Step 2: 登录后搜索平山书店...")
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=平山书店",
            wait_until="domcontentloaded", timeout=15000
        )
        time.sleep(3)
        
        # 截图看搜索结果
        search_screenshot = "/Users/lyu/.openclaw/workspace/login_search_result.png"
        page.screenshot(path=search_screenshot, full_page=True)
        print(f"   📸 搜索结果截图: login_search_result.png")
        
        # 看页面里有什么文字内容
        body_text = page.evaluate("document.body.innerText")
        print(f"     页面文字量: {len(body_text)} 字符")
        
        # 看图片
        imgs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('img'))
                .map(img => ({
                    src: img.src.substring(0, 80),
                    alt: img.alt || img.getAttribute('title') || ''
                }))
                .filter(img => img.src && img.src.startsWith('http'))
                .slice(0, 5)
        }""")
        print(f"     页面图片数 (前5):")
        for img in imgs:
            print(f"       · {img['src']}")
        
        # Step 3: 保存 cookies 给后续使用
        cookies = browser.cookies()
        save_cookies(cookies)
        
        browser.close()

def demo_use_saved_cookies():
    """
    用保存的 cookies 做自动请求 (不用开浏览器)
    演示如何绕过登录墙直接访问 API
    """
    import requests
    
    print("\n" + "=" * 60)
    print("🦁 用 Cookies 做自动请求 (Playwright 关闭后仍可用)")
    print("=" * 60)
    
    cookies = load_cookies()
    if not cookies:
        print("   ❌ 没有保存的 cookies，请先运行登录流程")
        return
    
    # 把 cookies 转成 dict 格式
    cookies_dict = {c["name"]: c["value"] for c in cookies}
    print(f"   📦 已加载 {len(cookies_dict)} 个 cookie")
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.xiaohongshu.com/"
    }
    
    # 试试搜索页面
    print("\n  1️⃣ 搜索页面 (带登录态):")
    search_url = "https://www.xiaohongshu.com/search_result?keyword=平山书店"
    r = requests.get(search_url, headers=headers, cookies=cookies_dict, timeout=15)
    print(f"     状态码: {r.status_code}")
    print(f"     最终 URL: {r.url}")
    
    if "平山" in r.text:
        print("     ✅ 页面包含搜索关键词!")
    elif "login" in r.url.lower():
        print("     ❌ 仍然被重定向到登录页")
    else:
        # 看看返回了什么
        print(f"     响应大小: {len(r.text):,} 字符")
    
    # 试试搜索 API
    print("\n  2️⃣ 搜索 API (带登录态):")
    api_url = "https://www.xiaohongshu.com/api/sns/web/v1/search/result"
    params = {"keyword": "平山书店", "page": 1, "page_size": 20, "sort": "general"}
    r = requests.get(api_url, headers=headers, cookies=cookies_dict, 
                     params=params, timeout=15)
    print(f"     状态码: {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"     ✅ API 返回 JSON! 数据结构: {list(data.keys())}")
        except:
            print(f"     响应 (前100字): {r.text[:100]}")
    else:
        print(f"     响应: {r.text[:100]}")
        print("     ⚠️ 即使是登录状态，API 仍然需要签名参数")
    
    print("\n" + "=" * 60)
    print("📊 结论")
    print("=" * 60)
    print("""
    登录后:
    ✅ 能通过 Playwright 浏览器正常浏览和搜索
    ✅ 能看到图片、内容等（跟真人用户一样）
    ❌ requests 发 API 还是被挡 (缺 X-s, X-t 签名)
    ❌ requests 搜页面可能还是空壳 (SPA 渲染)
    
    所以正确的路径是:
    用 Playwright 全程驱动浏览器 → 
    它自动执行 JS 生成签名 →
    你在浏览器里操作就能拿到数据
    
    真正的爬虫方案 = Playwright + 登录态 + 页面解析
    不需要逆向 API 签名，让浏览器自己干活就行。
    代价是: 慢 (每个操作都要等页面渲染)
    """)

if __name__ == "__main__":
    print("🦁 爬虫学习: 登录实战")
    print("1) 运行登录流程 (会打开浏览器)")
    print("2) 用已保存的 cookies 测试 (不开浏览器)")
    print()
    
    choice = input("请选择 (1 或 2): ").strip()
    
    if choice == "1":
        demo_login_flow()
    elif choice == "2":
        demo_use_saved_cookies()
    else:
        print("无效选择")
