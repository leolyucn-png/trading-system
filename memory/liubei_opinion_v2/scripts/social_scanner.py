#!/usr/bin/env python3
"""
刘备 V3.1 · 社交媒体异常检测
扫描东方财富股吧，检测帖子回复量异常暴增的个股
"""
import requests
import re
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

# 重点监控池（可扩展）
WATCHLIST = [
    "002607",  # 中公教育
    "002624",  # 完美世界
    "002023",  # 海特高新
    "002185",  # 华天科技
    "600703",  # 三安光电
    "002747",  # 埃斯顿
    "600391",  # 航发科技
    "600547",  # 山东黄金
]

# 全市场热门扫描（前100活跃股吧）
FULL_SCAN = True

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://guba.eastmoney.com/"
}

def fetch_guba_page(code, page=1):
    """抓取东方财富股吧个股页面"""
    url = f"https://guba.eastmoney.com/list,{code},f_{page}.html"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        return None

def parse_post_stats(html):
    """解析帖子阅读/回复数据"""
    if not html:
        return []
    # 匹配阅读数和回复数
    posts = []
    # 东财股吧的帖子数据通常在 article 或 div 中
    pattern = r'<cite class="l1.*?">(\d+)</cite>.*?<cite class="l2.*?">(\d+)</cite>'
    matches = re.findall(pattern, html, re.DOTALL)
    for read_count, reply_count in matches:
        posts.append({
            "read": int(read_count),
            "reply": int(reply_count)
        })
    return posts

def scan_stock(code, name=""):
    """扫描单只股票的股吧热度"""
    html = fetch_guba_page(code)
    posts = parse_post_stats(html)
    
    if not posts:
        return None
    
    total_reads = sum(p["read"] for p in posts)
    total_replies = sum(p["reply"] for p in posts)
    avg_replies = total_replies / len(posts) if posts else 0
    hot_post_replies = max(p["reply"] for p in posts) if posts else 0
    
    return {
        "code": code,
        "name": name,
        "posts_scanned": len(posts),
        "total_reads": total_reads,
        "total_replies": total_replies,
        "avg_replies": round(avg_replies, 1),
        "hottest_post_replies": hot_post_replies,
        "time": datetime.now().isoformat()
    }

def check_anomaly(current, baseline=None):
    """检测异常：当前热度 vs 基准（前3日均值）"""
    alerts = []
    
    # 无基准数据时使用绝对阈值
    if baseline is None:
        if current["total_replies"] > 500:
            alerts.append(f"🔥 高热度: 总回复{current['total_replies']}条")
        if current["hottest_post_replies"] > 100:
            alerts.append(f"🚀 热帖: 最高回复{current['hottest_post_replies']}条")
        return alerts
    
    # 有基准数据时使用相对阈值
    ratio = current["total_replies"] / max(baseline.get("total_replies", 1), 1)
    if ratio > 5:
        alerts.append(f"🔥🔥 回复量暴涨{ratio:.0f}倍! ({baseline.get('total_replies',0)}→{current['total_replies']})")
    elif ratio > 3:
        alerts.append(f"🔥 回复量增长{ratio:.0f}倍")
    
    return alerts

def main():
    print("=" * 60)
    print(f"🐉 刘备 V3.1 · 社交媒体异动扫描")
    print(f"   时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    alerts = []
    
    # 扫描重点监控池
    for code in WATCHLIST:
        result = scan_stock(code)
        if result:
            results.append(result)
            anomaly = check_anomaly(result)
            if anomaly:
                alerts.append({"code": code, "alerts": anomaly, "data": result})
        time.sleep(0.5)  # 避免被封
    
    # 输出结果
    print("\n📊 重点监控池热度排名：")
    print("-" * 60)
    sorted_results = sorted(results, key=lambda x: x["total_replies"], reverse=True)
    for i, r in enumerate(sorted_results[:10], 1):
        hot_mark = "🔥" if r["hottest_post_replies"] > 100 else "  "
        print(f"  {i:2}. {hot_mark} {r['code']} | 总回复{r['total_replies']:>5} | 均{r['avg_replies']:>5} | 最热{r['hottest_post_replies']:>5}")
    
    # 输出警报
    if alerts:
        print(f"\n🚨 社交媒体异常警报（{len(alerts)}条）：")
        print("-" * 60)
        for a in alerts:
            print(f"  📍 {a['code']}")
            for al in a['alerts']:
                print(f"     → {al}")
    else:
        print("\n✅ 未检测到社交媒体异常")
    
    # 保存结果
    output = {
        "scan_time": datetime.now().isoformat(),
        "results": results,
        "alerts": alerts
    }
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    hour_str = datetime.now().strftime("%H%M")
    filename = f"/Users/lyu/.openclaw/workspace/memory/liubei_opinion_v2/social_alert/{date_str}_{hour_str}.json"
    with open(filename, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📁 结果已保存：{filename}")
    
    return alerts

if __name__ == "__main__":
    main()
