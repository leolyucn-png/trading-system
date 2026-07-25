#!/usr/bin/env python3
"""
🦁 小红书爬虫完整版
登录 → 搜索平山书店 → 拦截 API JSON → 下载图片
"""
import os, json, time, re
import urllib.request
import warnings
warnings.filterwarnings("ignore")

USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"
OUTPUT_DIR = "/Users/lyu/.openclaw/workspace/xhs_images"

os.makedirs(OUTPUT_DIR, exist_ok=True)

from playwright.sync_api import sync_playwright

# ---------- 1. 启动浏览器 ----------
with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        locale="zh-CN"
    )
    page = browser.pages[0]

    # ---------- 2. 拦截 API response body ----------
    api_results = []

    def handle_response(response):
        url = response.url
        # 只抓搜索结果的 API
        if "/api/sns/web/v1/search/result" in url and response.status == 200:
            try:
                body = response.json()
                api_results.append({
                    "url": url,
                    "data": body
                })
                notes = body.get("data", {}).get("items", [])
                print(f"\n  📦 搜索 API 返回: {len(notes)} 条笔记")
            except:
                pass
        
        # 也抓搜索 recommend API
        if "/api/sns/web/v1/search/recommend" in url and response.status == 200:
            try:
                body = response.json()
                api_results.append({
                    "url": url,
                    "data": body
                })
            except:
                pass

    page.on("response", handle_response)

    # ---------- 3. 打开搜索页 ----------
    print("🔎 打开搜索页: 平山书店")
    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=20000
    )

    # ---------- 4. 等用户扫码 ----------
    print("⏳ 等待加载...")
    time.sleep(3)

    # 检查是否弹出登录框
    need_login = page.evaluate("""() => {
        return document.querySelector('[class*="login"]') !== null
    }""")

    if need_login:
        print("\n📌 检测到登录弹窗，请在浏览器中扫码登录")
        print("   登录完成后回到这里继续...")
        
        # 等登录框消失 (轮询)
        for i in range(60):
            time.sleep(2)
            still_login = page.evaluate("""() => {
                return document.querySelector('[class*="login"]') !== null
            }""")
            if not still_login:
                print("   ✅ 登录成功！")
                break
            if i % 10 == 0:
                print(f"   等待中... ({i*2}s)")
        else:
            print("   ⚠️ 等待超时，但继续尝试...")
        
        # 重新加载搜索页
        print("🔄 重新加载搜索页...")
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=平山书店",
            wait_until="domcontentloaded", timeout=20000
        )
        time.sleep(5)
    else:
        print("   ✅ 已登录，直接加载")

    # 等 network idle
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass
    time.sleep(3)

    # ---------- 5. 处理搜索结果 ----------
    print(f"\n{'='*60}")
    print(f"📊 搜索结果")
    print(f"{'='*60}")

    if api_results:
        for result in api_results:
            data = result["data"]
            notes = data.get("data", {}).get("items", [])
            
            for note in notes:
                note_id = note.get("id", "unknown")
                display_title = note.get("display_title", "") or note.get("note_card", {}).get("display_title", "")
                user = note.get("user", {}) or note.get("note_card", {}).get("user", {})
                nickname = user.get("nickname", "unknown")
                
                # 提取图片 URL
                image_list = note.get("image_list", []) or note.get("note_card", {}).get("image_list", [])
                image_urls = [img.get("url", img.get("original", "")) for img in image_list if img.get("url") or img.get("original")]
                
                # 也可能在 note_card 的 image_list 里
                if not image_list:
                    note_card = note.get("note_card", {})
                    img_list = note_card.get("image_list", [])
                    image_urls = [img.get("url_default", "") or img.get("url", "") for img in img_list]
                
                print(f"\n  📝 {display_title[:50] if display_title else '无标题'}")
                print(f"     👤 {nickname}")
                print(f"     🆔 {note_id}")
                print(f"     🖼️ {len(image_urls)} 张图")
                
                # 下载图片
                for idx, img_url in enumerate(image_urls):
                    if not img_url:
                        continue
                    # 转成高清图 (去掉末尾的参数)
                    clean_url = re.sub(r'[?&].*', '', img_url)
                    if not clean_url.startswith('http'):
                        clean_url = "https:" + clean_url if clean_url.startswith("//") else clean_url
                    
                    filename = f"{note_id}_{idx+1}.jpg"
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    
                    try:
                        req = urllib.request.Request(
                            clean_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                                "Referer": "https://www.xiaohongshu.com/"
                            }
                        )
                        with urllib.request.urlopen(req, timeout=15) as r:
                            with open(filepath, "wb") as f:
                                f.write(r.read())
                        print(f"     ✅ 已下载: {filename} ({os.path.getsize(filepath)//1024}KB)")
                    except Exception as e:
                        print(f"     ❌ 下载失败: {e}")
    else:
        print("  ⚠️ 没有捕获到搜索 API 响应")
        print("  尝试从页面直接提取...")
        
        # 直接从 DOM 提取
        page_data = page.evaluate("""() => {
            const imgs = document.querySelectorAll('img');
            return Array.from(imgs)
                .filter(img => img.src && img.src.includes('xhscdn.com'))
                .map(img => img.src)
                .slice(0, 20);
        }""")
        
        if page_data:
            print(f"  从 DOM 提取到 {len(page_data)} 张图片")
            for idx, img_url in enumerate(page_data):
                clean_url = re.sub(r'[?&].*', '', img_url)
                filename = f"dom_extract_{idx+1}.jpg"
                filepath = os.path.join(OUTPUT_DIR, filename)
                try:
                    req = urllib.request.Request(
                        clean_url,
                        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.xiaohongshu.com/"}
                    )
                    with urllib.request.urlopen(req, timeout=15) as r:
                        with open(filepath, "wb") as f:
                            f.write(r.read())
                    print(f"     ✅ 已下载: {filename} ({os.path.getsize(filepath)//1024}KB)")
                except Exception as e:
                    print(f"     ❌ {e}")

    # ---------- 6. 打印 API 原始数据 ----------
    if api_results:
        raw_path = "/Users/lyu/.openclaw/workspace/xhs_search_raw.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(api_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 原始 API 数据已保存: xhs_search_raw.json")

    # 截图留念
    page.screenshot(path="/Users/lyu/.openclaw/workspace/xhs_final.png", full_page=True)

    browser.close()

    print(f"\n{'='*60}")
    print(f"🏁 完成!")
    print(f"{'='*60}")
    print(f"   图片目录: xhs_images/")
    print(f"   API 数据: xhs_search_raw.json")
    print(f"   截图: xhs_final.png")
