#!/usr/bin/env python3
"""
🦁 小红书数据采集 — 学术研究用途
平山书店: 帖子详情 + 前10评论 + 互动数据
目标: 20条帖子
"""
import os, json, time, re
import warnings
warnings.filterwarnings("ignore")

USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"
OUTPUT = "/Users/lyu/.openclaw/workspace/xhs_academic_data.json"

from playwright.sync_api import sync_playwright

all_posts = []  # 最终数据

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        locale="zh-CN"
    )
    page = browser.pages[0]

    # ---------- 第一步: 搜索获取 20 个 note_id ----------
    print("=" * 60)
    print("Step 1: 搜索平山书店，获取笔记 ID")
    print("=" * 60)

    note_ids = []

    def capture_search(resp):
        url = resp.url
        if "/api/sns/web/v1/search/notes" in url and resp.status == 200:
            try:
                body = resp.json()
                items = body.get("data", {}).get("items", [])
                for item in items:
                    nid = item.get("id", "")
                    if nid and nid not in note_ids and len(note_ids) < 20:
                        note_ids.append(nid)
                print(f"   已获取 {len(note_ids)} 个 ID")
            except:
                pass

    page.on("response", capture_search)

    # 先回首页稳定一下
    print("   先回首页...")
    try:
        page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
    except:
        pass
    
    print("   再进搜索页...")
    try:
        page.goto(
            "https://www.xiaohongshu.com/search_result?keyword=平山书店",
            wait_until="domcontentloaded", timeout=20000
        )
    except Exception as e:
        print(f"   第一次失败 ({e}), 2秒后重试...")
        time.sleep(2)
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

    # 如果不够 20 个，滚动加载更多
    scroll_attempts = 0
    while len(note_ids) < 20 and scroll_attempts < 5:
        print(f"   滚动加载更多... (当前 {len(note_ids)}/20)")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        scroll_attempts += 1

    print(f"\n  ✅ 获取到 {len(note_ids)} 个笔记 ID")
    for i, nid in enumerate(note_ids):
        print(f"     {i+1}. {nid}")

    # ---------- 第二步: 遍历每个笔记，抓详情 ---------- 
    print(f"\n{'='*60}")
    print("Step 2: 逐篇抓取详情 + 评论")
    print(f"{'='*60}")

    for idx, note_id in enumerate(note_ids):
        print(f"\n--- [{idx+1}/{len(note_ids)}] {note_id} ---")

        post_data = {"id": note_id, "url": f"https://www.xiaohongshu.com/explore/{note_id}"}
        # 用 mutable 容器替代 nonlocal
        flags = {"note": False, "comment": False}

        def make_handler(nid, pd, fl):
            def on_response(resp):
                url = resp.url
                try:
                    if f"/api/sns/web/v1/feed?source_note_id={nid}" in url and resp.status == 200:
                        body = resp.json()
                        items = body.get("data", {}).get("items", [])
                        if items:
                            nc = items[0].get("note_card", {})
                            pd["title"] = nc.get("display_title", "")
                            pd["desc"] = nc.get("desc", "")
                            pd["time"] = nc.get("time", nc.get("create_time", ""))
                            pd["like_count"] = nc.get("interact_info", {}).get("liked_count", 0)
                            pd["comment_count"] = nc.get("interact_info", {}).get("comment_count", 0)
                            pd["collect_count"] = nc.get("interact_info", {}).get("collected_count", 0)
                            pd["share_count"] = nc.get("interact_info", {}).get("share_count", 0)
                            pd["user"] = nc.get("user", {}).get("nickname", "")
                            pd["tag_list"] = nc.get("tag_list", [])
                            fl["note"] = True
                            print(f"   ✅ 详情: {pd.get('title', '')[:40]}")
                            print(f"       👍 {pd['like_count']}  💬 {pd['comment_count']}")
                    
                    if f"/api/sns/web/v2/comment/page?note_id={nid}" in url and resp.status == 200:
                        body = resp.json()
                        comments = body.get("data", {}).get("comments", [])
                        top_comments = []
                        for c in comments[:10]:
                            top_comments.append({
                                "user": c.get("user_info", {}).get("nickname", ""),
                                "content": c.get("content", ""),
                                "like_count": c.get("like_count", 0),
                                "time": c.get("create_time", "")
                            })
                        pd["top_comments"] = top_comments
                        pd["total_comments"] = body.get("data", {}).get("total_count", len(comments))
                        fl["comment"] = True
                        print(f"   💬 评论: {len(top_comments)} 条 (共 {pd.get('total_comments', '?')})")
                except:
                    pass
            return on_response

        page.on("response", make_handler(note_id, post_data, flags))

        # 打开笔记详情页 (带重试)
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        retries = 2
        ok = False
        for attempt in range(retries):
            try:
                page.goto(note_url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(3)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except:
                    pass
                time.sleep(2)
                ok = True
                break
            except Exception as e:
                print(f"   ⚠️ 第{attempt+1}次打开失败: {str(e)[:60]}")
                time.sleep(3)
        if not ok:
            print(f"   ❌ 跳过 {note_id}")
            continue

        # 如果 API 没抓到，尝试从 DOM 提取
        if not flags["note"]:
            try:
                dom_data = page.evaluate("""() => {
                    const text = document.body.innerText;
                    const imgs = Array.from(document.querySelectorAll('img[src*="xhscdn"]')).map(i => i.src.substring(0,60));
                    const title = document.title;
                    return {title, textLen: text.length, imgs: imgs.slice(0,3)};
                }""")
                post_data["dom_fallback"] = dom_data
                print(f"   ⚠️ API 未捕获，DOM fallback: 文字{dom_data.get('textLen','?')}字符")
            except:
                pass

        all_posts.append(post_data)

        # 慢一点，防止被 ban
        time.sleep(2)

    browser.close()

# ---------- 第三步: 保存 ----------
print(f"\n{'='*60}")
print(f"📊 最终统计")
print(f"{'='*60}")

success_count = sum(1 for p in all_posts if p.get("title") or p.get("desc"))
comment_count = sum(1 for p in all_posts if p.get("top_comments"))

print(f"   尝试抓取: {len(note_ids)} 篇")
print(f"   成功获取内容: {success_count} 篇")
print(f"   成功获取评论: {comment_count} 篇")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=2)

print(f"\n💾 数据保存: xhs_academic_data.json")
print(f"\n🏁 完成!")
