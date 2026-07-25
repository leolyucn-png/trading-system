#!/usr/bin/env python3
"""
深度探针：打开一篇笔记，打印所有 API 响应
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

    def on_response(resp):
        url = resp.url
        # 只看 edith 的业务 API
        if "edith.xiaohongshu.com/api" in url:
            try:
                if "application/json" in (resp.headers.get("content-type", "")):
                    body = resp.json()
                    print(f"\n  📡 {resp.status} {url.split('?')[0]}")
                    print(f"     keys: {list(body.keys()) if isinstance(body, dict) else type(body).__name__}")
                    # 看 success/msg
                    if isinstance(body, dict):
                        s = body.get("success", body.get("code", ""))
                        m = body.get("msg", "")
                        print(f"     status: {s} | msg: {m}")
                        # 如果是 feed API，打印 item 结构
                        if "feed" in url and body.get("data", {}).get("items"):
                            item = body["data"]["items"][0]
                            nc = item.get("note_card", {})
                            print(f"     title: {nc.get('display_title','')[:30]}")
                            print(f"     desc length: {len(nc.get('desc',''))}")
                            print(f"     desc: {nc.get('desc','')[:100]}")
            except:
                pass

    page.on("response", on_response)

    # 打开第一篇笔记
    note_id = "69ef64ac000000001f006a0b"  # 釜山旅行最惊喜的一天
    print(f"🔍 打开笔记: {note_id}")
    page.goto(f"https://www.xiaohongshu.com/explore/{note_id}",
              wait_until="domcontentloaded", timeout=20000)
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # 页面是什么内容？
    page_text = page.evaluate("document.body.innerText")
    print(f"\n📝 页面文字 (前300):")
    print(f"  {page_text[:300]}")

    # 检查正文元素
    content_el = page.evaluate("""() => {
        // 看页面中最大的文字区块
        const allDivs = document.querySelectorAll('div');
        let maxLen = 0, maxText = '';
        allDivs.forEach(d => {
            const t = d.innerText.trim();
            if (t.length > maxLen && t.length < 5000) {
                maxLen = t.length;
                maxText = t.substring(0, 100);
            }
        });
        return {maxLen, maxText};
    }""")
    print(f"\n📐 最大文字块: {content_el['maxLen']} 字")
    print(f"   {content_el['maxText']}")

    browser.close()
