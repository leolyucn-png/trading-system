#!/usr/bin/env python3
"""
关羽 V3.1 — 多线并存资金扫描器
四线并行:
  线1: ETF方向 (Sina — 始终稳定)
  线2: 3日K线量价 (替代资金流 — EastMoney挂了时用)
  线3: 个股资金流 (EastMoney fflow — 通时用)
  线4: 🆕 暗流板块+自动扫成分股 (EastMoney概念 — 找最强领涨股)
铁律: 哪条线通就用哪条。不通不硬选。多线并存。
"""

import requests, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 10
BLIND = {}

def sf(v, d=0):
    try: return float(v) if v else d
    except: return d

# ============================================================
# 线1: ETF方向 (Sina)
# ============================================================

ETF_MAP = {
    "养殖": "sz159865", "半导体": "sh512480", "芯片": "sz159995",
    "科创50": "sh588000", "医药": "sh512010", "军工": "sh512660",
    "机器人": "sh562500", "证券": "sh512880", "有色": "sh512400",
    "游戏": "sz159869", "消费": "sz159928", "国防": "sh512670",
    "酒": "sh512690", "新能源车": "sh515030", "通信": "sh515880",
}

def line1_etf():
    """线1: ETF方向"""
    try:
        codes = ",".join(ETF_MAP.values())
        r = requests.get(f"http://hq.sinajs.cn/list={codes}",
                         headers={"Referer": "http://finance.sina.com.cn"}, timeout=5)
        r.encoding = 'gbk'
        result = {}
        for line in r.text.strip().split('\n'):
            if not line.strip(): continue
            parts = line.split('"')[1].split(',')
            px, prev, vol = float(parts[3]), float(parts[2]), int(parts[8]) // 100
            chg = (px - prev) / prev * 100
            for en, ec in ETF_MAP.items():
                if ec.split('.')[-1] in line.lower():
                    result[en] = (chg, vol, px)
        return result
    except:
        return None

# ============================================================
# 线2: K线量价 (替代资金流)
# ============================================================

def line2_kline_volume(code):
    """线2: 个股K线量价推断资金方向"""
    mkt = "sh" if code.startswith('6') else "sz"
    try:
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={mkt}{code}&scale=240&datalen=5"
        r = requests.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=6)
        data = json.loads(r.text)
        if len(data) < 3: return None
        d2, d1, d0 = data[-3], data[-2], data[-1]
        c2, c1, c0 = float(d2['close']), float(d1['close']), float(d0['close'])
        v2, v1, v0 = int(d2['volume']), int(d1['volume']), int(d0['volume'])
        chg_fri = (c1 - c2) / c2 * 100
        chg_tdy = (c0 - c1) / c1 * 100
        vr = v0 / v1 if v1 > 0 else 1
        if chg_tdy > 0 and vr > 1.2: sig = "🟢主力买"
        elif chg_tdy > 0 and vr < 0.8: sig = "🟡散户追"
        elif chg_tdy < -2 and vr > 1.3: sig = "🔴主力卖"
        elif chg_tdy < 0 and vr < 0.6: sig = "🗡️卖压衰竭"
        elif chg_tdy < 0 and vr < 0.9: sig = "🟡缩量等底"
        else: sig = f"量比{vr:.1f}"
        return (chg_fri, chg_tdy, v1 // 100, v0 // 100, vr, sig)
    except:
        return None

def line2_scan(holdings):
    """线2: 批量扫描持仓量价"""
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(line2_kline_volume, c): (n, c) for n, c in holdings}
        for f in as_completed(futures):
            n, c = futures[f]
            results[(n, c)] = f.result()
    return results

# ============================================================
# 线3: 个股资金流 (EastMoney fflow)
# ============================================================

def line3_fflow(code, days=5):
    """线3: 个股主力资金流"""
    mkt = 1 if code.startswith('6') else 0
    url = f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={mkt}.{code}&fields1=f1&fields2=f51,f52,f53,f54,f55,f56&lmt={days}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200: return None
        k = r.json().get('data', {}).get('klines', [])
        if not k: return None
        total = sum(float(p.split(',')[3]) + float(p.split(',')[4]) for p in k)
        today = float(k[-1].split(',')[3]) + float(k[-1].split(',')[4])
        return (total / 1e8, today / 1e8, len(k))
    except:
        return None

# ============================================================
# 线4: 🆕 暗流板块 + 自动扫成分股
# ============================================================

