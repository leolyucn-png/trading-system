#!/usr/bin/env python3
"""
🦁 爬虫学习实验 — 从 Level 1 到 Level 3
目标：小红书图片爬取
但我们会一步步走，先理解爬虫的原理
"""

import os, sys, json, time
import warnings
warnings.filterwarnings("ignore")

# ====================================================================
# LEVEL 1: 基础 — requests + BeautifulSoup
# 爬一个静态页面看看
# ====================================================================
def level1_basic_request():
    print("\n" + "=" * 60)
    print("📗 LEVEL 1: 基础 HTTP 请求")
    print("=" * 60)
    
    import requests
    from bs4 import BeautifulSoup
    
    # 挑一个简单的公开页面
    url = "https://httpbin.org/html"
    print(f"\n  1.1 GET 请求: {url}")
    
    resp = requests.get(url, timeout=10)
    print(f"     状态码: {resp.status_code}")
    print(f"     响应头 Content-Type: {resp.headers.get('content-type')}")
    
    # 用 BeautifulSoup 解析
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.string if soup.title else "无标题"
    print(f"     页面标题: {title}")
    
    # 找所有链接
    links = soup.find_all("a")
    print(f"     页面链接数: {len(links)}")
    for link in links[:3]:
        print(f"       → {link.get('href')}: {link.get_text(strip=True)}")
    
    # 1.2 看看请求头 — 为什么小红书会认出你不是浏览器
    print(f"\n  1.2 你当前的身份: ")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36"
    }
    resp2 = requests.get("https://httpbin.org/headers", headers=headers, timeout=10)
    data = resp2.json()
    print(f"     User-Agent 模拟浏览器: {'headers' in data}")
    
    return soup

# ====================================================================
# LEVEL 2: 动态页面 — Playwright 模拟真实浏览器
# ====================================================================
def level2_playwright_basics():
    print("\n" + "=" * 60)
    print("📙 LEVEL 2: 动态页面 — 用 Playwright 模拟浏览器")
    print("=" * 60)
    
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        # 启动浏览器（无头模式 = 不显示窗口）
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n  2.1 打开一个动态渲染的页面...")
        page.goto("https://httpbin.org/html")
        print(f"     页面标题: {page.title()}")
        print(f"     页面 URL: {page.url}")
        
        # 执行 JavaScript
        print("\n  2.2 在页面中执行 JavaScript...")
        dimension = page.evaluate("""() => {
            return {
                width: document.body.scrollWidth,
                height: document.body.scrollHeight,
                links: document.querySelectorAll('a').length
            }
        }""")
        print(f"     页面尺寸: {dimension['width']}x{dimension['height']}")
        print(f"     链接数: {dimension['links']}")
        
        # 截图 — 能看到页面长什么样
        screenshot_path = "/Users/lyu/.openclaw/workspace/level2_screenshot.png"
        page.screenshot(path=screenshot_path)
        print(f"\n  2.3 截图已保存: level2_screenshot.png")
        
        # 拦截网络请求（抓 API）
        print("\n  2.4 拦截网络请求，看看页面背后调了什么 API...")
        requests_log = []
        page.on("request", lambda req: requests_log.append({
            "url": req.url[:80],
            "method": req.method,
            "type": req.resource_type
        }))
        page.goto("https://httpbin.org/html")
        api_calls = [r for r in requests_log if "api" in r["url"].lower()]
        print(f"     共 {len(requests_log)} 个网络请求")
        print(f"     其中 API 请求: {len(api_calls)} 个")
        
        browser.close()
    
    print("\n  ✅ LEVEL 2 完成: 你现在有了一个自动化浏览器")
    return True

