#!/usr/bin/env python3
"""Semantic Scholar 论文搜索"""
import sys, requests, json

API = "https://api.semanticscholar.org/graph/v1"
HEADERS = {"User-Agent": "LEO-S2/1.0"}

def fmt(p):
    title = p.get("title","")
    year = p.get("year","")
    cited = p.get("citationCount",0)
    authors = ", ".join(a.get("name","") for a in p.get("authors",[])[:3])
    if len(p.get("authors",[])) > 3: authors += " et al."
    pid = p.get("paperId","")
    ext = p.get("externalIds",{})
    doi = ext.get("DOI","") if ext else ""
    venue = p.get("venue","") or ""
    return f"  [{year}] {title}\n  {authors}\n  {venue} | 被引{cited}次 | ID={pid}\n  DOI: {doi}\n"

def search(query, n=10):
    r = requests.get(f"{API}/paper/search", params={"query": query, "limit": n, "fields": "title,year,citationCount,authors,venue,externalIds"}, headers=HEADERS, timeout=15)
    if r.status_code != 200: return f"❌ API错误: {r.status_code}"
    data = r.json()
    cnt = data.get("total",0)
    out = f"🔍 搜索: {query}\n共{cnt}条结果:\n\n"
    for p in data.get("data",[]):
        out += fmt(p)
    return out

def recommend(pid, n=5):
    pid = pid.replace("https://doi.org/","").replace("CorpusId:","")
    r = requests.get(f"{API}/paper/{pid}/recommendations", params={"limit": n}, headers=HEADERS, timeout=15)
    if r.status_code != 200: return f"❌ API错误: {r.status_code}"
    data = r.json()
    out = "🔗 推荐论文:\n\n"
    for p in data.get("recommendedPapers",[]):
        out += fmt(p)
    return out

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 search.py <cmd> <query>")
        print("命令: search | recommend")
        sys.exit(1)
    cmd, q = sys.argv[1], " ".join(sys.argv[2:])
    print({"search": search, "recommend": recommend}.get(cmd, lambda x: "未知命令")(q))
