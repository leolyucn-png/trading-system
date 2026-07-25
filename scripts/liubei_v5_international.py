#!/usr/bin/env python3
"""
刘备 V5 — 海外先发信息捕获
=============================
定位：第一时间捕获国外关于中国的大事 + 全球大事
不依赖国内新闻源（东财/新浪/同花顺只做排雷验证，不参与预测）

数据源（无需密钥，直接可拿）：
  1. Yahoo Finance 首页新闻 (美股+全球市场)
  2. Google News 搜索特定话题（中国、关税、半导体等）
  3. Reuters/Bloomberg 关键标题

用法：
  python3 liubei_v5_international.py           # 全量扫描
  python3 liubei_v5_international.py --china   # 只扫关于中国的事
  python3 liubei_v5_international.py --global  # 只扫全球大事
"""

import json, sys, os, datetime as dt
import requests

TIMEOUT = 10
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def _get(url, timeout=TIMEOUT):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r.text if r.status_code == 200 else None
    except:
        return None


# ============================================================
# 海外线1: Yahoo Finance 热门新闻（全球市场+宏观）
# ============================================================
def reuters_top_news():
    """路透社 — 路透已关闭公开RSS，改用Google News搜索路透来源"""
    results = []
    # Reuters killed their RSS in 2024/2025
    # 用web_search搜索路透社新闻作为替代
    queries = ["Reuters world news", "Reuters business China", "Reuters markets breaking"]
    # 更稳定的方式: Google News RSS 过滤路透来源
    try:
        for q in ["Reuters world", "Reuters China", "Reuters business"]:
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    src = item.findtext('source', '') or ''
                    # 只保留路透来源的
                    if 'Reuters' in src or 'reuters' in title[:20].lower():
                        results.append({
                            "title": title,
                            "desc": "",
                            "time": item.findtext('pubDate', '')[:25],
                            "source": "Reuters(via Google)"
                        })
                        if len(results) >= 30:
                            break
    except:
        pass
    return results


def bloomberg_top_news():
    """彭博 — 全球金融市场核心来源"""
    results = []
    # Bloomberg RSS feeds (已验证可用)
    feed_urls = [
        "https://www.bloomberg.com/feeds/markets/news.rss",
        "https://www.bloomberg.com/feeds/politics/news.rss",
        "https://www.bloomberg.com/feeds/technology/news.rss",
    ]
    for url in feed_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    desc = item.findtext('description', '')[:80]
                    pubdate = item.findtext('pubDate', '')[:25]
                    results.append({
                        "title": title,
                        "desc": desc,
                        "time": pubdate,
                        "source": "Bloomberg"
                    })
                    if len(results) >= 20:
                        break
        except:
            pass
    return results


def bbc_business_news():
    """BBC商业/全球新闻"""
    results = []
    feed_urls = [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ]
    for url in feed_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    desc = item.findtext('description', '')[:80]
                    pubdate = item.findtext('pubDate', '')[:25]
                    results.append({
                        "title": title,
                        "desc": desc,
                        "time": pubdate,
                        "source": "BBC"
                    })
                    if len(results) >= 20:
                        break
        except:
            pass
    return results