# ====================================================================
# LEVEL 3: 小红书 — 实战试探
# ====================================================================
def level3_xiaohongshu_probe():
    print("\n" + "=" * 60)
    print("📕 LEVEL 3: 小红书 — 反爬实战分析")
    print("=" * 60)
    
    import requests
    
    print("\n  🎯 目标: 搜索小红书 '平山书店' 的内容")
    print("  🔧 工具: requests (先试裸请求) + Playwright (浏览器模拟)")
    
    # 3.1 裸请求 — 看小红书返回什么
    print("\n  3.1 裸 HTTP 请求 (模拟浏览器 User-Agent)...")
    url = "https://www.xiaohongshu.com/search_result?keyword=平山书店"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.xiaohongshu.com/"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        print(f"     状态码: {resp.status_code}")
        print(f"     最终 URL: {resp.url}")
        print(f"     响应大小: {len(resp.text):,} 字符")
        
        # 检查是否返回的是小红书首页（未登录被重定向）
        if "login" in resp.url.lower():
            print("     ⚠️ 被重定向到登录页 (小红书要求登录)")
        
        # 看看返回的 HTML 里有什么
        if "平山" in resp.text:
            print("     ✅ HTML 中包含关键词 '平山'")
        else:
            print("     ❌ HTML 中无目标内容 (SPA 动态渲染)")
        
        # 检查 Set-Cookie
        cookies = dict(resp.cookies)
        print(f"     Cookies 数量: {len(cookies)}")
        
    except Exception as e:
        print(f"     ❌ 请求失败: {e}")
    
    # 3.2 小红书开放的公开接口探针
    print("\n  3.2 试探小红书开放的 API...")
    api_endpoints = [
        ("搜索建议", "https://www.xiaohongshu.com/api/sns/web/v1/search/result?keyword=平山书店&page=1&page_size=20"),
        ("笔记详情", "https://www.xiaohongshu.com/explore/任意ID"),
    ]
    for name, api_url in api_endpoints:
        try:
            r = requests.get(api_url, headers=headers, timeout=10)
            print(f"     [{r.status_code}] {name}: {api_url[:60]}...")
            if r.status_code == 200:
                print(f"       响应: {r.text[:100]}...")
        except Exception as e:
            print(f"     [ERR] {name}: {e}")
    
    # 3.3 用 Playwright 模拟真实浏览器访问
    print("\n  3.3 用 Playwright 模拟完整浏览器 (有 JS 引擎 + Cookie 管理)...")
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--disable-blink-features=AutomationControlled"  # 隐藏自动化痕迹
            ])
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                locale="zh-CN"
            )
            page = context.new_page()
            
            # 先访问首页拿 cookie
            print("     Step 1: 先访问首页拿 cookie...")
            page.goto("https://www.xiaohongshu.com", 
                      wait_until="domcontentloaded", timeout=15000)
            print(f"       首页状态: {page.url}")
            print(f"       标题: {page.title()}")
            
            # 截图看实际情况
            screenshot_path = "/Users/lyu/.openclaw/workspace/level3_xhs_home.png"
            page.screenshot(path=screenshot_path)
            print(f"       截图: level3_xhs_home.png")
            
            # 检查 login
            if "login" in page.url.lower():
                print(f"       ⚠️ 被弹登录页，说明小红书已检测到 automation 特征")
                
            browser.close()
    except Exception as e:
        print(f"     ❌ Playwright 访问失败: {e}")
    
    # 3.4 总结
    print("\n" + "=" * 60)
    print("📊 小红书反爬总结")
    print("=" * 60)
    print("""
    小红书有 3 道关卡:
    
    1️⃣ 登录墙
       - 未登录只能看首页
       - 内容页/搜索页需要登录态
    
    2️⃣ 签名校验 (X-s, X-t)
       - 每个 API 请求需要带签名参数
       - 签名算法由前端 JS 生成，混淆严重
       - 社区有逆向方案 (如 xhs_ 系列库)，但随时失效
    
    3️⃣ 自动化检测
       - 检测 headless 浏览器特征
       - 检测 WebDriver/navigator.webdriver
       - 检测异常请求频率
    
    学习建议:
    - 先从 ⽆反爬的公开 API 开始练习
    - 然后用 Playwright 操作需要登录的网站 (如微博、知乎)
    - 再挑战小红书这种高防护等级的平台
    """)
    
    print("\n  ✅ LEVEL 3 完成")

# ====================================================================
# 运行全部
# ====================================================================
if __name__ == "__main__":
    print("🦁 爬虫学习实验")
    print("=" * 60)
    print("我们会一步步深入:")
    print("  Level 1: requests + BeautifulSoup (基础 HTTP)")
    print("  Level 2: Playwright (动态页面 + API 拦截)")
    print("  Level 3: 小红书 (实战试探)")
    
    level1_basic_request()
    input("\n按 Enter 进入 Level 2...")
    level2_playwright_basics()
    input("\n按 Enter 进入 Level 3（小红书实战）...")
    level3_xiaohongshu_probe()
    
    print("\n" + "=" * 60)
    print("🏁 全部完成！总结见上方输出")
    print("=" * 60)
