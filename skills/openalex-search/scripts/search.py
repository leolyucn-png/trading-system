#!/usr/bin/env python3
"""
OpenAlex 学术搜索 (requests版，解决macOS SSL问题)
"""
import sys, json, requests

API = "https://api.openalex.org"
HEADERS = {"User-Agent": "LEO-OpenAlex/1.0 (mailto:leolyucn@gmail.com)"}

def api_get(path, params=None):
    url = f"{API}{path}"
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def fmt(w):
    authors = ", ".join(a.get("author",{}).get("display_name","?") for a in w.get("authorships",[])[:3])
    if len(w.get("authorships",[])) > 3: authors += " et al."
    year = w.get("publication_year","")
    title = w.get("title","") or "(无标题)"
    cited = w.get("cited_by_count",0)
    venue = (w.get("primary_location") or {}).get("source") or {}
    journal = venue.get("display_name","") if venue else ""
    oid = w["id"].split("/")[-1] if w.get("id") else "?"
    return f"  [{year}] {title}\n  {authors}\n  {journal} | 被引{cited}次 | ID={oid}\n"

def search(query, n=10):
    data = api_get("/works", {"search": query, "per_page": n, "sort": "cited_by_count:desc"})
    if "error" in data: return f"❌ API错误: {data['error']}"
    cnt = data.get("meta",{}).get("count",0)
    out = f"🔍 搜索: {query}\n共{cnt}条结果, 显示前{n}条:\n\n"
    for w in data.get("results",[]):
        out += fmt(w)
    return out

def author(name, n=5):
    data = api_get("/authors", {"search": name, "per_page": 3})
    if not data.get("results"): return f"❌ 未找到: {name}"
    a = data["results"][0]
    aid = a["id"].split("/")[-1]
    inst = a.get("last_known_institution",{})
    out = f"👤 {a['display_name']}\n  机构: {inst.get('display_name','?')}\n  h-index: {a.get('summary_stats',{}).get('h_index','?')}\n  论文数: {a.get('works_count',0)}  总被引: {a.get('cited_by_count',0)}\n\n📄 代表作:\n"
    works = api_get(f"/authors/{aid}/works", {"per_page": n, "sort": "cited_by_count:desc"})
    for w in works.get("results",[])[:n]:
        out += fmt(w)
    return out

def cite(work_id, n=5):
    oid = work_id.replace("https://openalex.org/","")
    w = api_get(f"/works/{oid}")
    if "error" in w: return f"❌ {w['error']}"
    out = f"📖 引用 「{w.get('title','')}」 的论文:\n\n"
    refs = api_get(f"/works/{oid}/citations", {"per_page": n})
    for r in refs.get("results",[]):
        cw = r.get("citing_work",{})
        if cw.get("id"): out += fmt(cw)
    return out

def journal(name):
    data = api_get("/sources", {"search": name, "per_page": 3})
    if not data.get("results"): return f"❌ 未找到期刊: {name}"
    s = data["results"][0]
    out = f"📰 {s['display_name']}\n"
    out += f"  ISSN: {s.get('issn','?')}\n"
    out += f"  类型: {s.get('type','?')}\n"
    out += f"  论文数: {s.get('works_count',0)} | 被引: {s.get('cited_by_count',0)}\n"
    out += f"  h-index: {s.get('summary_stats',{}).get('h_index','?')}\n"
    out += f"  OA率: {s.get('is_oa',False)}\n"
    out += f"  主页: {s.get('homepage_url','?')}\n"
    if s.get('apc_prices'):
        apc = s['apc_prices'][0]
        out += f"  APC: {apc.get('price',0)} {apc.get('currency','USD')}\n"
    return out

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 search.py <cmd> <query>")
        print("命令: search | author | cite | journal")
        sys.exit(1)
    cmd, q = sys.argv[1], " ".join(sys.argv[2:])
    print({"search": search, "author": author, "cite": cite, "journal": journal}.get(cmd, lambda x: "未知命令")(q))
