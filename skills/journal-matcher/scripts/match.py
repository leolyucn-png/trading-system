#!/usr/bin/env python3
"""期刊匹配器 — 基于论文关键词推荐投稿期刊"""
import sys, requests

API = "https://api.openalex.org"
H = {"User-Agent": "LEO-OpenAlex/1.0 (mailto:leolyucn@gmail.com)"}

# 预置SSCI期刊数据库（含审稿周期和接收率）
JOURNALS = {
    "New Media & Society": {"sjr":"Q1","h":210,"weeks":12,"rate":"15-20%","cat":"Communication","fmt":"SAGE"},
    "Social Media + Society": {"sjr":"Q1","h":98,"weeks":8,"rate":"18-22%","cat":"Communication","fmt":"SAGE"},
    "Big Data & Society": {"sjr":"Q1","h":65,"weeks":10,"rate":"20-25%","cat":"Communication","fmt":"SAGE"},
    "Convergence": {"sjr":"Q2","h":42,"weeks":8,"rate":"25-30%","cat":"Communication","fmt":"SAGE"},
    "Information, Communication & Society": {"sjr":"Q1","h":108,"weeks":10,"rate":"12-18%","cat":"Communication/Sociology","fmt":"Taylor & Francis"},
    "Games and Culture": {"sjr":"Q2","h":40,"weeks":6,"rate":"25-30%","cat":"Cultural Studies","fmt":"SAGE"},
    "International Journal of Communication": {"sjr":"Q2","h":55,"weeks":6,"rate":"20-25%","cat":"Communication","fmt":"USC Annenberg"},
    "Journal of Communication": {"sjr":"Q1","h":196,"weeks":14,"rate":"10-15%","cat":"Communication","fmt":"Oxford"},
    "Finance Research Letters": {"sjr":"Q1","h":72,"weeks":6,"rate":"25-30%","cat":"Finance","fmt":"Elsevier"},
    "Journal of Behavioral Finance": {"sjr":"Q2","h":46,"weeks":8,"rate":"30%","cat":"Finance","fmt":"Taylor & Francis"},
    "Pacific-Basin Finance Journal": {"sjr":"Q1","h":75,"weeks":8,"rate":"20-25%","cat":"Finance","fmt":"Elsevier"},
    "Tourism Management": {"sjr":"Q1","h":248,"weeks":16,"rate":"10-15%","cat":"Tourism","fmt":"Elsevier"},
}

def match(abstract):
    """基于关键词匹配期刊"""
    text = abstract.lower()
    # 关键词权重
    scores = {}
    
    keyword_scores = {
        "New Media & Society": {"platform":3, "social media":3, "affective":2, "algorithm":2, "networked":2, "china":1, "digital":1},
        "Social Media + Society": {"social media":3, "platform":2, "china":2, "hashtag":2, "algorithm":2, "user":1, "content":1},
        "Big Data & Society": {"big data":3, "algorithm":2, "platform":2, "computational":2, "governance":2, "surveillance":2},
        "Convergence": {"platform":2, "cultural":2, "media":2, "digital":2, "china":1, "convergence":3},
        "Information, Communication & Society": {"platform":2, "public":2, "government":2, "policy":2, "democracy":2, "china":1},
        "Games and Culture": {"game":3, "gaming":3, "player":2, "digital":1, "culture":2, "play":2},
        "International Journal of Communication": {"china":2, "social media":2, "digital":1, "platform":1, "public":1},
        "Finance Research Letters": {"investor":3, "sentiment":3, "stock":3, "market":3, "finance":2, "volatility":2, "return":2},
        "Journal of Behavioral Finance": {"investor":3, "behavioral":3, "sentiment":2, "bias":2, "finance":2, "decision":2},
        "Pacific-Basin Finance Journal": {"china":3, "a-share":3, "asia":2, "pacific":2, "emerging":2, "market":2},
        "Tourism Management": {"tourism":3, "travel":3, "destination":3, "visitor":2, "tourist":2},
    }
    
    for jname, keywords in keyword_scores.items():
        score = 0
        for word, weight in keywords.items():
            if word in text:
                score += weight
        scores[jname] = score
    
    # 排序
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    
    out = f"📋 根据摘要关键词，推荐投稿期刊排名:\n\n"
    rank = 1
    for jname, score in ranked:
        if score > 0:
            j = JOURNALS.get(jname, {})
            out += f"{'🥇🥇🥇' if rank==1 else '🥈' if rank==2 else '🥉' if rank==3 else f'{rank}.':4s} "
            out += f"{jname:40s} Q={j.get('sjr','?'):4s}  匹配度={score:2d}  审稿≈{j.get('weeks','?')}w  接收率={j.get('rate','?')}\n"
            rank += 1
            if rank > 5: break
    
    if rank == 1:
        out += "\n⚠️ 没有找到匹配的期刊。你的论文可能偏其他方向。\n"
    
    return out

def review_speed(jname):
    j = JOURNALS.get(jname)
    if not j:
        # 尝试模糊匹配
        for key, val in JOURNALS.items():
            if jname.lower() in key.lower():
                j = val
                jname = key
                break
    if j:
        return f"📰 {jname}\n  审稿周期: 约{j['weeks']}周\n  接收率: {j['rate']}\n  学科: {j['cat']}\n  出版商: {j['fmt']}"
    return f"❌ 未找到期刊: {jname}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 match.py <论文标题+摘要>")
        print("   or: python3 match.py speed <期刊名>")
        sys.exit(1)
    if sys.argv[1] == "speed":
        print(review_speed(" ".join(sys.argv[2:])))
    else:
        print(match(" ".join(sys.argv[1:])))
