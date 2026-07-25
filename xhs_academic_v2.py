#!/usr/bin/env python3
"""
🦁 小红书数据采集 v2
从搜索 API 直接提取 (绕过详情页登录墙)
+ 从详情页 DOM 提取正文
"""
import os, json, time, re
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

    search_raw = []  # 存搜索 API 的原始数据

    def capture_search(resp):
        url = resp.url
        if "/api/sns/web/v1/search/notes" in url and resp.status == 200:
            try:
                body = resp.json()
                items = body.get("data", {}).get("items", [])
                search_raw.extend(items)
                print(f"  📦 搜索API: 已缓存 {len(items)} 条 (累计 {len(search_raw)})")
            except:
                pass

    page.on("response", capture_search)

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

    # 滚动加载更多到 20+
    while len(search_raw) < 20:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        print(f"   滚动加载... (当前 {len(search_raw)} 条)")
        if len(search_raw) >= 20:
            break

    # 整理数据
    posts = []
    for item in search_raw[:20]:
        note_id = item.get("id", "")
        nc = item.get("note_card", {})
        interact = nc.get("interact_info", {})
        
        # 从 note_card 提取
        post = {
            "id": note_id,
            "url": f"https://www.xiaohongshu.com/explore/{note_id}",
            "title": nc.get("display_title", ""),
            "desc": nc.get("desc", ""),
            "user": nc.get("user", {}).get("nickname", ""),
            "like_count": interact.get("liked_count", 0),
            "comment_count": interact.get("comment_count", 0),
            "collect_count": interact.get("collected_count", 0),
            "share_count": interact.get("share_count", 0),
            "image_count": len(nc.get("image_list", [])),
            "type": nc.get("type", ""),
            "top_comments": []
        }
        
        # 提取发帖时间 (可能在不同字段)
        raw_time = nc.get("time", 0) or nc.get("create_time", 0)
        if raw_time:
            import datetime
            try:
                post["time"] = datetime.datetime.fromtimestamp(raw_time).strftime("%Y-%m-%d %H:%M:%S")
            except:
                post["time"] = str(raw_time)
        else:
            post["time"] = ""
        
        posts.append(post)
        print(f"  [{len(posts)}] {post['title'][:30]}  👍{post['like_count']} 💬{post['comment_count']}")

    # 尝试获取评论 (从 DOM)
    print(f"\n{'='*60}")
    print("尝试获取前10评论 (从页面 DOM)")
    print(f"{'='*60}")

    for idx, post in enumerate(posts):
        nid = post["id"]
        print(f"\n  [{idx+1}/{len(posts)}] {post['title'][:25]}...")
        
        # 尝试打开详情页
        note_url = f"https://www.xiaohongshu.com/explore/{nid}"
        try:
            page.goto(note_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)
            
            # 检查是否被登录墙挡住
            page_text = page.evaluate("document.body.innerText")
            
            if "登录" in page_text[:100]:
                print(f"     ⚠️ 登录墙，跳过")
                continue
            
            # 从 DOM 提取正文
            content = page.evaluate("""() => {
                // 尝试多种选择器找正文
                const selectors = [
                    '.note-content', '[class*="content"]', 
                    '.desc', '.note', 'article',
                    '.rich-content', '.post-content'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.length > 50) 
                        return el.innerText.substring(0, 2000);
                }
                // 全页文字去头尾
                const text = document.body.innerText;
                return text.length > 300 ? text.substring(200, 1500) : text;
            }""")
            if content and len(content) > 50:
                post["desc"] = content[:2000]
                print(f"     ✅ 正文: {len(content)} 字")
            
            # 从 DOM 提取评论
            comments = page.evaluate("""() => {
                const commentEls = document.querySelectorAll('[class*="comment"]');
                if (commentEls.length === 0) return [];
                const results = [];
                commentEls.forEach(el => {
                    const text = el.innerText.trim();
                    if (text.length > 5 && text.length < 500) {
                        results.push(text);
                    }
                });
                // 去重取前10
                const unique = [...new Set(results)];
                return unique.slice(0, 10);
            }""")
            
            if comments and len(comments) > 0:
                post["top_comments"] = [{"content": c} for c in comments]
                print(f"     ✅ 评论: {len(comments)} 条")
            else:
                print(f"     ⚠️ 未提取到评论")
                
        except Exception as e:
            print(f"     ❌ 打开失败: {str(e)[:50]}")
        
        time.sleep(2)

    browser.close()

# 保存
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print("📊 最终统计")
print(f"{'='*60}")
print(f"   帖子: {len(posts)} 篇")
print(f"   含正文: {sum(1 for p in posts if p.get('desc') and len(p.get('desc',''))>50)} 篇")
print(f"   含评论: {sum(1 for p in posts if p.get('top_comments'))} 篇")
print(f"\n💾 保存: xhs_academic_data.json")
