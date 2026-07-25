#!/usr/bin/env python3
"""
🦁 v4 — 从首页搜索框输入关键词触发搜索，绕过直接导航的限流
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
                if items:
                    raw_items.extend(items)
                    print(f"  📦 +{len(items)} 条 (累计 {len(raw_items)})")
            except:
                pass

    page.on("response", capture)

    # 打开首页
    print("📌 打开小红书首页...")
    page.goto("https://www.xiaohongshu.com/explore", 
              wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)

    # 用搜索框输入
    print("🔍 在搜索框输入: 平山书店")
    try:
        # 找搜索框
        search_input = page.locator('input[placeholder*="搜索"], input[class*="search"], input[type="text"]').first
        search_input.click()
        time.sleep(1)
        search_input.fill("平山书店")
        time.sleep(1)
        search_input.press("Enter")
        print("   ✅ 已提交搜索")
    except Exception as e:
        print(f"   ⚠️ 搜索框方式失败: {e}")
        # fallback: 直接导航
        print("   → 改用直接导航")
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=平山书店",
            wait_until="domcontentloaded", timeout=20000
        )

    # 等待结果
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # 滚动加载更多
    scrolls = 0
    while len(raw_items) < 20 and scrolls < 8:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        scrolls += 1
        print(f"   滚动... ({len(raw_items)} 条)")

    browser.close()

# 整理
if not raw_items:
    print("\n❌ 未捕获到数据，小红书拒绝访问")
    # 尝试从已有数据恢复
    fallback = "/Users/lyu/.openclaw/workspace/xhs_search_raw.json"
    if os.path.exists(fallback):
        print(f"   但上一次有数据，尝试恢复...")
    print("\n🏁 被拒绝，采集失败")
    exit(1)

print(f"\n📊 整理 {len(raw_items[:20])} 条数据...")
posts = []
for item in raw_items[:20]:
    nid = item.get("id", "")
    nc = item.get("note_card", {})
    interact = nc.get("interact_info", {})
    user = nc.get("user", {})
    
    ts = nc.get("time", 0) or nc.get("create_time", 0)
    time_str = ""
    if ts:
        try:
            time_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = str(ts)
    
    desc = nc.get("desc", "") or nc.get("content", "")
    
    images = []
    for img in nc.get("image_list", []):
        for info in img.get("info_list", []):
            url = info.get("url", "")
            if url:
                if url.startswith("//"):
                    url = "https:" + url
                images.append(url.split("?")[0])
                break
    
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
        "images": images[:5],
        "tags": [t.get("name", "") for t in nc.get("tag_list", [])[:5] if t.get("name")],
        "top_comments": []
    }
    posts.append(post)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

# 打印
print(f"\n{'='*60}")
print(f"📊 共 {len(posts)} 篇帖子")
print(f"{'='*60}")
for p in posts:
    d = p['desc'][:70].replace('\n', ' ') if p['desc'] else '(无正文)'
    print(f"\n  [{p['time']}] {p['title'][:35]}")
    print(f"      👤 {p['user']}  👍 {p['like_count']}  💬 {p['comment_count']}")
    print(f"      {d}")

print(f"\n💾 保存: xhs_academic_data.json")
