#!/usr/bin/env python3
"""
关羽 V3.4 — 全市场ETF扫描 + 四线 + 半导体7环节追踪 🆕
四线并行:
  线1: ETF方向 (Sina · 38个行业ETF全覆盖)
  线2: 3日K线量价 (替代资金流)
  线3: 个股资金流 (EastMoney fflow)
  线4: 暗流板块+暴跌复苏检测 (行业+概念双扫)
  线5: 🆕 半导体7环节合成追踪 (Sina龙头股合成，永远稳定)
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
    # 科技/成长
    "半导体": "sh512480", "芯片": "sz159995", "科创50": "sh588000",
    "消费电子": "sz159732", "软件": "sz159852", "人工智能": "sh515070",
    "云计算": "sz159890", "通信": "sh515880",
    # 医药
    "医药": "sh512010", "创新药": "sh515120", "医疗器械": "sz159883",
    # 军工/航天
    "军工": "sh512660", "国防": "sh512670",
    # 制造/新能源
    "新能源车": "sh515030", "新能源": "sh516160", "光伏": "sh515790",
    "碳中和": "sh560550", "电力": "sz159611",
    "机器人": "sh562500", "汽车": "sh516110",
    # 周期
    "有色": "sh512400", "煤炭": "sh515220", "化工": "sh516020",
    "钢铁": "sh515210", "建材": "sz159745",
    # 金融
    "证券": "sh512880", "银行": "sh512800",
    # 消费/传媒
    "消费": "sz159928", "酒": "sh512690", "家电": "sz159996",
    "旅游": "sz159766", "农业": "sz159825", "养殖": "sz159865",
    "游戏": "sz159869", "传媒": "sz159805", "影视": "sz159855",
    # 基建/地产
    "基建": "sh516970", "地产": "sh512200",
}

def line1_etf():
    """线1: ETF方向 (Sina)"""
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
# 线2: K线量价 (Sina)
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
# 线3: 个股资金流 (EastMoney — 绕过代理)
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
    except requests.exceptions.ProxyError:
        # 代理不通时直连重试
        try:
            r = requests.get(url, proxies={'http':'','https':''}, timeout=8)
            if r.status_code != 200: return None
            k = r.json().get('data', {}).get('klines', [])
            if not k: return None
            total = sum(float(p.split(',')[3]) + float(p.split(',')[4]) for p in k)
            today = float(k[-1].split(',')[3]) + float(k[-1].split(',')[4])
            return (total / 1e8, today / 1e8, len(k))
        except:
            return None
    except:
        return None

# ============================================================
# 线4: 暗流板块 + 暴跌复苏 + 自动扫成分股
# ============================================================

def _em_get(url, timeout=TIMEOUT):
    """EastMoney请求：走代理 → 不通则直连重试"""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200: return r
    except requests.exceptions.ProxyError:
        pass  # 代理不通，走直连
    try:
        r = requests.get(url, proxies={'http':'','https':''}, timeout=timeout)
        if r.status_code == 200: return r
    except:
        pass
    return None

def _fetch_sectors(fs_filter, label):
    """拉取行业/概念板块数据"""
    url = (f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=250&po=1"
           f"&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
           f"&fltt=2&invt=2&fid=f3&fs={fs_filter}"
           f"&fields=f2,f3,f12,f14,f62")
    r = _em_get(url, TIMEOUT)
    if not r: return []
    try:
        items = r.json()['data']['diff']
        result = []
        for it in items:
            n = it['f14']
            if any(k in n for k in ['昨', '连板', '打板', 'ST', '昨日', '首板']):
                continue
            result.append({
                'name': n, 'chg': sf(it['f3']), 'bid': it['f12'],
                'flow': sf(it['f62']) / 1e8, 'source': label,
            })
        return result
    except:
        return []

def _scan_components(bid):
    """扫板块成分股"""
    url = (f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=15&po=1"
           f"&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
           f"&fltt=2&invt=2&fid=f3&fs=b:{bid}&fields=f2,f3,f14,f43,f62")
    r = _em_get(url, 8)
    if not r: return []
    try:
        stocks = r.json()['data']['diff']
        valid = [(s['f14'], sf(s['f3']), sf(s.get('f62', 0)) / 1e8)
                 for s in stocks
                 if sf(s.get('f43', 0)) / 100 > 1 and sf(s.get('f43', 0)) / 100 < 5000]
        valid.sort(key=lambda x: -x[1])
        return valid[:5]
    except:
        return []

def line4_darkflow():
    """
    线4: 全板块平等扫描 — 禁止白名单/黑名单
    
    三分类:
      🗡️ 暗流     — 价格跌(c<0) + 主力买入(m>0.3亿)
      👻 横盘建仓  — 价格平(0≤c<0.5) + 大额流入(m>3亿)
      🔄 复苏暗流  — 微跌/微涨 + 有资金逆势 = 昨跌今回暖
    """
    sectors = _fetch_sectors('m:90+t:2', '行业') + _fetch_sectors('m:90+t:3', '概念')
    if not sectors:
        return None, None, None

    dark, stealth, recovery = [], [], []
    for s in sectors:
        n, c, m = s['name'], s['chg'], s['flow']
        tag, bid = s['source'], s['bid']

        if c < 0 and m > 0.3:
            dark.append((n, c, m, tag, bid))
        elif 0 <= c < 0.5 and m > 3:
            stealth.append((n, c, m, tag, bid))
        elif 0 <= c < 0.5 and 0.5 < m <= 3:
            recovery.append((n, c, m, tag, bid))

    def dedup(items):
        seen, out = set(), []
        for item in items:
            if item[0] not in seen:
                seen.add(item[0]); out.append(item)
        return out

    dark = sorted(dedup(dark), key=lambda x: -x[2])[:8]
    stealth = sorted(dedup(stealth), key=lambda x: -x[2])[:5]
    recovery = sorted(dedup(recovery), key=lambda x: -x[2])[:6]

    dark_out = [(n, c, m, tag, _scan_components(bid)) for n, c, m, tag, bid in dark]
    stealth_out = [(n, c, m, tag) for n, c, m, tag, _ in stealth]
    recovery_out = [(n, c, m, tag, _scan_components(bid)) for n, c, m, tag, bid in recovery]

    return dark_out, stealth_out, recovery_out

# ============================================================
# 线5: 🆕 半导体7环节合成追踪 (Sina龙头股，永远稳定)
# ============================================================

SEMI_STAGES = {
    '①封测': ['sz002185', 'sz002156', 'sh600584'],
    '②芯片设计': ['sz002049', 'sh603501', 'sz300661'],
    '③晶圆代工': ['sh688981', 'sh688126'],
    '④设备': ['sz002371', 'sh688012', 'sh688037'],
    '⑤材料': ['sh600171', 'sh600460', 'sz300054'],
    '⑥功率/EDA': ['sz300373', 'sz300623'],
    '⑦光通信': ['sz300308', 'sz300502', 'sz300394'],  # 中际旭创/新易盛/天孚
    '⑧储存芯片': ['sh603986', 'sz300672', 'sz300661'],  # 兆易创新/国科微/圣邦
}

SEMI_STOCK_NAMES = {
    'sz002185': '华天科技', 'sz002156': '通富微电', 'sh600584': '长电科技',
    'sz002049': '紫光国微', 'sh603501': '韦尔股份', 'sz300661': '圣邦股份',
    'sh688981': '中芯国际', 'sh688126': '沪硅产业',
    'sz002371': '北方华创', 'sh688012': '中微公司', 'sh688037': '芯源微',
    'sh600171': '上海贝岭', 'sh600460': '士兰微', 'sz300054': '鼎龙股份',
    'sz300373': '扬杰科技', 'sz300623': '捷捷微电',
    'sz300308': '中际旭创', 'sz300502': '新易盛', 'sz300394': '天孚通信',
    'sh603986': '兆易创新', 'sz300672': '国科微',
}

def line5_semi_stages():
    """线5: 半导体7环节合成追踪"""
    all_codes = []
    for codes in SEMI_STAGES.values():
        all_codes.extend(codes)
    
    codes_str = ','.join(all_codes)
    try:
        r = requests.get(f'http://hq.sinajs.cn/list={codes_str}',
                        headers={'Referer': 'http://finance.sina.com.cn'}, timeout=6)
        r.encoding = 'gbk'
    except:
        return None
    
    # Parse prices
    prices = {}
    for line in r.text.strip().split('\n'):
        if not line.strip(): continue
        try:
            fields = line.split('"')[1].split(',')
            if len(fields) < 4: continue
            code_raw = line.split('=')[0].split('_')[-1]
            px = float(fields[3])
            prev = float(fields[2])
            chg = (px - prev) / prev * 100
            for c in all_codes:
                if c.split('.')[-1] in code_raw:
                    prices[c.split('.')[-1]] = (px, chg)
                    break
        except:
            continue
    
    if not prices:
        return None
    
    # Calculate stage averages
    stages_result = {}
    for stage_name, codes in SEMI_STAGES.items():
        chgs = []
        stocks = []
        for c in codes:
            code_key = c.split('.')[-1]
            if code_key in prices:
                px_v, chg_v = prices[code_key]
                stock_name = SEMI_STOCK_NAMES.get(code_key, code_key)
                chgs.append(chg_v)
                stocks.append((stock_name, px_v, chg_v))
        if chgs:
            avg = sum(chgs) / len(chgs)
            stages_result[stage_name] = (avg, stocks)
    
    return stages_result

# ============================================================
# 主输出
# ============================================================

def scan(holdings=None):
    t0 = time.time()
    now = time.strftime("%H:%M")
    blind_lines = []

    print("━" * 65)
    print(f"🐉 关羽 V3.3 · 全市场ETF(38个)+四线 | {now}")
    print("━" * 65)

    # === 线1: ETF ===
    print("\n📈 线1 · ETF方向")
    etfs = line1_etf()
    if etfs:
        up = [(n, c) for n, (c, v, p) in etfs.items() if c > 0.3]
        down = [(n, c) for n, (c, v, p) in etfs.items() if c < -0.3]
        up.sort(key=lambda x: -x[1])
        down.sort(key=lambda x: x[1])
        print(f"  🟢 前10: {' '.join(f'{n}{c:+.1f}%' for n,c in up[:10])}")
        print(f"  🔴 后10: {' '.join(f'{n}{c:+.1f}%' for n,c in down[:10])}")
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

    # === 线5: 半导体7环节 ===
    print("\n🔬 线5 · 🆕 半导体7环节合成追踪")
    semi_stages = line5_semi_stages()
    if semi_stages:
        sorted_stages = sorted(semi_stages.items(), key=lambda x: -x[1][0])
        for stage_name, (avg, stocks) in sorted_stages:
            bar = 'RM' if avg > 8 else ('GR' if avg > 3 else ('YW' if avg > 0 else 'RD'))
            print(f"  {avg:+.1f}% {stage_name}")
            for sn, spx, schg in stocks:
                bar2 = 'RM' if schg > 8 else ('GR' if schg > 3 else ('YW' if schg > 0 else 'RD'))
                if bar2 == 'RM': m2 = 'RM'
                elif bar2 == 'GR': m2 = 'GR'
                else: m2 = 'YW'
                print(f"     {sn:10s} {spx:.2f}  {schg:+.2f}%")
    else:
        print("  ❌ 不通")

    # === 线4: 暗流+暴跌复苏 ===
    print("\n🔍 线4 · 暗流+暴跌复苏(行业+概念双扫)")
    dark_flows = line4_darkflow()
    if dark_flows and dark_flows[0] is not None:
        dark_with, stealth, recovery = dark_flows

        if dark_with:
            print(f"\n  🗡️ 跌+资金买({len(dark_with)}个):")
            for n, c, m, tag, stocks in dark_with[:6]:
                print(f"     🔥 [{tag}] {n}: {c:+.2f}% 主力{m:+.1f}亿")
                for sn, sc, sm in stocks[:3]:
                    bar2 = '🚀' if sc > 10 else ('🟢' if sc > 0 else '🔴')
                    print(f"        {bar2} {sn:8s} {sc:+.2f}%")

        if stealth:
            print(f"\n  👻 横盘+暗中建仓({len(stealth)}个):")
            for n, c, m, tag in stealth:
                print(f"     👻 [{tag}] {n}: {c:+.2f}% 主力{m:+.1f}亿")

        if recovery:
            print(f"\n  🔄 复苏暗流({len(recovery)}个) ⚠️")
            for n, c, m, tag, stocks in recovery[:6]:
                bar3 = '🟢' if c > 0 else '🟡'
                print(f"     🔄 [{tag}] {bar3} {n}: {c:+.2f}% 主力{m:+.1f}亿")
                for sn, sc, sm in stocks[:3]:
                    bar2 = '🚀' if sc > 10 else ('🟢' if sc > 0 else '🔴')
                    print(f"        {bar2} {sn:8s} {sc:+.2f}%")
        else:
            print("\n  (无复苏暗流板块)")
    else:
        blind_lines.append("线4")
        print("  ❌ 不通")

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
