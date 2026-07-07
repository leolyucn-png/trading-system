#!/usr/bin/env python3
import subprocess, re
from datetime import datetime

def fetch_futures():
    url = "https://vip.stock.finance.sina.com.cn/q/view/vCffex_Positions_jcgc.php?symbol=IC2606"
    r = subprocess.run(['curl', '-s', '--noproxy', '*', url], capture_output=True, timeout=10)
    html = r.stdout.decode('gb2312', errors='replace')
    rows = re.findall(r'(\d{4}-\d{2}-\d{2})[^<]*?</td>[^<]*?<td[^>]*>\d+[^<]*?</td>[^<]*?<td[^>]*>[-?\d]+[^<]*?</td>[^<]*?<td[^>]*>(\d+)[^<]*?</td>[^<]*?<td[^>]*>[-?\d]+[^<]*?</td>[^<]*?<td[^>]*>(\d+)', html)
    return [{'date':r[0], 'long':int(r[1]), 'short':int(r[2])} for r in rows[:14]]

def scan_holdings():
    codes = "sh600353,sh603005,sz002624,sz002156,sz000938"
    raw = subprocess.run(['curl','-s','--noproxy','*',f'https://qt.gtimg.cn/q={codes}'], capture_output=True, timeout=10).stdout.decode('gb2312',errors='replace')
    stocks = {}
    for m in re.finditer(r'v_\w+="(.*?)"', raw):
        p = m.group(1).split('~')
        if len(p)<10: continue
        try:
            o=int(p[7]) if p[7].lstrip('-').isdigit() else 0
            n=int(p[8]) if p[8].lstrip('-').isdigit() else 0
            stocks[p[2]]={'name':p[1],'price':float(p[3]),'prev':float(p[4]),'outer':o,'inner':n,'net':o-n,'chg':round((float(p[3])-float(p[4]))/float(p[4])*100,2)}
        except: continue
    return stocks

def main():
    print(f"🚨 {datetime.now():%H:%M:%S}")
    
    f = fetch_futures()
    if f:
        latest = f[0]
        week = next((x for x in f if '05-27' in x['date']), None)
        d = latest['short']-week['short'] if week else 0
        print(f"📊 中信IC2606: {latest['date']} 净空{latest['short']-latest['long']}手 (空{latest['short']}/多{latest['long']})")
        if week: print(f"   较5/27: 空{d:+} 净空{(latest['short']-latest['long'])-(week['short']-week['long']):+}")
    
    s = scan_holdings()
    total = sum(x['net'] for x in s.values())
    for c,x in s.items():
        sign = "✅" if x['net']>0 else "❌"
        print(f"  {sign} {x['name']:<8} {x['price']:.2f}({x['chg']:+.1f}%) 净{x['net']:+,}")
    print(f"  总: {total:+,}")
    
    allred = all(x['net']<0 for x in s.values())
    if allred: print("🔴 五票全在卖")
    if total<-50000: print("🔴 只减不加")
    print("🔍 缺口: 银行白酒涨/宗申涨停/中化涨停")

if __name__=='__main__': main()
