#!/usr/bin/env python3
"""
关羽 V2.1 — 独立资金流扫描器
绕过 akshare HTTP 限制，直连 EastMoney HTTPS + 并行请求

用法:
  python3 guanyu_v2.py              # 完整扫描
  python3 guanyu_v2.py --holdings   # 仅扫描持仓
  python3 guanyu_v2.py --sectors    # 仅扫描板块
"""

import requests
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://push2.eastmoney.com/api/qt"
BASE_HIS = "https://push2his.eastmoney.com/api/qt"
TIMEOUT = 8

# ============================================================
# 工具函数
# ============================================================

def api_get(url, timeout=TIMEOUT):
    """带超时和错误处理的 GET 请求"""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return None

def secid(code):
    """股票代码 → EastMoney secid"""
    return f"{1 if code.startswith('6') else 0}.{code}"

def make_units(val, unit="亿"):
    """格式化资金数值"""
    if unit == "亿":
        return round(val / 100000000, 2)
    elif unit == "万":
        return round(val / 10000, 1)
    return val

# ============================================================
# 1. 概念板块资金流 TOP-N
# ============================================================

def concept_fund_flow(n=10, sort_desc=True):
    """概念板块主力资金流"""
    order = 1 if sort_desc else 0
    url = (
        f"{BASE}/clist/get?pn=1&pz={n}&po={order}&np=1"
        f"&ut=bd1d9ddb04089700cf9c27f6f7426281"
        f"&fltt=2&invt=2&fid=f62&fs=m:90+t:3"
        f"&fields=f2,f3,f4,f12,f14,f62,f66,f184"
    )
    data = api_get(url)
    if not data:
        return []
    items = data.get("data", {}).get("diff", [])
    result = []
    for item in items:
        result.append({
            "name": item.get("f14", "?"),
            "code": item.get("f12", ""),
            "chg": item.get("f3", 0),
            "main_net_in": item.get("f62", 0),
        })
    return result

# ============================================================
# 2. 行业板块资金流 TOP-N
# ============================================================

def industry_fund_flow(n=10, sort_desc=True):
    """行业板块主力资金流"""
    order = 1 if sort_desc else 0
    url = (
        f"{BASE}/clist/get?pn=1&pz={n}&po={order}&np=1"
        f"&ut=bd1d9ddb04089700cf9c27f6f7426281"
        f"&fltt=2&invt=2&fid=f62&fs=m:90+t:2"
        f"&fields=f2,f3,f4,f12,f14,f62,f66,f184"
    )
    data = api_get(url)
    if not data:
        return []
    items = data.get("data", {}).get("diff", [])
    result = []
    for item in items:
        result.append({
            "name": item.get("f14", "?"),
            "code": item.get("f12", ""),
            "chg": item.get("f3", 0),
            "main_net_in": item.get("f62", 0),
        })
    return result

# ============================================================
# 3. 个股资金流（近N日）
# ============================================================

def stock_fund_flow(code, days=3):
    """个股近N日主力资金流"""
    url = (
        f"{BASE_HIS}/stock/fflow/daykline/get"
        f"?secid={secid(code)}"
        f"&fields1=f1,f2,f3,f7"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65"
        f"&lmt={days}"
    )
    data = api_get(url)
    if not data:
        return None
    
    klines = data.get("data", {}).get("klines", [])
    result = []
    for line in klines:
        parts = line.split(",")
        date = parts[0]
        main_net = float(parts[4]) + float(parts[5])  # 大单 + 超大单
        retail = float(parts[2])                       # 小单
        mid = float(parts[3])                          # 中单
        super_big = float(parts[5])                    # 超大单
        big = float(parts[4])                          # 大单
        result.append({
            "date": date,
            "main_net": main_net,       # 主力净流入(元)
            "retail": retail,           # 散户(小单)
            "mid": mid,                 # 中单
            "super_big": super_big,     # 超大单
            "big": big,                 # 大单
        })
    return result

# ============================================================
# 4. 个股实时行情
# ============================================================

def stock_realtime(code):
    """个股实时行情"""
    url = (
        f"{BASE}/stock/get?secid={secid(code)}"
        f"&fields=f43,f44,f45,f46,f170,f171,f47,f48,f50,f51,f52,f60"
    )
    data = api_get(url)
    if not data:
        return None
    d = data.get("data", {})
    price = (d.get("f43", 0) or 0) / 100
    high = (d.get("f44", 0) or 0) / 100
    low = (d.get("f45", 0) or 0) / 100
    open_p = (d.get("f46", 0) or 0) / 100
    prev = (d.get("f60", 0) or 0) / 100
    chg = (d.get("f170", 0) or 0) / 100
    vol = (d.get("f47", 0) or 0)
    amount = (d.get("f48", 0) or 0)
    return {
        "price": price,
        "chg_pct": chg,
        "open": open_p,
        "high": high,
        "low": low,
        "prev": prev,
        "volume": vol,
        "amount": amount,
    }

# ============================================================
# 5. 板块ETF/指数行情 (备用)
# ============================================================

