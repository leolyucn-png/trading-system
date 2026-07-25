#!/usr/bin/env python3
"""
关羽 v4.0 · 多源容灾数据模块
================================
职责: 只做眼睛——取数、判源、报健康状态。不选股、不决策。

四线架构(每线多源自动切换):
 线1 ETF方向 : 新浪 → 腾讯 → 东财HTTPS
 线2 K线量价 : 新浪K线 → (东财K线, 预留)
 线3 个股资金流 : 东财HTTPS(唯一源, 断=该线盲区, 自动回退到线2推算)
 线4 板块暗流 : 东财HTTPS(概念板块主力净流入)

输出:
 guanyu_status.json —— 机器可读健康状态, 龙虾读它决定当天权限:
 "live_trade_permitted": true/false
 规则: 线1 OK 且 线4 OK → true; 否则 false(盲区禁实盘)

用法:
 pip install requests
 python guanyu_v4.py         # 全线扫描
 python guanyu_v4.py --health # 只做健康检查(盘前跑一次)
"""

import json, sys, time, os, datetime as dt
import requests

TIMEOUT = 6; RETRY = 2
HEADERS_SINA = {"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
HEADERS_STD = {"User-Agent": "Mozilla/5.0"}

ETF_POOL = {
    "sh512480":"半导体ETF","sh515790":"光伏ETF","sh512690":"酒ETF",
    "sh512170":"医疗ETF","sh512880":"证券ETF","sh516160":"新能源ETF",
    "sh512400":"有色ETF","sh512660":"军工ETF","sh515880":"通信ETF",
    "sh562500":"机器人ETF","sz159770":"机器人AI",
    "sz159819":"AI_ETF","sh512800":"银行ETF","sz159928":"消费ETF",
    "sz159865":"养殖ETF","sh512010":"医药ETF","sz159852":"软件ETF",
}

def _get(url, headers):
    for _ in range(RETRY+1):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            if r.status_code == 200 and r.text: return r.text
        except: pass
        time.sleep(0.5)
    return None

def parse_sina(raw):
    try:
        body = raw.split('="')[1].rstrip('";\n'); f = body.split(",")
        prev, price, vol = float(f[2]), float(f[3]), float(f[8])
        if prev<=0 or price<=0: return None
        return {"name":f[0],"price":price,"pct":round((price/prev-1)*100,2),"vol":vol}
    except: return None

def parse_tencent(raw):
    try:
        body = raw.split('="')[1].rstrip('";\n'); f = body.split("~")
        price, prev, vol = float(f[3]), float(f[4]), float(f[6])*100
        if prev<=0 or price<=0: return None
        return {"name":f[1],"price":price,"pct":round((price/prev-1)*100,2),"vol":vol}
    except: return None

def parse_em(raw):
    try:
        d = json.loads(raw)["data"]; price, prev = d["f43"]/100, d["f60"]/100
        if prev<=0 or price<=0: return None
        return {"name":d.get("f58",""),"price":price,"pct":round((price/prev-1)*100,2),"vol":float(d.get("f47",0))*100}
    except: return None

def parse_boards(raw):
    try:
        rows = json.loads(raw)["data"]["diff"]
        return [{"board":r["f14"],"pct":r["f3"]/100 if isinstance(r["f3"],(int,float)) else None,"main_inflow":r.get("f62")} for r in rows]
    except: return None

class Line:
    def __init__(self, name, sources):
        self.name=name; self.sources=sources; self.status="盲区"; self.active_source=None; self.data=None
    def fetch(self):
        for sn, fn in self.sources:
            try: data = fn()
            except: data = None
            if data: self.data=data; self.active_source=sn; self.status="OK" if sn==self.sources[0][0] else "降级"; return
        self.status="盲区"

def _etf_via(parse_fn, url_builder, headers):
    def fn():
        out = {}
        for code, name in ETF_POOL.items():
            raw = _get(url_builder(code), headers)
            q = parse_fn(raw) if raw else None
            if q: q["name"]=name; out[code]=q
        return out if len(out)>=len(ETF_POOL)//2 else None
    return fn

def em_secid(code):
    return ("1." if code.startswith("sh") else "0.") + code[2:]

line1 = Line("线1·ETF方向", [
    ("新浪", _etf_via(parse_sina, lambda c: f"https://hq.sinajs.cn/list={c}", HEADERS_SINA)),
    ("腾讯", _etf_via(parse_tencent, lambda c: f"https://qt.gtimg.cn/q={c}", HEADERS_STD)),
    ("东财", _etf_via(parse_em, lambda c: f"https://push2.eastmoney.com/api/qt/stock/get?secid={em_secid(c)}&fields=f43,f47,f58,f60", HEADERS_STD)),
])

def fetch_boards():
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=200&po=1&np=1&fltt=2&fid=f62&fs=m:90+t:3&fields=f3,f14,f62"
    h = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Referer": "https://quote.eastmoney.com/"}
    raw = _get(url, h)
    return parse_boards(raw) if raw else None

def dark_flow(boards):
    out = [b for b in boards if b["pct"] is not None and b["main_inflow"] is not None and b["pct"]<0 and b["main_inflow"]>0]
    return sorted(out, key=lambda x: -x["main_inflow"])[:10]

line4 = Line("线4·板块暗流", [("东财", fetch_boards)])

def verdict(lines):
    l1_ok = lines["线1·ETF方向"].status in ("OK","降级")
    l4_ok = lines["线4·板块暗流"].status in ("OK","降级")
    permitted = l1_ok and l4_ok
    return {"timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "lines": {k:{"status":v.status,"source":v.active_source} for k,v in lines.items()},
        "live_trade_permitted": permitted,
        "note": "全线可用" if permitted else "存在盲区 → 今日禁止实盘指令, 信号只许登记为纸面"}

if __name__ == "__main__":
    health_only = "--health" in sys.argv
    lines = {"线1·ETF方向": line1, "线4·板块暗流": line4}
    for ln in lines.values(): ln.fetch()
    status = verdict(lines)
    with open("guanyu_status.json","w",encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    
    print("="*56)
    print(f"⚔️ 关羽 v4.0 · {status['timestamp']}")
    for name, info in status["lines"].items():
        mark = {"OK":"✅","降级":"⚠️","盲区":"🔴"}[info["status"]]
        src = f"(源:{info['source']})" if info["source"] else ""
        print(f" {mark} {name}: {info['status']} {src}")
    print(f" 实盘许可: {'✅' if status['live_trade_permitted'] else '🔴 否'}")
    if status['live_trade_permitted']:
        etfs = sorted(line1.data.values(), key=lambda x:-x["pct"])
        print("\n📈 线1 ETF方向:")
        for q in etfs: print(f" {q['name']:<8} {q['pct']:+.2f}%")
        flows = dark_flow(line4.data)
        print("\n🌊 线4 暗流:")
        if flows:
            for b in flows: print(f" {b['board']:<10} {b['pct']:+.2f}% 主力{b['main_inflow']/1e8:.2f}亿")
        
        # 🆕 暗流历史存档 (每日累积, 不覆盖)
        flow_dir = os.path.expanduser("~/memory/暗流历史")
        os.makedirs(flow_dir, exist_ok=True)
        today = dt.datetime.now().strftime('%Y-%m-%d')
        rec = {"timestamp": dt.datetime.now().isoformat(timespec="minutes"),
               "etf_top5": [(q['name'], q['pct']) for q in etfs[:5]],
               "dark_flow": [{"board": b['board'], "pct": b['pct'], "inflow_yi": round(b['main_inflow']/1e8, 2)} for b in (flows or [])[:10]]}
        path = os.path.join(flow_dir, f"{today}.json")
        existing = []
        if os.path.exists(path):
            try:
                with open(path) as f: existing = json.load(f)
            except: pass
        existing.append(rec)
        with open(path, 'w') as f: json.dump(existing, f, ensure_ascii=False)
    
    print("="*56)