def line4_darkflow():
    """线4: 找跌但有资金买的板块 → 自动扫最强成分股"""
    # 拉全部概念板块
    url = ("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=200&po=1"
           "&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
           "&fltt=2&invt=2&fid=f3&fs=m:90+t:3"
           "&fields=f2,f3,f12,f14,f62")
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200: return None
        items = r.json()['data']['diff']
    except:
        return None

    def is_med(n):
        return any(k in n for k in ['药', 'CAR', 'CRO', '细胞', '免疫', '减肥', '疫苗', '流感', '生物', '医疗', '病毒', '防治'])
    def is_junk(n):
        return any(k in n for k in ['昨', '连板', '打板', 'ST', '昨日'])

    # 找暗流: 板块涨=0 且有资金
    flows = []
    for it in items:
        n, c = it['f14'], sf(it['f3'])
        m = sf(it['f62']) / 1e8
        if not is_med(n) and not is_junk(n):
            flows.append((n, c, m, it['f12']))

    # 分类
    dark = [(n, c, m, bid) for n, c, m, bid in flows if c < 0 and m > 1]
    stealth = [(n, c, m, bid) for n, c, m, bid in flows if 0 <= c < 0.5 and m > 3]

    # 扫暗流板块成分股
    def scan_components(bid):
        url2 = f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=15&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=b:{bid}&fields=f2,f3,f14,f43,f62"
        try:
            r2 = requests.get(url2, timeout=8)
            if r2.status_code != 200: return []
            stocks = r2.json()['data']['diff']
            valid = [(s['f14'], sf(s['f3']), sf(s.get('f62', 0)) / 1e8)
                     for s in stocks
                     if sf(s.get('f43', 0)) / 100 > 1 and sf(s.get('f43', 0)) / 100 < 5000]
            valid.sort(key=lambda x: -x[1])
            return valid[:5]
        except:
            return []

    dark_with_stocks = []
    for n, c, m, bid in dark[:6]:
        stocks = scan_components(bid) if m > 1 else []
        dark_with_stocks.append((n, c, m, stocks))

    stealth_best = [(n, c, m) for n, c, m, _ in stealth[:5]]
    return dark_with_stocks, stealth_best

# ============================================================
# 主输出
# ============================================================

def scan(holdings=None):
    t0 = time.time()
    now = time.strftime("%H:%M")
    blind_lines = []

    print("━" * 65)
    print(f"🐉 关羽 V3.1 · 四线并行 | {now}")
    print("━" * 65)

    # === 线1: ETF ===
    print("\n📈 线1 · ETF方向")
    etfs = line1_etf()
    if etfs:
        up = [(n, c) for n, (c, v, p) in etfs.items() if c > 0.3]
        down = [(n, c) for n, (c, v, p) in etfs.items() if c < -0.3]
        up.sort(key=lambda x: -x[1])
        down.sort(key=lambda x: x[1])
        print(f"  🟢: {' '.join(f'{n}{c:+.1f}%' for n,c in up[:6])}")
        print(f"  🔴: {' '.join(f'{n}{c:+.1f}%' for n,c in down[:6])}")
    else:
        blind_lines.append("线1")
        print("  ❌ 不通")

    # === 线2: K线量价 ===
    if holdings:
        print("\n📊 线2 · K线量价推断")
        kline_data = line2_scan(holdings)
        buys, sells, exhaust = [], [], []
        for (n, c), r in kline_data.items():
            if not r: continue
            cf, ct, vf, vt, vr, sig = r
            bar = '🚀' if ct > 3 else ('🟢' if ct > 0 else ('🔴' if ct < -3 else '🟡'))
            print(f"  {bar} {n:8s} {ct:+5.1f}% {sig}")
            if '主力买' in sig: buys.append(n)
            if '主力卖' in sig: sells.append(n)
            if '卖压衰竭' in sig: exhaust.append(n)
        if buys: print(f"  → 主力买: {', '.join(buys)}")
        if sells: print(f"  → 主力卖: {', '.join(sells)}")
    else:
        blind_lines.append("线2")

    # === 线3: fflow ===
    if holdings:
        print("\n💸 线3 · 个股资金流(fflow)")
        fflow_ok = False
        for n, c in holdings[:6]:
            r = line3_fflow(c, 5)
            if r:
                total, today, days = r
                bar = '🔴' if total < 0 else '🟢'
                print(f"  {bar} {n:8s} {days}日累计{total:+.1f}亿  今日{today:+.1f}亿")
                fflow_ok = True
            else:
                print(f"  ⚠️ {n:8s} 不通")
        if not fflow_ok:
            blind_lines.append("线3(fflow)")
    else:
        blind_lines.append("线3")

    # === 线4: 暗流 ===
    print("\n🔍 线4 · 🆕 暗流板块+扫成分股")
    dark_flows = line4_darkflow()
    if dark_flows:
        dark_with, stealth = dark_flows
        print(f"\n  🗡️ 跌+资金买({len(dark_with)}个):")
        for n, c, m, stocks in dark_with:
            print(f"     🔥 {n}: {c:+.2f}% 主力{m:+.1f}亿")
            if stocks:
                for sn, sc, sm in stocks[:4]:
                    bar2 = '🚀' if sc > 10 else ('🟢' if sc > 0 else '🔴')
                    print(f"        {bar2} {sn:8s} {sc:+.2f}%")

        if stealth:
            print(f"\n  👻 横盘+暗中建仓({len(stealth)}个):")
            for n, c, m in stealth:
                print(f"     👻 {n}: {c:+.2f}% 主力{m:+.1f}亿")
    else:
        blind_lines.append("线4(概念API)")
        print("  ❌ 不通")

    # === 状态 ===
    elapsed = time.time() - t0
    print(f"\n{'━'*65}")
    if blind_lines:
        print(f"🔴 盲线: {', '.join(blind_lines)}")
    else:
        print("🟢 四线全通")
    print(f"   耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    DEFAULT = [
        ("华天科技", "002185"),
        ("完美世界", "002624"),
        ("云天化", "600096"),
        ("楚江新材", "002171"),
        ("海特高新", "002023"),
        ("中工国际", "002051"),
    ]
    scan(DEFAULT)
