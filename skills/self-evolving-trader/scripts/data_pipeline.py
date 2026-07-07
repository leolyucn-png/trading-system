#!/usr/bin/env python3
"""
汉武帝 · 预判数据管道 v1.0
统一数据接口，GB2312编码处理
"""

import subprocess, re, json
from datetime import datetime

def fetch_url(url, headers=None, enc='gb2312'):
    """通用HTTP fetch，处理编码"""
    cmd = ['curl', '-s', '--noproxy', '*', url]
    if headers:
        for k, v in headers.items():
            cmd.extend(['-H', f'{k}: {v}'])
    r = subprocess.run(cmd, capture_output=True, timeout=10)
    return r.stdout.decode(enc, errors='replace')

def parse_tencent(raw):
    """腾讯API解析"""
    stocks = {}
    for m in re.finditer(r'v_\w+="(.*?)"', raw):
        p = m.group(1).split('~')
        if len(p) < 10: continue
        try:
            code = p[2]; name = p[1]
            price = float(p[3]); prev = float(p[4])
            outer = int(p[7]) if p[7].lstrip('-').isdigit() else 0
            inner = int(p[8]) if p[8].lstrip('-').isdigit() else 0
            high  = float(p[33]) if len(p)>33 else 0
            low   = float(p[34]) if len(p)>34 else 0
            chg   = round((price-prev)/prev*100, 2)
            stocks[code] = {'name':name,'price':price,'prev':prev,'chg':chg,
                           'high':high,'low':low,'outer':outer,'inner':inner,
                           'net':outer-inner}
        except: continue
    return stocks

def parse_sina(raw):
    """Sina API解析"""
    idx = {}
    for m in re.finditer(r'hq_str_(\w+)="(.*?)"', raw):
        p = m.group(2).split(',')
        if len(p) < 6: continue
        try:
            name = p[0]; price = float(p[3]); prev = float(p[2])
            idx[m.group(1)] = {'name':name,'price':price,'prev':prev,
                              'high':float(p[4]),'low':float(p[5]),
                              'chg':round((price-prev)/prev*100,2)}
        except: continue
    return idx

def run(holdings="sh600353,sh603005,sz002624,sz002156,sz000938"):
    print(f"📡 数据管道 @{datetime.now():%H:%M:%S}")
    holdings_tencent = fetch_url(f"https://qt.gtimg.cn/q={holdings}")
    stocks = parse_tencent(holdings_tencent)
    
    # 指数
    idx_raw = fetch_url(
        "https://hq.sinajs.cn/list=sh000001,sz399001,sz399006,sh000688",
        {"Referer":"https://finance.sina.com.cn"})
    indices = parse_sina(idx_raw)
    
    # 板块
    sectors_code = ",".join([
        "sz399610","sz399678","sz399986","sz399989","sz399993",
        "sz399995","sz399997","sh000827","sh000808",
        "sh000933","sh000944","sz399438","sz399440",
        "sz399611","sz399612","sz399613","sz399614","sz399615"
    ])
    sectors_raw = fetch_url(f"https://qt.gtimg.cn/q={sectors_code}")
    sectors = parse_tencent(sectors_raw)
    
    # 输出
    print("\n📊 大盘:")
    for k,v in indices.items():
        a = "🔴" if v['chg']<0 else "🟢"
        print(f"  {a} {v['name']}: {v['price']:.1f} ({v['chg']:+.2f}%) L:{v['low']:.1f}")

    print("\n📈 持仓:")
    for k,v in stocks.items():
        nb = f"+{v['net']}" if v['net']>=0 else str(v['net'])
        print(f"  {v['name']:<8} {v['price']:.2f} ({v['chg']:+.2f}%) 外>{nb}")

    print("\n🏭 板块(前5+后3):")
    ranked = sorted(sectors.items(), key=lambda x: x[1]['chg'], reverse=True)
    for k,v in ranked[:5]:
        print(f"  🔥 {v['name']:<16} {v['chg']:+.2f}%")
    for k,v in ranked[-3:]:
        print(f"  📉 {v['name']:<16} {v['chg']:+.2f}%")

if __name__ == '__main__':
    run()
