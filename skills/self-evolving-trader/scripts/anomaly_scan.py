#!/usr/bin/env python3
"""
异动扫描器 v1.0 — 扫全行业watchlist找异常信号
用法: python3 anomaly_scan.py
输出: 量比>3或净买异常的标的
"""
import subprocess, re, sys

WATCHLIST = {
    "军工": "002625,600879,600118,600072,601606,600685,000547,600391,600893,002013,600760,600435,002829,603698,600501,002544",
    "化工": "600500,002256,600229,603938,002274,002092,600309,601678,000830",
    "AI算力": "603019,000977,000938,002230,000063,603236",
    "封测": "600584,002185,002156,603005,600171,603501,002409",
    "医药": "600276,000538,600085,002007,600196,603259,000963",
    "消费白酒": "000858,600519,002304,000568,600809,600702,603369,600559",
    "低空经济": "001696,600843,000801",
    "新能源": "601012,002459,600438",
    "金融": "601398,601939,600036,601166,601318,601628,600030",
    "央企重组": "600500,600579,601698,601606,600391",
    "软件数字化": "603039,600536,002410,600845,300624",
    "通信": "600118,002544,000063,600487,601698",
    "传媒游戏": "002354,600088,002602,002555"
}

def fetch_codes(codes_str):
    url = f"https://qt.gtimg.cn/q={codes_str}"
    r = subprocess.run(['curl','-s','--noproxy','*',url], capture_output=True, timeout=10)
    return r.stdout.decode('gb2312','replace')

def scan():
    print("🔍 全行业异动扫描")
    
    # Deduplicate codes
    all_codes = set()
    for codes in WATCHLIST.values():
        for c in codes.split(','):
            if c.startswith('60') or c.startswith('00'):  # 主板only
                all_codes.add(c)
    
    # Fetch in batches of 30
    code_list = list(all_codes)
    all_stocks = {}
    
    for i in range(0, len(code_list), 30):
        batch = code_list[i:i+30]
        codes = ','.join(f'sh{c}' if c.startswith('6') else f'sz{c}' for c in batch)
        raw = fetch_codes(codes)
        for m in re.finditer(r'v_\w+="(.*?)"', raw):
            p = m.group(1).split('~')
            if len(p) < 15: continue
            try:
                code = p[2]
                name = p[1]
                price = float(p[3])
                prev = float(p[4])
                chg = (price-prev)/prev*100
                outer = int(p[7]) if p[7].lstrip('-').isdigit() else 0
                inner = int(p[8]) if p[8].lstrip('-').isdigit() else 0
                net = outer-inner
                vr = float(p[46]) if len(p)>46 and p[46].replace('.','').replace('-','').replace('.','').isdigit() else 0
                high = float(p[33]) if len(p)>33 else 0
                low = float(p[34]) if len(p)>34 else 0
                turnover = float(p[38]) if len(p)>38 and p[38].replace('.','').isdigit() else 0
                all_stocks[code] = {'name':name,'price':price,'chg':chg,'net':net,'vr':vr,'high':high,'low':low,'prev':prev,'turnover':turnover}
            except: pass
    
    # Find sector for each stock
    code_sector = {}
    for sector, codes in WATCHLIST.items():
        for c in codes.split(','):
            if c in all_stocks:
                code_sector[c] = sector
    
    # Signal 1: 量比>5
    print("\n🔥 量比>5异动:")
    for code, s in sorted(all_stocks.items(), key=lambda x: x[1]['vr'], reverse=True):
        if s['vr'] > 5 and s['chg'] < 8 and code not in ('001696','600500'):  # exclude涨停
            sec = code_sector.get(code, '?')
            sign = '✅' if s['net']>0 else '➖'
            print(f"  {sign} {code} {s['name']:<10} {s['price']:.1f} {s['chg']:+.1f}% 量比{s['vr']:.1f} 净{s['net']:+,} [{sec}]")
    
    # Signal 2: 涨幅2-8% + 净买>0
    print("\n📈 主力建仓信号(涨2-8%+净买>0):")
    for code, s in sorted(all_stocks.items(), key=lambda x: x[1]['chg'], reverse=True):
        if 2 < s['chg'] < 8 and s['net'] > 10000:
            sec = code_sector.get(code, '?')
            print(f"  ✅ {code} {s['name']:<10} {s['price']:.1f} {s['chg']:+.1f}% 净{s['net']:+,} [{sec}]")
    
    # Signal 3: 超跌弹候选 (跌>3% + 量比>2)
    print("\n📉 超跌候选(跌>3%+量比>2):")
    for code, s in sorted(all_stocks.items(), key=lambda x: x[1]['chg']):
        if s['chg'] < -3 and s['vr'] > 2:
            sec = code_sector.get(code, '?')
            print(f"  🔴 {code} {s['name']:<10} {s['price']:.1f} {s['chg']:+.1f}% 量比{s['vr']:.1f} [{sec}]")
    
    # Signal 4: 游资试盘(量比>4 + 涨幅<2% + 冲高>5%)
    print("\n🎯 游资试盘(量比>4+涨<2%+冲高>5%):")
    for code, s in sorted(all_stocks.items(), key=lambda x: x[1]['vr'], reverse=True):
        if s['vr'] > 4 and abs(s['chg']) < 2.5:
            high_pct = (s['high']-s['prev'])/s['prev']*100
            if high_pct > 4:
                sec = code_sector.get(code, '?')
                print(f"  🎯 {code} {s['name']:<10} {s['price']:.1f} {s['chg']:+.1f}% 高{s['high']:.1f}(+{high_pct:.1f}%) 量比{s['vr']:.1f} [{sec}]")

if __name__ == '__main__':
    scan()