def yahoo_top_news():
    """Yahoo Finance 首页新闻 — 美股+全球市场风向"""
    results = []
    
    # Yahoo Finance RSS (无需API)
    urls = [
        "https://finance.yahoo.com/news/rssindex",
        "https://finance.yahoo.com/rss/topstories",
    ]
    
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    link = item.findtext('link', '')
                    pubdate = item.findtext('pubDate', '')[:25]
                    results.append({
                        "title": title,
                        "url": link,
                        "time": pubdate,
                        "source": "Yahoo Finance"
                    })
                    if len(results) >= 15:
                        break
        except:
            pass
    
    # 备用：Yahoo Finance 页面抓取
    if len(results) < 5:
        try:
            r = requests.get("https://finance.yahoo.com", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import re
                # 提取新闻标题（Yahoo页面结构）
                titles = re.findall(r'<h3[^>]*>([^<]+)</h3>', r.text)
                for t in titles[:10]:
                    t = t.strip()
                    if len(t) > 15 and t not in [x['title'] for x in results]:
                        results.append({
                            "title": t[:120],
                            "url": "",
                            "time": dt.datetime.now().strftime("%H:%M"),
                            "source": "Yahoo Finance(web)"
                        })
        except:
            pass
    
    return results


# ============================================================
# 海外线2: 国外关于中国的大事（关键词搜索）
# ============================================================
def china_related_news():
    """
    搜索国外媒体关于中国的最新报道
    使用 Google News RSS（完全开放，无需密钥）
    """
    results = []
    
    queries = [
        "China economy",
        "China stock market", 
        "China trade tariff",
        "China semiconductor",
        "China tech",
    ]
    
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    src = item.findtext('source', '') or "Google News"
                    results.append({
                        "title": title,
                        "url": item.findtext('link', ''),
                        "time": item.findtext('pubDate', '')[:25],
                        "source": f"Google News/{q}"
                    })
                    if len(results) >= 30:
                        break
        except:
            pass
    
    return results


# ============================================================
# 海外线3: 全球大事（市场+地缘+科技）
# ============================================================
def global_big_events():
    """全球宏观大事：地缘、美联储、战争、科技突破"""
    results = []
    
    queries = [
        "Federal Reserve interest rate",
        "global market selloff",
        "oil price crude",
        "AI regulation",
        "geopolitical conflict",
        "trade war tariffs",
    ]
    
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.content)
                for item in root.iter('item'):
                    title = item.findtext('title', '')[:120]
                    results.append({
                        "title": title,
                        "url": item.findtext('link', ''),
                        "time": item.findtext('pubDate', '')[:25],
                        "source": f"Google News/{q}"
                    })
                    if len(results) >= 30:
                        break
        except:
            pass
    
    return results


