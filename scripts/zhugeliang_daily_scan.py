#!/usr/bin/env python3
"""
诸葛亮 V2.0 · 长期牛股筛选（每日12:00运行）
============================================
✅ 诸葛亮做: DNA≥70分 → 长期池（持有2周-3月）
✅ 诸葛亮做: 输出合理入场区间 + 季线止损
❌ 不做: 短线买卖建议（那是汉武帝+小乔的事）

DNA五维（0-100）:
  ① 逆势强度(35) — 大盘跌时它不跌的程度
  ② 独立性(25) — 板块跌它涨的表现
  ③ 资金异常(20) — 缩量横盘后的放量信号
  ④ 筹码结构(10) — 市值/机构/股东
  ⑤ 催化质量(10) — 硬逻辑/产业催化

输出: memory/诸葛亮长期池/YYYY-MM-DD.md
"""
import requests, json, os
from datetime import datetime

TIMEOUT = 8

# ==================== 38个ETF ====================
ETF_MAP = {
    '半导体':'sh512480','芯片':'sz159995','消费电子':'sz159732','AI':'sh515070','通信':'sh515880',
    '云计算':'sz159890','软件':'sz159852','科创50':'sh588000',
    '医药':'sh512010','创新药':'sh515120','医疗器械':'sz159883',
    '军工':'sh512660','国防':'sh512670','机器人':'sh562500',
    '新能源车':'sh515030','新能源':'sh516160','光伏':'sh515790','电力':'sz159611',
    '有色':'sh512400','煤炭':'sh515220','化工':'sh516020','钢铁':'sh515210',
    '证券':'sh512880','银行':'sh512800',
    '消费':'sz159928','酒':'sh512690','家电':'sz159996','旅游':'sz159766','农业':'sz159825','养殖':'sz159865',
    '游戏':'sz159869','传媒':'sz159805','影视':'sz159855',
    '基建':'sh516970','地产':'sh512200','汽车':'sh516110',
}

# 股票持仓映射（每个板块3-5只候选）
CANDIDATES = {
    '半导体': 'sh600171,sz002049,sh600460,sh600584,sz002185',
    '芯片设计': 'sz300672,sz300661,sh603501,sz300782',
    '消费电子': 'sz000725,sz002475,sh603005,sz002241,sh601138',
    '医药': 'sh600276,sz300760,sz300015,sz300347,sh600196',
    '创新药': 'sh600216,sz300122,sz300759',
    'AI/算力': 'sz000977,sz002230,sh603019,sz300624',
    '通信': 'sh600941,sz000063,sz300394,sz300308',
    '云计算': 'sz300454,sz300442,sh600588,sh688111',
    '软件': 'sz300033,sz002410,sz300496,sh603171',
    '证券': 'sh601995,sz300059,sz002736,sh601211',
    '机器人': 'sz002747,sz300124,sz002527,sh601689',
    '军工': 'sh600760,sh600893,sz000768,sz002013',
    '光伏': 'sh601012,sz002459,sz300274,sz300724',
    '新能源车': 'sz002594,sz300750,sz002460,sh600104',
    '化工': 'sh600309,sz002709,sh600352,sz300409',
    '有色': 'sh601899,sh600362,sh600547,sz000630',
    '钢铁': 'sh600019,sh600010,sh600808',
    '游戏': 'sz002624,sh603444,sz300315,sz002555',
    '传媒': 'sz300058,sz002400,sh601858,sz300251',
    '食品饮料': 'sh600519,sh600887,sh603288',
    '基建': 'sh601668,sh601800,sh600039,sh601186',
    '地产': 'sz000002,sh600048,sh600383',
    '银行': 'sh601398,sh601939,sh601288,sh600036',
}


