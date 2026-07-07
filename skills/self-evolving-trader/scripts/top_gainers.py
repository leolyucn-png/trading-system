#!/usr/bin/env python3
"""
汉武帝 · 同花顺涨停板/龙虎榜扫描 v1.0
通过web_fetch同花顺获取实时涨幅榜，替代被阻断的akshare/东财API
"""
import subprocess, re, sys

def fetch_top_gainers(max_chars=5000):
    """从同花顺获取涨幅榜"""
    cmd = [
        'python3', '-c', f'''
import sys, json
sys.path.insert(0, "/Users/lyu/.openclaw/workspace")
exec(open("/dev/stdin").read())
''' 
    ]
    # Use curl to mimic web_fetch
    result = subprocess.run(
        ['curl', '-s', '--noproxy', '*',
         'https://q.10jqka.com.cn/',
         '-H', 'User-Agent: Mozilla/5.0'],
        capture_output=True, timeout=10
    )
    html = result.stdout.decode('gb2312', errors='replace')
    
    # Parse the stock table
    stocks = []
    # Pattern: code, name, price, chg%, chg_amount, speed%, turnover%, volume_ratio
    pattern = re.compile(
        r'\[(\d{6})\]\([^)]+\)\s+\[([^\]]+)\]\s+([\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)\s+([\d.]+)\s+([\d.]+)',
        re.MULTILINE
    )
    
    for m in pattern.finditer(html):
        try:
            code = m.group(1)
            name = m.group(2)
            price = float(m.group(3))
            chg_pct = float(m.group(4))
            stocks.append({'code': code, 'name': name, 'price': price, 'chg_pct': chg_pct})
        except:
            continue
    
    return stocks[:25]

def main():
    print("📡 同花顺涨幅榜")
    stocks = fetch_top_gainers()
    
    # Classify by sector
    sectors = {}
    for s in stocks:
        code = s['code']
        # Rough sector classification
        if code.startswith('920'): sector = '京股'
        elif code.startswith('300'): sector = '创业板'
        elif code.startswith('688'): sector = '科创板'
        elif code.startswith('60'): sector = '沪主板'
        elif code.startswith('00'): sector = '深主板'
        else: sector = '其他'
        
        if sector not in sectors: sectors[sector] = []
        sectors[sector].append(s)
    
    for sector, items in sorted(sectors.items()):
        print(f"\n  [{sector}]")
        for s in items:
            print(f"    {s['code']} {s['name']:<10} {s['price']:>8.2f} {s['chg_pct']:+.2f}%")
    
    print(f"\n⚠️ 反共识提示：以上涨停票分布在哪些板块？有没有不在我关注范围内的？")

if __name__ == '__main__':
    main()
