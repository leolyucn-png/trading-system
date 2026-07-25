#!/usr/bin/env python3
"""
🦁 小红书数据采集 v3 (最终版)
直接从搜索 API 提取完整数据: 正文 + 互动 + 图片
"""
import os, json, time, datetime
import warnings
warnings.filterwarnings("ignore")

USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"
OUTPUT = "/Users/lyu/.openclaw/workspace/xhs_academic_data.json"

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

    raw_items = []

    def capture(resp):
        url = resp.url
        if "/api/sns/web/v1/search/notes" in url and resp.status == 200:
            try:
                body = resp.json()
                items = body.get("data", {}).get("items", [])
                print(f"  📦 搜索 API: +{len(items)} 条")
                raw_items.extend(items)
            except:
                pass

    page.on("response", capture)

    # 搜索
    print("🔎 搜索: 平山书店")
    try:
        page.goto("https://www.xiaohongshu.com/explore", 
                  wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
    except:
        pass

    page.goto(
        "https://www.xiaohongshu.com/search_result?keyword=平山书店",
        wait_until="domcontentloaded", timeout=20000
    )
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # 滚动到够 20 条
    scrolls = 0
    while len(raw_items) < 20 and scrolls < 5:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        scrolls += 1
        print(f"   滚动... ({len(raw_items)} 条)")

    browser.close()

# ---------- 整理数据 ----------
print(f"\n📊 数据整理中...")

posts = []
for item in raw_items[:20]:
    nid = item.get("id", "")
    nc = item.get("note_card", {})
    interact = nc.get("interact_info", {})
    user = nc.get("user", {})
    
    # 发帖时间
    ts = nc.get("time", 0) or nc.get("create_time", 0)
    time_str = ""
    if ts:
        try:
            time_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = str(ts)
    
    # 正文
    desc = nc.get("desc", "")
    if not desc:
        desc = nc.get("content", "")
    
    # 图片列表
    images = []
    for img in nc.get("image_list", []):
        info_list = img.get("info_list", [])
        best_url = ""
        for info in info_list:
            scene = info.get("image_scene", "")
            url = info.get("url", "")
            if scene == "WB_DFT" and url:
                best_url = url.split("?")[0]
            elif scene == "WB_PVT" and url and not best_url:
                best_url = url.split("?")[0]
        if not best_url and info_list:
            best_url = info_list[0].get("url", "").split("?")[0]
        if best_url:
            if best_url.startswith("//"):
                best_url = "https:" + best_url
            images.append(best_url)
    
    post = {
        "id": nid,
        "url": f"https://www.xiaohongshu.com/explore/{nid}",
        "title": nc.get("display_title", ""),
        "desc": desc,
        "time": time_str,
        "user": user.get("nickname", ""),
        "user_id": user.get("user_id", ""),
        "like_count": interact.get("liked_count", 0),
        "comment_count": interact.get("comment_count", 0),
        "collect_count": interact.get("collected_count", 0),
        "share_count": interact.get("share_count", 0),
        "type": nc.get("type", ""),
        "images": images,
        "tags": [t.get("name", "") for t in nc.get("tag_list", []) if t.get("name")],
        "top_comments": []  # 评论无法获取
    }
    posts.append(post)

# 保存
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

# 打印摘要
print(f"\n{'='*60}")
print(f"📊 采集结果 | 共 {len(posts)} 篇")
print(f"{'='*60}")

for p in posts:
    desc_preview = p['desc'][:80].replace('\n', ' ') if p['desc'] else '(无)'
    print(f"\n  📝 {p['title'][:35]}")
    print(f"     时间: {p['time']}  |  👤 {p['user']}")
    print(f"     👍 {p['like_count']}  💬 {p['comment_count']}  📌 {p['collect_count']}")
    print(f"     正文: {desc_preview}...")
    if p['tags']:
        print(f"     标签: {', '.join(p['tags'][:5])}")
    print(f"     图片: {len(p['images'])} 张")

print(f"\n{'='*60}")
print(f"💾 保存: xhs_academic_data.json")
print(f"🏁 完成!")