# ============================================================
# 汇总输出
# ============================================================
def run_all():
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("=" * 70)
    print(f"🌍 刘备 V5 · 海外先发信息捕获 · {now}")
    print("=" * 70)
    print("  定位：不靠国内新闻（那些进去就是接盘）")
    print("  只抓：国外关于中国的大事 + 全球大事")
    print("=" * 70)
    
    # 核心源1: 路透社
    print(f"\n📡 核心源1 · Reuters 路透社（全球最权威财经通讯社）")
    print("-" * 50)
    reuters = reuters_top_news()
    for n, item in enumerate(reuters[:8], 1):
        t = item['title'][:90]
        print(f"  {n:2}. {t}")
        print(f"      └ Reuters")
    if not reuters:
        print("  ⚠️ Reuters暂未获取到数据")
    
    # 核心源2: 彭博
    print(f"\n📡 核心源2 · Bloomberg 彭博（全球金融市场核心源）")
    print("-" * 50)
    bloomberg = bloomberg_top_news()
    for n, item in enumerate(bloomberg[:6], 1):
        t = item['title'][:90]
        print(f"  {n:2}. {t}")
        print(f"      └ Bloomberg")
    if not bloomberg:
        print("  ⚠️ Bloomberg暂未获取到数据")
    
    # 核心源3: BBC
    print(f"\n📡 核心源3 · BBC News（全球大事+商业）")
    print("-" * 50)
    bbc = bbc_business_news()
    for n, item in enumerate(bbc[:6], 1):
        t = item['title'][:90]
        print(f"  {n:2}. {t}")
        print(f"      └ BBC")
    if not bbc:
        print("  ⚠️ BBC暂未获取到数据")
    
    # 备选源: Yahoo Finance
    print(f"\n📡 备选源 · Yahoo Finance")
    print("-" * 50)
    yahoo = yahoo_top_news()
    for n, item in enumerate(yahoo[:5], 1):
        t = item['title'][:90]
        print(f"  {n:2}. {t}")
        print(f"      └ Yahoo Finance")
    if not yahoo:
        print("  (Yahoo无数据，不影响核心三源)")
    
    # 海外线2: 关于中国
    print(f"\n📡 海外线2 · 国外媒体关于中国的大事件")
    print("-" * 50)
    china = china_related_news()
    seen = set()
    count = 0
    for item in china:
        key = item['title'][:60]
        if key not in seen:
            seen.add(key)
            count += 1
            t = item['title'][:90]
            s = item['source'].split('/')[-1] if '/' in item['source'] else item['source']
            print(f"  {count:2}. {t}")
            print(f"      └ {s}")
            if count >= 10:
                break
    
    # 海外线3: 全球大事
    print(f"\n📡 海外线3 · 全球大事（地缘+宏观+科技）")
    print("-" * 50)
    glob = global_big_events()
    seen2 = set()
    count2 = 0
    for item in glob:
        key = item['title'][:60]
        if key not in seen2:
            seen2.add(key)
            count2 += 1
            t = item['title'][:90]
            s = item['source'].split('/')[-1] if '/' in item['source'] else item['source']
            print(f"  {count2:2}. {t}")
            print(f"      └ {s}")
            if count2 >= 12:
                break
    
    # 汇总
    total_reuters = len(reuters)
    total_bloomberg = len(bloomberg)
    total_bbc = len(bbc)
    total_backup = len(yahoo)
    
    print(f"\n{'='*70}")
    print(f"📋 汇总")
    print(f"{'='*70}")
    print(f"  核心三源:")
    print(f"    Reuters:   {total_reuters}条")
    print(f"    Bloomberg: {total_bloomberg}条")
    print(f"    BBC:       {total_bbc}条")
    print(f"  备选源:")
    print(f"    Yahoo:     {total_backup}条")
    print(f"  关于中国:     {len(china)}条（去重后{len(seen)}条）")
    print(f"  全球大事:     {len(glob)}条（去重后{len(seen2)}条）")
    
    # 判断：有无值得注意的夜间风险
    risk_level = "🟢 低"
    # 从核心三源+关于中国+全球里扫风险关键词
    risk_check = reuters[:5] + bloomberg[:5] + bbc[:5] + list(seen)[:5] + list(seen2)[:5]
    for item in risk_check:
        if isinstance(item, str):
            tl = item.lower()
        else:
            tl = item.get('title', '')[:50].lower()
        if any(x in tl for x in ['crash', 'plunge', 'tariff', 'war', 'sanction', 'collapse', 'crisis']):
            risk_level = "🔴 高"
            break
        elif any(x in tl for x in ['fall', 'drop', 'decline', 'tension', 'protest', 'slowdown']):
            risk_level = "🟡 中"
    
    print(f"\n  隔夜风险等级: {risk_level}")
    if risk_level == "🔴 高":
        print(f"  → 注意：有负面关键词出现在海外报道中，A股可能受影响")
    elif risk_level == "🟡 中":
        print(f"  → 需关注：有偏负面报道但程度不足以恐慌")
    else:
        print(f"  → 总体平稳")
    
    # 保存
    output = {
        "time": now,
        "reuters": reuters[:10],
        "bloomberg": bloomberg[:10],
        "bbc": bbc[:10],
        "china_related": list(seen)[:15],
        "global_events": list(seen2)[:15],
        "risk_level": risk_level,
        "source_stats": {"reuters": total_reuters, "bloomberg": total_bloomberg, "bbc": total_bbc, "yahoo": total_backup}
    }
    with open(os.path.join(OUT_DIR, "liubei_v5_status.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n💾 已保存: liubei_v5_status.json")


if __name__ == "__main__":
    # 命令行过滤
    if '--china' in sys.argv:
        print("\n🌍 仅扫描关于中国的内容")
        for item in china_related_news()[:15]:
            print(f"  {item['title'][:100]}")
    elif '--global' in sys.argv:
        print("\n🌍 仅扫描全球大事")
        for item in global_big_events()[:15]:
            print(f"  {item['title'][:100]}")
    else:
        run_all()
