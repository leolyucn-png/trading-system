#!/usr/bin/env python3
"""
📊 导出 Excel + 🦁 正文评论采集 v2
两步并行：
  1. 把已有数据转成 Excel
  2. 用新会话逐篇打开页面提取正文和评论
"""
import os, json, time, datetime
import warnings
warnings.filterwarnings("ignore")

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

DATA_FILE = "/Users/lyu/.openclaw/workspace/xhs_academic_data.json"
EXCEL_FILE = "/Users/lyu/.openclaw/workspace/xhs_academic_data.xlsx"
USER_DATA_DIR = "/Users/lyu/.openclaw/workspace/.xhs_browser_data"

# ======== 1. 加载已有数据 ========
with open(DATA_FILE, encoding="utf-8") as f:
    posts = json.load(f)

# ======== 2. 转 Excel ========
print("📊 生成 Excel...")
wb = Workbook()
ws = wb.active
ws.title = "平山书店帖子数据"

# 表头
headers = [
    "序号", "笔记ID", "标题", "正文/描述", "发帖时间",
    "作者", "点赞数", "评论数", "收藏数", "分享数",
    "类型", "标签", "图片链接", "TOP评论", "笔记链接"
]
# 样式
header_font = Font(bold=True, color="FFFFFF", size=11)
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align

# 数据行
for i, p in enumerate(posts, 1):
    row = i + 1
    ws.cell(row=row, column=1, value=i)
    ws.cell(row=row, column=2, value=p.get("id", ""))
    ws.cell(row=row, column=3, value=p.get("title", ""))
    ws.cell(row=row, column=4, value=p.get("desc", ""))
    ws.cell(row=row, column=5, value=p.get("time", ""))
    ws.cell(row=row, column=6, value=p.get("user", ""))
    ws.cell(row=row, column=7, value=p.get("like_count", 0))
    ws.cell(row=row, column=8, value=p.get("comment_count", 0))
    ws.cell(row=row, column=9, value=p.get("collect_count", 0))
    ws.cell(row=row, column=10, value=p.get("share_count", 0))
    ws.cell(row=row, column=11, value=p.get("type", ""))
    ws.cell(row=row, column=12, value=", ".join(p.get("tags", [])))
    ws.cell(row=row, column=13, value="\n".join(p.get("images", [])))
    ws.cell(row=row, column=14, value="\n".join(
        [f"{c.get('user','')}: {c.get('content','')}" for c in p.get("top_comments", [])]
    ) if p.get("top_comments") else "")
    ws.cell(row=row, column=15, value=p.get("url", ""))

# 列宽
col_widths = [6, 28, 35, 40, 20, 18, 10, 10, 10, 10, 10, 20, 50, 40, 40]
for col, w in enumerate(col_widths, 1):
    ws.column_dimensions[chr(64+col)].width = w

wb.save(EXCEL_FILE)
print(f"   ✅ Excel 已保存: xhs_academic_data.xlsx")
print(f"      共 {len(posts)} 行数据")