def get_sina(codes):
    """批量获取Sina实时数据 + qt.gtimg.cn市值"""
    all_results = {}
    # 1. Sina获取价格/成交量
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        try:
            r = requests.get(f'http://hq.sinajs.cn/list={",".join(batch)}',
                           headers={'Referer':'http://finance.sina.com.cn'}, timeout=TIMEOUT)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                fields = line.split('"')[1].split(',')
                if len(fields) < 6: continue
                code_raw = line.split('=')[0].split('_')[-1]
                all_results[code_raw] = {
                    'name': fields[0], 'px': float(fields[3]), 'prev': float(fields[2]),
                    'high': float(fields[4]), 'low': float(fields[5]), 'vol': int(float(fields[8])),
                    'cap': 0
                }
        except: continue
    
    # 2. qt.gtimg.cn补市值
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        try:
            r2 = requests.get(f'http://qt.gtimg.cn/q={",".join(batch)}',
                            headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
            r2.encoding = 'gbk'
            for line in r2.text.strip().split('\n'):
                if not line.strip(): continue
                f = line.split('~')
                if len(f) < 45: continue
                code_raw = line.split('=')[0].split('_')[-1]
                cap_val = float(f[44]) if len(f)>44 and f[44] else 0
                if code_raw in all_results:
                    all_results[code_raw]['cap'] = cap_val
        except: continue
    
    return all_results


def get_etf_data():
    """获取ETF数据"""
    codes = ','.join(ETF_MAP.values())
    try:
        r = requests.get(f'http://hq.sinajs.cn/list={codes}',
                        headers={'Referer':'http://finance.sina.com.cn'}, timeout=TIMEOUT)
        r.encoding = 'gbk'
        result = {}
        for line in r.text.strip().split('\n'):
            if not line.strip(): continue
            fields = line.split('"')[1].split(',')
            if len(fields) < 4: continue
            px, prev = float(fields[3]), float(fields[2])
            chg = (px-prev)/prev*100
            for name, code in ETF_MAP.items():
                if code.split('.')[-1] in line.lower():
                    result[name] = round(chg, 1)
                    break
        return result
    except:
        return {}


def score_dna(info, etf_data):
    """
    诸葛亮DNA五维评分（0-100）
    长期票要求: ≥70分 + 市值≤500亿

    维度① 弹性强度(30分) — 大盘跌时个股独立上涨（不涨=僵尸不是牛股）
    维度② 独立性(20分) — 板块跌它涨
    维度③ 资金信号(15分) — 缩量横盘后的放量
    维度④ 筹码结构(10分) — 市值适中/振幅稳
    维度⑤ 催化质量(25分) — 产业级硬逻辑（权重最高！没催化的=僵尸）
    """
    s = 0
    chg = info['chg']
    amp = info['amp']
    sector = info['sector']
    vol = info['vol']

    # ── 维度① 弹性强度 (30分)──
    # 要求：大盘跌的时候个股必须涨>2%，平盘不算强，平盘是僵尸
    kcb = etf_data.get('科创50', 0)
    if kcb < -1 and chg > 2:        # 大盘跌，个股大涨 → 旭光模式
        s += 30
    elif kcb < -1 and chg > 0:       # 大盘跌，个股小涨
        s += 20
    elif kcb < 0 and chg > 1:        # 大盘微跌，个股有涨幅
        s += 10
    elif chg > 0 and chg > kcb + 2:  # 大幅跑赢大盘
        s += 8
    # 大盘跌+个股平盘 → 0分（防御≠牛股特征）
    
    # ── 维度② 独立性 (20分) ──
    sector_chg = etf_data.get(sector, 999)
    if sector_chg != 999:
        if sector_chg < -1 and chg > 1:           # 板块跌，个股涨>1%
            s += 20
        elif sector_chg < -1 and chg > sector_chg + 2:  # 大幅跑赢弱板块
            s += 12
        elif sector_chg > 0 and chg > sector_chg + 2:   # 跑赢强板块
            s += 8
        elif chg > sector_chg:
            s += 3
    
    # ── 维度③ 资金信号 (15分) ──
    if vol > 100000 and -0.5 < chg < 3:
        s += 15  # 放量+温和涨幅=建仓
    elif vol > 50000 and -0.5 < chg < 3:
        s += 8
    elif vol > 30000:
        s += 3
    
    # ── 维度④ 筹码结构 (10分) ──
    if amp < 3:
        s += 10
    elif amp < 5:
        s += 5
    elif amp > 8:
        s -= 5
    
    # ── 维度⑤ 催化质量 (25分) ──
    # 板块必须强！没催化的"稳"=僵尸。板块领涨才叫有催化
    sector_rank = list(etf_data.values())
    sector_rank.sort(reverse=True)
    top_cut = sector_rank[min(5, len(sector_rank)-1)] if sector_rank else 0
    
    if sector_chg != 999 and sector_chg > 2:           # 板块领涨
        s += 25
    elif sector_chg != 999 and sector_chg > 1:          # 板块偏强
        s += 15
    elif sector_chg != 999 and sector_chg > 0:           # 板块微涨
        s += 5
    # 板块跌=催化弱 = 0分
    
    return s


def entry_zone(info):
    """计算合理入场区间（比现价低5-10%）"""
    px = info['px']
    low = round(px * 0.92, 2)
    high = round(px * 0.97, 2)
    return f"{low}-{high}"


def season_stop(info):
    """季线止损（-20%）"""
    return round(info['px'] * 0.80, 2)


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M')
    print(f"🏯 诸葛亮 V2.0 · 长期牛股筛选 | {today} {now}")
    print()

    # 1. 扫ETF
    etf_data = get_etf_data()
    if etf_data:
        sorted_etf = sorted(etf_data.items(), key=lambda x: -x[1])
        print("━" * 50)
        print("  📊 ETF方向")
        print("━" * 50)
        for n, c in sorted_etf[:8]:
            bar = '🚀' if c > 3 else ('🟢' if c > 1 else ('🟡' if c > 0 else '🔴'))
            print(f"  {bar} {n}: {c:+.1f}%")
        print()

    # 2. 扫候选个股
    all_codes = []
    for codes in CANDIDATES.values():
        for c in codes.split(','):
            c = c.strip()
            if c and len(c) > 5 and c not in all_codes:
                all_codes.append(c)

    raw_data = get_sina(all_codes)

    # 3. DNA评分
    candidates = []
    for code, info in raw_data.items():
        if info['px'] == 0: continue
        chg = (info['px'] - info['prev']) / info['prev'] * 100
        amp = (info['high'] - info['low']) / info['prev'] * 100
        amount = info['px'] * info['vol'] / 1e8
        sector = "未知"
        for sn, sc in CANDIDATES.items():
            for c in sc.split(','):
                if c.strip().split('.')[-1] == code:
                    sector = sn
                    break

        cand = {
            'code': code, 'name': info['name'], 'px': round(info['px'], 2),
            'chg': round(chg, 2), 'amp': round(amp, 1),
            'vol': info['vol'] // 100, 'amount': round(amount, 1),
            'sector': sector, 'cap': info.get('cap', 0),
        }
        cand['score'] = score_dna(cand, etf_data)
        candidates.append(cand)

    candidates.sort(key=lambda x: -x['score'])

    # ── 4. 分层输出 ──
    long_pool = [c for c in candidates if c['score'] >= 70 and c.get('cap', 0) <= 500]
    short_pool = [c for c in candidates if 50 <= c['score'] < 70]

    # 长期池
    print("━" * 55)
    print(f"  📦 诸葛亮长期池 (DNA≥70, {len(long_pool)}只)")
    print("━" * 55)
    if long_pool:
        print(f"  {'名称':10s} {'板块':8s} {'现价':>7} {'涨跌':>6} {'评分':>4} {'入场区间':>12} {'季线止损':>8}")
        print("  " + "-" * 62)
        for c in long_pool:
            entry = entry_zone(c)
            stop = season_stop(c)
            bar = '🚀' if c['chg'] > 2 else ('🟢' if c['chg'] > 0 else '🔴')
            print(f"  {bar} {c['name']:10s} {c['sector']:8s} {c['px']:>7.2f} {c['chg']:>+5.1f}% {c['score']:>3d}  {entry:>12}  {stop:>8.2f}")
        print()
        print("  📌 规则: 回调到入场区间才动手，设季线止损，持有2周-3月。不追高。")
    else:
        print("  无 ≥70分的长期候选。")
    print()

    # 短线候选（交汉武帝）
    print(f"  🏹 汉武帝短线候选 (50-69分, {len(short_pool)}只)")
    print("  " + "-" * 45)
    if short_pool:
        for c in short_pool[:10]:
            bar = '🟢' if c['chg'] > 0 else '🔴'
            print(f"  {bar} {c['name']:10s} {c['sector']:8s} {c['px']:.2f} {c['chg']:+.1f}% {c['score']}分 → 交汉武帝尾盘判断")
    else:
        print("  无候选。")

    # 5. 写入日志
    out_dir = os.path.expanduser("~/memory/诸葛亮长期池")
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, f"{today}.md")
    
    # Also save to daily scan log
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          'memory/zhugeliang_midstock/daily_scan_log')
    os.makedirs(log_dir, exist_ok=True)

    with open(log_file, 'w') as f:
        f.write(f"# 诸葛亮 V2.0 长期牛股 | {today}\n\n")
        f.write(f"## ETF方向\n\n")
        if etf_data:
            for n, c in sorted_etf[:8]:
                f.write(f"- {n}: {c:+.1f}%\n")
        
        f.write(f"\n## 长期池 (DNA≥70, {len(long_pool)}只)\n\n")
        if long_pool:
            f.write("| 代码 | 名称 | 板块 | 现价 | 涨跌 | DNA | 入场区间 | 季线止损 |\n")
            f.write("|:---:|:----|:----|:---:|:---:|:---:|:--------|:------:|\n")
            for c in long_pool:
                entry = entry_zone(c)
                stop = season_stop(c)
                f.write(f"| {c['code']} | {c['name']} | {c['sector']} | {c['px']} | {c['chg']:+.1f}% | {c['score']} | {entry} | {stop} |\n")
        else:
            f.write("无。\n")
        
        f.write(f"\n## 汉武帝短线候选 (50-69分)\n\n")
        if short_pool:
            for c in short_pool[:10]:
                f.write(f"- {c['name']} {c['sector']} {c['px']} {c['chg']:+.1f}% {c['score']}分\n")
        else:
            f.write("无。\n")
    
    print(f"\n  日志: {log_file}")


if __name__ == '__main__':
    main()
