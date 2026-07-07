#!/usr/bin/env python3
"""
刘备 V3.1 · 热搜排名追踪
抓取东方财富/同花顺个股热搜榜，追踪排名变化
"""
import requests
import re
import json
import os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 历史快照目录
SNAPSHOT_DIR = "/Users/lyu/.openclaw/workspace/memory/liubei_opinion_v2/hot_rank"

def fetch_eastmoney_hot():
    """抓取东方财富个股热搜榜"""
    # 东财热搜榜API
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "50",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
        "_": str(int(datetime.now().timestamp() * 1000))
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                stocks.append({
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0),
                    "change_pct": item.get("f3", 0),
                    "volume": item.get("f62", 0),
                    "amount": item.get("f66", 0),
                })
        return stocks
    except Exception as e:
        print(f"  ⚠️ 东财热搜榜抓取失败: {e}")
        return []

def fetch_eastmoney_hotrank():
    """抓取东方财富关注度排行榜（备选方案）"""
    try:
        url = "https://rm.api.eastmoney.com/api/hy/get"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        stocks = []
        if data.get("data"):
            for item in data["data"]:
                stocks.append({
                    "code": item.get("c", ""),
                    "name": item.get("n", ""),
                    "rank": item.get("r", 0),
                })
        return stocks
    except:
        return []

def load_previous_snapshot():
    """加载最近一次快照，用于对比排名变化"""
    files = sorted(os.listdir(SNAPSHOT_DIR)) if os.path.exists(SNAPSHOT_DIR) else []
    if not files:
        return {}
    
    latest = files[-1]
    with open(os.path.join(SNAPSHOT_DIR, latest), "r") as f:
        return json.load(f)

def compare_rankings(current, previous):
    """对比两次排名，找出异动"""
    if not previous or "stocks" not in previous:
        return []
    
    prev_map = {s["code"]: i for i, s in enumerate(previous.get("stocks", []))}
    changes = []
    
    for i, stock in enumerate(current):
        code = stock["code"]
        prev_rank = prev_map.get(code, -1)
        if prev_rank != -1:
            jump = prev_rank - i  # 正数=排名上升
            if jump >= 30:
                changes.append({
                    "code": code,
                    "name": stock["name"],
                    "prev_rank": prev_rank + 1,
                    "curr_rank": i + 1,
                    "jump": jump,
                    "level": "🚀" if jump >= 50 else "📊"
                })
        else:
            if i < 20:  # 新进入前20
                changes.append({
                    "code": code,
                    "name": stock["name"],
                    "prev_rank": "N/A",
                    "curr_rank": i + 1,
                    "jump": "NEW",
                    "level": "🆕"
                })
    
    return changes

def main():
    print("=" * 60)
    print(f"📊 刘备 V3.1 · 热搜排名追踪")
    print(f"   时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 抓取当前排名
    print("\n📡 抓取东方财富热搜榜...")
    stocks = fetch_eastmoney_hot()
    
    if not stocks:
        print("  ❌ 热搜榜数据为空，可能是非交易时段")
        return
    
    print(f"  ✅ 获取到 {len(stocks)} 只热门股")
    
    # 显示前20
    print(f"\n🏆 热搜榜 TOP20：")
    print("-" * 60)
    for i, s in enumerate(stocks[:20], 1):
        change_str = f"{s['change_pct']:+.2f}%" if isinstance(s['change_pct'], (int, float)) else "N/A"
        print(f"  {i:2}. {s['code']} {s['name']:<8} {s['price']} {change_str}")
    
    # 加载历史快照对比
    previous = load_previous_snapshot()
    if previous:
        print(f"\n📈 排名变化（对比上次快照 {previous.get('scan_time','')[:16]}）：")
        print("-" * 60)
        changes = compare_rankings(stocks, previous)
        if changes:
            for c in changes:
                if c["jump"] == "NEW":
                    print(f"  {c['level']} {c['code']} {c['name']} → 新进入 TOP{c['curr_rank']}!")
                else:
                    print(f"  {c['level']} {c['code']} {c['name']} → {c['prev_rank']}位→{c['curr_rank']}位 (↑{c['jump']})")
        else:
            print("  ✅ 无重大排名变化")
    else:
        print("\n  📝 首次快照，无历史对比数据")
    
    # 保存快照
    output = {
        "scan_time": datetime.now().isoformat(),
        "source": "eastmoney",
        "stocks": stocks
    }
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    hour_str = datetime.now().strftime("%H%M")
    filename = os.path.join(SNAPSHOT_DIR, f"{date_str}_{hour_str}.json")
    with open(filename, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📁 快照已保存：{filename}")
    
    return stocks

if __name__ == "__main__":
    main()
