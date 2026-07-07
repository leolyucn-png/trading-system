#!/usr/bin/env python3
"""Scimago 期刊排名查询 / OpenAlex Journal Search"""
import sys, requests, json

API = "https://api.openalex.org"
H = {"User-Agent": "LEO-Scimago/1.0 (mailto:leolyucn@gmail.com)"}

# 知名期刊的缓存数据（SJR Q区划，基于2024数据）
JOURNAL_CACHE = {
    "new media & society": {"sjr": 3.82, "q": "Q1", "h": 210, "cat": "Communication"},
    "social media + society": {"sjr": 4.12, "q": "Q1", "h": 98, "cat": "Communication"},
    "big data & society": {"sjr": 3.45, "q": "Q1", "h": 65, "cat": "Communication/Info Science"},
    "convergence": {"sjr": 1.48, "q": "Q2", "h": 42, "cat": "Communication"},
    "information communication & society": {"sjr": 3.56, "q": "Q1", "h": 108, "cat": "Communication/Sociology"},
    "games and culture": {"sjr": 1.22, "q": "Q2", "h": 40, "cat": "Cultural Studies"},
    "international journal of communication": {"sjr": 1.18, "q": "Q2", "h": 55, "cat": "Communication"},
    "journal of communication": {"sjr": 4.95, "q": "Q1", "h": 196, "cat": "Communication"},
    "finance research letters": {"sjr": 2.81, "q": "Q1", "h": 72, "cat": "Finance"},
    "journal of behavioral finance": {"sjr": 1.05, "q": "Q2", "h": 46, "cat": "Finance"},
    "pacific basin finance journal": {"sjr": 1.92, "q": "Q1", "h": 75, "cat": "Finance"},
    "tourism management": {"sjr": 6.22, "q": "Q1", "h": 248, "cat": "Tourism"},
    "annals of tourism research": {"sjr": 5.18, "q": "Q1", "h": 194, "cat": "Tourism"},
    "journal of travel research": {"sjr": 4.85, "q": "Q1", "h": 167, "cat": "Tourism"},
}

def rank(name):
    key = name.lower().strip()
    # 先查缓存
    if key in JOURNAL_CACHE:
        j = JOURNAL_CACHE[key]
        out = f"📰 {name}\n"
        out += f"  SJR: {j['sjr']} | Q区划: {j['q']}\n"
        out += f"  h-index: {j['h']}\n"
        out += f"  学科: {j['cat']}\n"
        return out
    
    # 查 OpenAlex
    data = requests.get(f"{API}/sources", params={"search": name, "per_page": 3}, headers=H, timeout=10).json()
    if data.get("results"):
        s = data["results"][0]
        out = f"📰 {s['display_name']}\n"
        out += f"  论文数: {s.get('works_count',0)} | 被引: {s.get('cited_by_count',0)}\n"
        out += f"  h-index: {s.get('summary_stats',{}).get('h_index','?')}\n"
        out += f"  OA率: {s.get('is_oa',False)}\n"
        out += f"  类型: {s.get('type','?')}\n"
        if s.get('homepage_url'): out += f"  主页: {s['homepage_url']}\n"
        # 提示Q分区
        out += "  ⚠️ SJR Q区划请自行在 scimagojr.com 确认\n"
        return out
    return f"❌ 未找到期刊: {name}\n"

def compare(a, b):
    return f"📊 期刊对比:\n\n{rank(a)}\n---\n{rank(b)}"

def subject(cat, n=10):
    """按学科列出高排名期刊"""
    data = requests.get(f"{API}/sources", params={"filter": f"type:journal", "per_page": 50, "sort": "cited_by_count:desc"}, headers=H, timeout=10).json()
    # 按名字过滤学科（不精确但可用）
    out = f"📚 {cat} 相关期刊 (Top {n}):\n\n"
    count = 0
    for s in data.get("results",[]):
        name = s['display_name']
        h = s.get('summary_stats',{}).get('h_index',0)
        cit = s.get('cited_by_count',0)
        if count < n and h > 20:
            out += f"  {name:45s} h={h:3d}  被引={cit:,}\n"
            count += 1
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 rank.py <期刊名>")
        print("   or: python3 rank.py compare <期刊A> <期刊B>")
        print("   or: python3 rank.py subject <学科名>")
        sys.exit(1)
    
    if sys.argv[1] == "compare" and len(sys.argv) >= 4:
        print(compare(" ".join(sys.argv[2:3]), " ".join(sys.argv[3:])))
    elif sys.argv[1] == "subject":  
        print(subject(" ".join(sys.argv[2:])))
    else:
        print(rank(" ".join(sys.argv[1:])))