def index_realtime(index_code):
    """指数实时行情"""
    url = (
        f"{BASE}/stock/get?secid={index_code}"
        f"&fields=f43,f44,f45,f46,f170,f171"
    )
    data = api_get(url)
    if not data:
        return None
    d = data.get("data", {})
    return {
        "price": (d.get("f43", 0) or 0) / 100,
        "chg_pct": (d.get("f170", 0) or 0) / 100,
    }

# ============================================================
# 输出格式
# ============================================================

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_fund_flow_table(items, n=10, unit_mul=10000):
    """打印资金流表格"""
    for i, item in enumerate(items[:n]):
        name = item["name"]
        chg = item.get("chg", 0)
        main_net = item.get("main_net_in", 0) / unit_mul
        bar = "🔥" if main_net > 10 else ("🟢" if main_net > 3 else ("🟡" if main_net > 0 else "🔴"))
        print(f"  {i+1:2d}. {bar} {name:14s} {chg:+.2f}%  主力: {main_net:+.1f}亿")

# ============================================================
# 主流程
# ============================================================

def scan_all(holdings=None):
    """完整资金扫描（并行）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n🐉 关羽 V2.1 · 资金流向全景扫描")
    print(f"   {now}  |  数据源: EastMoney HTTPS | 并行请求")
    
    # 大盘（并行）
    indices_list = [("上证", "1.000001"), ("深证", "0.399001"), ("科创50", "1.000688")]
    def _get_idx(name, idx):
        d = index_realtime(idx)
        return (name, d)
    
    print_section("📊 大盘")
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(_get_idx, n, i): n for n, i in indices_list}
        for f in as_completed(futures):
            name, d = f.result()
            if d:
                print(f"  {name}: {d['price']:.2f}  {d['chg_pct']:+.2f}%")
    
    # 概念+行业板块（并行）
    def _get_sectors():
        return concept_fund_flow(10), industry_fund_flow(10), industry_fund_flow(5, sort_desc=False)
    
    concepts, industries, out_industries = None, None, None
    with ThreadPoolExecutor(max_workers=1) as ex:
        f = ex.submit(_get_sectors)
        concepts, industries, out_industries = f.result()
    
    print_section("🔬 概念板块·主力净流入TOP10")
    if concepts:
        print_fund_flow_table(concepts)
    
    print_section("🏭 行业板块·主力净流入TOP5")
    if industries:
        print_fund_flow_table(industries, 5)
    
    print_section("📉 行业板块·主力净流出TOP5")
    if out_industries:
        print_fund_flow_table(out_industries, 5)
    
    # 持仓个股（并行）
    if holdings:
        print_section("📦 持仓个股·主力资金")
        def _get_stock(name, code):
            rt = stock_realtime(code)
            flow = stock_fund_flow(code, 3)
            return (name, code, rt, flow)
        
        results = []
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(_get_stock, n, c): (n, c) for n, c in holdings}
            for f in as_completed(futures):
                name, code, rt, flow = f.result()
                # Keep original order
                results.append((name, code, rt, flow))
        
        # Sort by original order
        order = {c: i for i, (_, c) in enumerate(holdings)}
        results.sort(key=lambda x: order.get(x[1], 99))
        
        for name, code, rt, flow in results:
            if rt:
                price = rt['price']
                chg = rt['chg_pct']
                amt = (rt.get('amount', 0) or 0) / 1e8
                bar = "🔴" if chg < -2 else ("🟢" if chg > 0 else "🟡")
                emoji = "🚀" if chg > 3 else ("💀" if chg < -3 else ("🔻" if chg < 0 else ""))
                
                if flow and len(flow) > 0:
                    today_main = make_units(flow[-1]["main_net"])
                    total_main = make_units(sum(f["main_net"] for f in flow))
                    main_str = f"今日主力: {today_main:+.1f}亿  3日: {total_main:+.1f}亿"
                else:
                    main_str = "无数据"
                
                print(f"  {bar} {name:8s} {price:.2f} {chg:+.2f}%{emoji} | {main_str} | 成交{amt:.1f}亿")
    
    # 总结
    print_section("🎯 关羽判定")
    if concepts:
        top3 = [c['name'] for c in concepts[:3]]
        print(f"  资金主攻: {' → '.join(top3)}")
    if industries:
        top_in = industries[0] if industries else {}
        top_out = out_industries[0] if out_industries else {}
        print(f"  行业流入第1: {top_in.get('name','?')}")
        print(f"  行业流出第1: {top_out.get('name','?')}")
    print()

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    # 默认持仓列表
    DEFAULT_HOLDINGS = [
        ("华天科技", "002185"),
        ("完美世界", "002624"),
        ("云天化", "600096"),
        ("楚江新材", "002171"),
        ("海特高新", "002023"),
        ("中工国际", "002051"),
    ]
    
    args = sys.argv[1:]
    if "--holdings" in args:
        scan_all(holdings=DEFAULT_HOLDINGS)
    elif "--sectors" in args:
        holdings = None
        scan_all(holdings=None)
    else:
        scan_all(holdings=DEFAULT_HOLDINGS)
