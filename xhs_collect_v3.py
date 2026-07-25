#!/usr/bin/env python3
"""
🦁 正文+评论采集 v3
全新会话 → 用户登录一次 → 逐篇提取
"""
import os, json, time
import warnings
warnings.filterwarnings("ignore")

DATA_FILE = "/Users/lyu/.openclaw/workspace/xhs_academic_data.json"
FRESH_DIR = "/Users/lyu/.openclaw/workspace/.xhs_fresh_session"

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=FRESH_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 900},
        locale="zh-CN"
    )
    page = browser.pages[0]

    # 1. 检查登录态
    print("📌 打开小红书首页...")
    page.goto("https://www.xiaohongshu.com/explore", 
              wait_until="domcontentloaded", timeout=15000)
    time.sleep(3)

    has_login = page.evaluate("""() => {
        const text = document.body.innerText;
        return !(text.includes('登录') && text.includes('扫码'));
    }""")

    if not has_login:
        print("\n⚠️ 请扫码登录小红书")
        print("   浏览器已打开，扫那个二维码")
        print("   登录好后按 Enter 继续")
        input()
        time.sleep(3)
        
        # 确认登录
        page.goto("https://www.xiaohongshu.com/explore", 
                  wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)

    print("✅ 已登录")

    # 2. 加载已有数据
    with open(DATA_FILE, encoding="utf-8") as f:
        posts = json.load(f)

    success_body = 0
    success_comment = 0

    for idx, post in enumerate(posts):
        note_id = post["id"]
        print(f"\n--- [{idx+1}/{len(posts)}] {post['title'][:30]} ---")

        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        retry = 2
        ok = False

        for attempt in range(retry):
            try:
                page.goto(note_url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(4)
                ok = True
                break
            except:
                if attempt == 0:
                    time.sleep(3)
                    continue
                print(f"   ⚠️ 加载失败，跳过")

        if not ok:
            continue

        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        time.sleep(2)

        # 检查是否被登录墙拦住
        login_check = page.evaluate("""() => {
            const t = document.body.innerText;
            return t.includes('登录') && t.includes('扫码') && t.includes('手机号');
        }""")

        if login_check:
            print(f"   ⚠️ 登录弹窗，可能是风控，跳过这篇")
            continue

        # --- 提取正文 ---
        body_text = page.evaluate("""() => {
            // 小红书 PC 版笔记内容通常在带有特定 data 属性的 div 中
            // 尝试多个策略
            
            // 策略1: #detail-desc (旧版)
            let el = document.querySelector('#detail-desc');
            if (el && el.innerText.trim().length > 50) return el.innerText.trim().substring(0, 5000);
            
            // 策略2: [class*="content"] 中最大的
            const texts = Array.from(document.querySelectorAll('[class*="content"], [class*="desc"], [class*="note"]'))
                .map(e => e.innerText.trim())
                .filter(t => t.length > 100 &&
                    !t.includes('沪ICP备') &&
                    !t.includes('营业执照') &&
                    !t.includes('举报中心'));
            
            if (texts.length > 0) {
                texts.sort((a,b) => b.length - a.length);
                return texts[0].substring(0, 5000);
            }
            
            // 策略3: 找所有 div 中最长且不像页脚的内容
            const excludePattern = /沪ICP备|营业执照|举报中心|个性化推荐|创作中心|业务合作|行吟信息/;
            const divs = document.querySelectorAll('div');
            let best = '', bestLen = 0;
            divs.forEach(d => {
                const t = d.innerText.trim();
                if (t.length > bestLen && t.length > 100 && !excludePattern.test(t)) {
                    // 检查是否有中文标点
                    if (/[，。！？：；""''（）【】]/.test(t)) {
                        best = t;
                        bestLen = t.length;
                    }
                }
            });
            return best ? best.substring(0, 5000) : '';
        }""")

        if body_text and len(body_text) > 80:
            post["desc"] = body_text
            success_body += 1
            preview = body_text[:80].replace('\n', ' ')
            print(f"   ✅ 正文: {len(body_text)} 字")
            print(f"      {preview}...")
        else:
            print(f"   ❌ 未找到正文 (页面可能是空的)")

        # --- 提取评论 ---
        comments = page.evaluate("""() => {
            // 小红书评论容器
            let commentContainer = document.querySelector('[class*="comment"], #comment');
            
            // 找所有评论项
            const items = document.querySelectorAll('[class*="comment-item"], [class*="commentItem"], [class*="reply"]');
            if (items.length > 0) {
                return Array.from(items)
                    .map(el => {
                        const nickname = el.querySelector('[class*="nickname"], [class*="name"]');
                        const content = el.querySelector('[class*="text"], [class*="content"]');
                        return {
                            user: nickname ? nickname.innerText.trim() : '',
                            content: content ? content.innerText.trim() : el.innerText.trim()
                        };
                    })
                    .filter(c => c.content.length > 2 && c.content.length < 500 &&
                        !c.content.includes('沪ICP') &&
                        !c.content.includes('营业执照'))
                    .slice(0, 10);
            }
            
            // fallback: 遍历所有文本节点找像评论的
            const excludePattern = /沪ICP备|营业执照|举报中心|行吟信息|©|分公司|热线电话/;
            const allTexts = Array.from(document.querySelectorAll('span, p, div'))
                .map(el => el.innerText.trim())
                .filter(t => t.length > 5 && t.length < 300 &&
                    /[\u4e00-\u9fff]/.test(t) &&
                    !excludePattern.test(t));
            
            // 去重
            const unique = [...new Set(allTexts)];
            return unique.slice(0, 10).map(t => ({content: t}));
        }""")

        if comments and len(comments) > 0:
            # 过滤掉太短的
            real_comments = [c for c in comments if len(c.get('content','')) > 5 and 
                           not c['content'].startswith('©')]
            if real_comments:
                post["top_comments"] = real_comments[:10]
                success_comment += 1
                print(f"   💬 评论: {len(real_comments)} 条")
                for c in real_comments[:3]:
                    uname = f"{c['user']}: " if c.get('user') else ""
                    print(f"      · {uname}{c['content'][:60]}")
                continue
        
        print(f"   ❌ 未提取到评论")

        # 每篇间隔
        time.sleep(3)

    # 4. 更新 JSON
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    browser.close()

print(f"\n{'='*60}")
print(f"🏁 完成")
print(f"{'='*60}")
print(f"   📝 正文采集: {success_body}/{len(posts)}")
print(f"   💬 评论采集: {success_comment}/{len(posts)}")
print(f"   💾 JSON: xhs_academic_data.json")
print(f"   📊 Excel: xhs_academic_data.xlsx")
print(f"\n   没拿到的 = 登录态不够或风控")
print(f"   如果大量没拿到，重新跑一次即可")
