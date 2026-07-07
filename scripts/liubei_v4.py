#!/usr/bin/env python3
"""
刘备 v4.0 · 多源催化搜证模块
================================
职责: 给定关键词, 从多个中文财经快讯源拉取近期消息,
 本地过滤匹配, 输出带时间和出处的证据清单。

多源: 财联社电报 → 东财7×24快讯 → 新浪财经滚动
盲区: 全源断 → liubei_status.json 标记, 催化无法查证→降级纸面

用法:
 python liubei_v4.py 融捷
 python liubei_v4.py 融捷 锂价
 python liubei_v4.py --health
"""

import json, sys, datetime as dt, requests

TIMEOUT = 6; FETCH_N = 60
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.cls.cn/"}

def _get(url, headers=HEADERS):
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        return r.text if r.status_code == 200 and r.text else None
    except: return None

def parse_cls(raw):
    try:
        rows = json.loads(raw)["data"]["roll_data"]
        return [{"time": dt.datetime.fromtimestamp(r["ctime"]).strftime("%m-%d %H:%M"),
                 "title": (r.get("title") or r.get("content","")).strip(),
                 "source": "财联社"} for r in rows] or None
    except: return None

def parse_em(raw):
    try:
        rows = json.loads(raw)["data"]["fastNewsList"]
        return [{"time": str(r.get("showTime") or r.get("updateTime",""))[:16],
                 "title": (r.get("title") or "").strip(),
                 "source": "东财快讯"} for r in rows] or None
    except: return None

def parse_sina(raw):
    try:
        rows = json.loads(raw)["result"]["data"]
        return [{"time": dt.datetime.fromtimestamp(int(r["ctime"])).strftime("%m-%d %H:%M"),
                 "title": r.get("title","").strip(),
                 "source": "新浪财经"} for r in rows] or None
    except: return None

def keyword_filter(items, keywords):
    return [it for it in items if it["title"] and any(k in it["title"] for k in keywords)]

def fetch_cls():
    raw = _get(f"https://www.cls.cn/nodeapi/updateTelegraphList?rn={FETCH_N}")
    return parse_cls(raw) if raw else None

def fetch_em():
    url = f"https://np-listapi.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&pageSize={FETCH_N}&sortEnd=&req_trace=1"
    raw = _get(url, {"User-Agent": "Mozilla/5.0"})
    return parse_em(raw) if raw else None

def fetch_sina():
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num={FETCH_N}"
    raw = _get(url, {"User-Agent": "Mozilla/5.0"})
    return parse_sina(raw) if raw else None

def parse_ths(raw):
    """同花顺7x24: data.list = [{ctime(秒), title}, ...]"""
    try:
        rows = json.loads(raw)["data"]["list"]
        out = [{"time": dt.datetime.fromtimestamp(int(r["ctime"])).strftime("%m-%d %H:%M"),
                 "title": (r.get("title") or "").strip(), "source": "同花顺"} for r in rows]
        return out or None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

def fetch_ths():
    url = f"https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=&track=website&pagesize={FETCH_N}"
    raw = _get(url, {"User-Agent": "Mozilla/5.0", "Referer": "https://news.10jqka.com.cn/"})
    return parse_ths(raw) if raw else None

SOURCES = [("财联社", fetch_cls), ("东财快讯", fetch_em), ("新浪财经", fetch_sina), ("同花顺", fetch_ths)]

def gather():
    pool, health = [], {}
    for name, fn in SOURCES:
        try: items = fn()
        except: items = None
        if items: pool.extend(items); health[name] = f"OK({len(items)}条)"
        else: health[name] = "盲区"
    return pool, health

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    health_only = "--health" in sys.argv

    pool, health = gather()
    ok_sources = [k for k,v in health.items() if v.startswith("OK")]
    status = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "sources": health, "evidence_available": bool(ok_sources),
        "note": "搜证可用" if ok_sources else "全源盲区→催化无法查证→降级纸面"}
    with open("liubei_status.json","w",encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print("="*56)
    print(f"🤝 刘备 v4.0 · {status['timestamp']}")
    for k,v in health.items():
        mark = "✅" if v.startswith("OK") else "🔴"
        print(f" {mark} {k}: {v}")
    print(f" 搜证: {'✅' if ok_sources else '🔴 全源盲区'}")
    print("="*56)

    if health_only: sys.exit(0)
    if not args: print("用法: python liubei_v4.py <关键词>"); sys.exit(0)
    if not ok_sources: print("无可用源。"); sys.exit(0)

    hits = keyword_filter(pool, args)
    print(f"\n🔍 {args} · 命中{len(hits)}条:")
    for h in hits[:15]:
        print(f" [{h['time']}] ({h['source']}) {h['title']}")
    if not hits:
        print(" 无命中。查证不到出处→登记为不合格纸面对照。")
