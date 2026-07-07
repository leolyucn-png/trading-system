#!/usr/bin/env python3
"""
秦始皇 v2.0 · GATE机械化模块
================================
判据(锁死):
 🔴 红灯: 沪深300当日跌幅 > 2% → 仓位上限30% · 禁止T+1
 🟢 绿灯: 非红灯 且 收盘 > 20日均线 → 仓位上限80%
 🟡 黄灯: 非红灯 且 收盘 <= 20日均线 → 仓位上限60%

输出: qinshihuang_gate.json
 龙虾 + 关羽guanyu_status.json → 双文件决定实盘权限
"""

import json, datetime as dt, requests

TIMEOUT = 6; MA_N = 20; RED_DROP = -2.0
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}

def parse_em(raw):
    try:
        ks = json.loads(raw)["data"]["klines"]
        out = [(k.split(",")[0], float(k.split(",")[1])) for k in ks]
        return out if len(out) >= MA_N + 1 else None
    except: return None

def parse_sina(raw):
    try:
        ks = json.loads(raw)
        out = [(k["day"], float(k["close"])) for k in ks]
        return out if len(out) >= MA_N + 1 else None
    except: return None

def decide(closes):
    dates = [c[0] for c in closes]; px = [c[1] for c in closes]
    today, prev = px[-1], px[-2]
    day_pct = (today/prev-1)*100; ma = sum(px[-MA_N:])/MA_N
    if day_pct < RED_DROP: gate, cap, t1 = "红", 30, False
    elif today > ma: gate, cap, t1 = "绿", 80, True
    else: gate, cap, t1 = "黄", 60, True
    return {"date": dates[-1], "index_close": round(today,2),
        "day_pct": round(day_pct,2), f"ma{MA_N}": round(ma,2),
        "gate": gate, "position_cap_pct": cap, "t1_allowed": t1}

def _get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        return r.text if r.status_code == 200 and r.text else None
    except: return None

def fetch():
    em = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000300&klt=101&fqt=1&lmt=40&fields1=f1,f2,f3&fields2=f51,f53"
    raw = _get(em)
    data = parse_em(raw) if raw else None
    if data: return data, "东财"
    sina = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=sh000300&scale=240&ma=no&datalen=40"
    raw = _get(sina)
    data = parse_sina(raw) if raw else None
    return (data, "新浪") if data else (None, "盲区")

if __name__ == "__main__":
    closes, source = fetch()
    now = dt.datetime.now().isoformat(timespec="seconds")
    if closes is None:
        try:
            with open("qinshihuang_gate.json", encoding="utf-8") as f:
                old = json.load(f)
            dg = {"绿": ("黄",60), "黄": ("红",30), "红": ("红",30)}
            g, cap = dg[old["gate"]]
            status = {**old, "gate": g, "position_cap_pct": cap,
                "t1_allowed": False, "source": "盲区(沿用昨日并降一档)", "timestamp": now}
        except:
            status = {"gate":"红","position_cap_pct":30,"t1_allowed":False,
                "source":"盲区(无历史)","timestamp":now}
    else:
        status = {**decide(closes), "source": source, "timestamp": now}
    
    with open("qinshihuang_gate.json","w",encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    
    icon = {"绿":"🟢","黄":"🟡","红":"🔴"}[status["gate"]]
    print("="*52)
    print(f"👑 秦始皇 v2.0 · {now} (源:{status['source']})")
    if "index_close" in status:
        print(f" 沪深300: {status['index_close']} {status['day_pct']:+.2f}% MA{MA_N}={status[f'ma{MA_N}']}")
    print(f" GATE: {icon} {status['gate']}灯 仓位{status['position_cap_pct']}% T+1{'允许' if status['t1_allowed'] else '禁止'}")
    print("="*52)
