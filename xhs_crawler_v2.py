#!/usr/bin/env python3
"""
🦁 最终版 — 小红书爬虫
拦截 /search/notes API → 提取笔记 → 下载图片
"""
import os, json, time, re, urllib.request
import warnings
warnings.filterwarnings("ignore")

USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"
OUTPUT_DIR = "/Users/lyu/.openclaw/workspace/xhs_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

    all_notes = []

    def on_response(resp):
        url = resp.url
        if "/api/sns/web/v1/search/notes" in url and resp.status == 200:
            try:
                body = resp.json()
                items = body.get("data", {}).get("items", [])
                if items:
                    all_notes.extend(items)
                    print(f"  📦 搜索结果: +{len(items)} 条笔记 (累计 {len(all_notes)})")
            except:
                pass

    page.on("response", on_response)

    # 打开搜索
    print("🔎 搜索: 平山书店")
    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=20000
    )

    # 等所有 API 回来
    print("⏳ 等待数据加载...")
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # ✅ 处理数据
    print(f"\n{'='*60}")
    print(f"📊 共捕获 {len(all_notes)} 条笔记，开始下载图片")
    print(f"{'='*60}")

    download_count = 0
    for note in all_notes:
        note_card = note.get("note_card", {})
        note_id = note.get("id", "unknown")
        title = note_card.get("display_title", "无标题")
        user = note_card.get("user", {})
        nickname = user.get("nickname", "未知")

        # 提取图片
        image_list = note_card.get("image_list", [])
        urls = []
        for img in image_list:
            # 取最高清版本
            info_list = img.get("info_list", [])
            # 找 WB_DFT 或 WB_PVT
            best_url = ""
            for info in info_list:
                scene = info.get("image_scene", "")
                url = info.get("url", "")
                if scene == "WB_DFT" and url:
                    best_url = url
                elif scene == "WB_PVT" and url and not best_url:
                    best_url = url
            if not best_url and info_list:
                best_url = info_list[0].get("url", "")

            if best_url:
                # 转 https
                if best_url.startswith("//"):
                    best_url = "https:" + best_url
                elif best_url.startswith("http://"):
                    best_url = best_url.replace("http://", "https://")
                urls.append(best_url.split("?")[0])  # 去掉参数

        print(f"\n  📝 {title[:50]}")
        print(f"     👤 {nickname}  🆔 {note_id}  🖼️ {len(urls)} 张")

        for idx, img_url in enumerate(urls):
            filename = f"{note_id}_{idx+1}.jpg"
            filepath = os.path.join(OUTPUT_DIR, filename)

            try:
                req = urllib.request.Request(
                    img_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Referer": "https://www.xiaohongshu.com/"
                    }
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    with open(filepath, "wb") as f:
                        f.write(r.read())
                print(f"     ✅ {filename} ({os.path.getsize(filepath)//1024}KB)")
                download_count += 1
            except Exception as e:
                print(f"     ❌ {filename}: {e}")

    # 保存元数据
    meta_path = "/Users/lyu/.openclaw/workspace/xhs_notes_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(all_notes, f, ensure_ascii=False, indent=2)

    page.screenshot(path="/Users/lyu/.openclaw/workspace/xhs_final2.png", full_page=True)
    browser.close()

    print(f"\n{'='*60}")
    print(f"🏁 完成!")
    print(f"{'='*60}")
    print(f"   笔记数: {len(all_notes)}")
    print(f"   下载图片: {download_count} 张")
    print(f"   图片目录: xhs_images/")
    print(f"   元数据: xhs_notes_meta.json")
    print(f"   截图: xhs_final2.png")