# ======== 3. 正文+评论采集 ========
print(f"\n{'='*60}")
print("🦁 逐篇采集正文和评论（新会话，正常浏览）")
print(f"{'='*60}")
print("  策略: 每次打开一篇笔记，等页面渲染，从 DOM 提取内容")
print("  间隔: 每篇等 3-5 秒，不触发风控")
print()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 用已有持久化上下文（已有登录态）
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 900},
        locale="zh-CN"
    )
    page = browser.pages[0]

    success_body = 0
    success_comment = 0

    for idx, post in enumerate(posts):
        note_id = post["id"]
        print(f"\n--- [{idx+1}/{len(posts)}] {post['title'][:30]} ---")

        # 先回首页洗一下导航状态
        if idx % 5 == 0:
            try:
                page.goto("https://www.xiaohongshu.com/explore",
                          wait_until="domcontentloaded", timeout=15000)
                time.sleep(2)
            except:
                pass

        # 打开笔记详情
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        try:
            page.goto(note_url, wait_until="domcontentloaded", timeout=20000)
        except:
            print(f"   ⚠️ 页面加载失败，跳过")
            continue

        # 等渲染 + API 返回
        time.sleep(4)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except:
            pass
        time.sleep(2)

        # 检查是否有登录弹窗
        page_text = page.evaluate("document.body.innerText")
        if "登录" in page_text[:200] and ("扫码" in page_text[:200] or "手机号" in page_text[:200]):
            print(f"   ⚠️ 登录弹窗，跳过这篇")
            continue

        # --- 提取正文 ---
        # 策略: 在页面里找包含笔记内容的节点
        body_text = page.evaluate("""() => {
            // 排除已知的非内容元素
            const excludeTexts = [
                '沪ICP备', '营业执照', '举报中心', '个性化推荐',
                '创作中心', '业务合作', '发现', '直播', '发布',
                '通知', '我', '登录', '注册'
            ];
            
            function isContent(el) {
                const t = el.innerText.trim();
                if (t.length < 80) return false;
                // 检查是否包含排除文本
                for (const ex of excludeTexts) {
                    if (t.includes(ex)) return false;
                }
                // 内容应该有换行、标点符号
                const hasPunct = /[，。！？、：；""''（）【】]/.test(t);
                return hasPunct && t.length > 100;
            }

            // 遍历所有 div，找最大内容块
            const divs = document.querySelectorAll('div');
            let best = '', bestLen = 0;
            divs.forEach(d => {
                const t = d.innerText.trim();
                if (t.length > bestLen && isContent(d)) {
                    best = t;
                    bestLen = t.length;
                }
            });
            return best.substring(0, 5000);
        }""")

        if body_text and len(body_text) > 80:
            post["desc"] = body_text
            success_body += 1
            print(f"   ✅ 正文: {len(body_text)} 字")
            print(f"      {body_text[:100].replace(chr(10), ' ')}...")
        else:
            print(f"   ⚠️ 未找到正文")

        # --- 提取评论 ---
        comments = page.evaluate("""() => {
            const excludePattern = /沪ICP|举报|营业执照|创作中心|发现|直播|发布|通知/;
            const allEls = document.querySelectorAll('div, span, p');
            const results = [];
            const seen = new Set();
            
            allEls.forEach(el => {
                const text = el.innerText.trim();
                // 评论的特征: 5-500字, 不含排除文本, 含对话感
                if (text.length < 5 || text.length > 500) return;
                if (excludePattern.test(text)) return;
                // 有用户名+冒号 或 以回复/评论开头
                if (seen.has(text)) return;
                seen.add(text);
                results.push(text);
            });
            
            // 再过滤: 去掉纯英文、纯数字、URL
            return results
                .filter(t => /[\u4e00-\u9fff]/.test(t))  // 至少有一个汉字
                .filter(t => !t.startsWith('http'))        // 不是 URL
                .slice(0, 15);                              // 取前15条
        }""")

        if comments:
            formatted = []
            for c in comments:
                formatted.append({"content": c[:300]})
            post["top_comments"] = formatted
            success_comment += 1
            print(f"   💬 评论: {len(comments)} 条")
            for c in comments[:3]:
                print(f"      · {c[:60]}")
        else:
            print(f"   ⚠️ 未提取到评论")

        # 每篇间隔，避免触发风控
        time.sleep(3)

    browser.close()

# ======== 4. 更新 Excel ========
print(f"\n{'='*60}")
print(f"📊 更新 Excel — 补充正文和评论")
print(f"{'='*60}")

for i, p in enumerate(posts):
    row = i + 2
    ws.cell(row=row, column=4, value=p.get("desc", ""))
    ws.cell(row=row, column=14, value="\n".join(
        [f"{c.get('user','')}: {c.get('content','')}" if c.get('user') else c.get('content','')
         for c in p.get("top_comments", [])]
    ) if p.get("top_comments") else "")

wb.save(EXCEL_FILE)

# ======== 5. 保存 JSON ========
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

# ======== 6. 总结 ========
print(f"\n{'='*60}")
print(f"🏁 全部完成")
print(f"{'='*60}")
print(f"   📊 Excel: xhs_academic_data.xlsx ({len(posts)} 行)")
print(f"   📝 采集到正文: {success_body}/{len(posts)} 篇")
print(f"   💬 采集到评论: {success_comment}/{len(posts)} 篇")

if success_body < len(posts):
    print(f"\n   ⚠️ 说明: {len(posts) - success_body} 篇正文没拿到")
    print(f"      → 可能是登录态过期或风控")
    print(f"      → 等几小时后重新运行即可补全")
