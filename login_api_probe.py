#!/usr/bin/env python3
"""
小红书搜索：拦截真实 API 请求，看数据到底怎么来的
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

    # 拦截 API 响应
    api_responses = []
    
    def on_response(response):
        url = response.url
        # 只抓小红书自己的 API
        if "xiaohongshu.com/api" in url:
            status = response.status
            api_responses.append({
                "url": url[:120],
                "status": status,
                "content_type": response.headers.get("content-type", "")
            })
    
    page.on("response", on_response)

    # 去搜索页
    print("🔎 搜索: 平山书店")
    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=20000
    )
    
    # 等 SPA 加载 + API 返回
    print("⏳ 等待内容加载...")
    time.sleep(5)
    
    # 额外等 network idle
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    
    # 再等等，也许有延迟加载
    time.sleep(3)
    
    # 看 API 请求
    print(f"\n📡 捕获到 {len(api_responses)} 个 API 请求:\n")
    for i, req in enumerate(api_responses):
        print(f"  [{req['status']}] {req['content_type'][:30]}")
        print(f"     {req['url']}")
    
    # 如果有 200 的请求，看看具体内容
    for resp_info in api_responses:
        if resp_info["status"] == 200 and "json" in resp_info.get("content_type", ""):
            print(f"\n📦 试图读取 {resp_info['url'][:80]}...")
            # 不能直接读 response body, 需要额外处理
            print("     (需要 response 处理器)")
    
    # 看 DOM 里的内容
    print(f"\n🔍 DOM 分析:")
    dom_info = page.evaluate("""() => {
        // 看各种容器里的内容
        const containers = document.querySelectorAll('[class*="container"], [class*="list"], [class*="feed"], section, .note-item, [class*="search"]');
        const results = [];
        containers.forEach(el => {
            const text = el.innerText.trim();
            if (text.length > 20) {
                results.push({
                    tag: el.tagName,
                    class: el.className.substring(0, 60),
                    text: text.substring(0, 100),
                    imgs: el.querySelectorAll('img[src]').length,
                    children: el.children.length
                });
            }
        });
        return results.slice(0, 15);
    }""")
    
    print(f"  内容容器 ({len(dom_info)}):")
    for d in dom_info:
        print(f"    <{d['tag']} .{d['class']}>")
        print(f"      文字: {d['text'][:80]}...")
        print(f"      图片: {d['imgs']} | 子节点: {d['children']}")
    
    # 看看 visible 图片的 URL
    print(f"\n🖼️ 页面可见图片:")
    imgs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('img'))
            .filter(img => img.src && img.src.startsWith('http') && img.offsetWidth > 0)
            .map(img => ({
                src: img.src.substring(0, 120),
                w: img.offsetWidth,
                h: img.offsetHeight,
                alt: (img.alt || '').substring(0, 40)
            }))
            .slice(0, 5)
    }""")
    for img in imgs:
        print(f"    [{img['w']}x{img['h']}] {img['src']}")
        if img['alt']:
            print(f"      alt: {img['alt']}")
    
    # 截图
    page.screenshot(path="/Users/lyu/.openclaw/workspace/login_api_probe.png", full_page=True)
    
    browser.close()
    print("\n✅ 完成")
