#!/usr/bin/env python3
"""
DOM 结构探查：打开一篇笔记，打印所有 div 的 class 和 text 前 50 字
"""
import os, json, time
import warnings
warnings.filterwarnings("ignore")

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

    note_id = "69ef64ac000000001f006a0b"  # 釜山旅行
    print(f"🔍 打开笔记: {note_id}")
    page.goto(f"https://www.xiaohongshu.com/explore/{note_id}",
              wait_until="domcontentloaded", timeout=15000)
    time.sleep(5)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass
    time.sleep(3)

    # 打印所有 div 的 class + 文本摘要
    divs = page.evaluate("""() => {
        const divs = document.querySelectorAll('div');
        return Array.from(divs).slice(0, 80).map(d => ({
            class: (d.className || '').substring(0, 60),
            id: d.id || '',
            textLen: (d.innerText || '').trim().length,
            textPreview: (d.innerText || '').trim().substring(0, 80).replace(/\\n/g, ' '),
            childCount: d.children.length
        })).filter(d => d.textLen > 20);
    }""")

    print(f"\n📋 页面主要 div ({len(divs)}):")
    for i, d in enumerate(divs):
        print(f"\n  [{i}] class={d['class']}  id={d['id']}")
        print(f"      文字({d['textLen']}字): {d['textPreview']}")
        print(f"      子节点: {d['childCount']}")

    # 看看有没有 iframe / shadow root
    iframes = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('iframe')).map(f => f.src || f.id || f.className).slice(0,5);
    }""")
    print(f"\n📦 iframe: {iframes}")

    page.screenshot(path="/Users/lyu/.openclaw/workspace/dom_probe.png", full_page=True)
    browser.close()
