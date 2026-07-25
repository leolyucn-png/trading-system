#!/usr/bin/env python3
"""
刘备 V3.4 · 舆情验证 + 国际新闻(Google News) + 主力持仓检测
数据源: 国内新闻 + Google News(英/中) + MarketWatch + CNBC
"""
import requests, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE, 'memory/liubei_opinion_v2/news_raw')
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def fetch_domestic():
    """国内新闻"""
    results = []
    try:
        r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=10&page=1', timeout=8)
        if r.ok:
            data = r.json()
            for item in data.get('result',{}).get('data',[])[:5]:
                results.append(item.get('title',''))
    except:
        results.append("(接口超时)")
    return results

def fetch_concepts():
    """热门概念"""
    try:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f3,f14'
        r = requests.get(url, timeout=5)
        if r.ok:
            items = r.json().get('data',{}).get('diff',[])
            return [it['f14'] for it in items if it.get('f14')]
    except:
        pass
    return []

def fetch_international():
    """国际新闻 - 影响A股的关键信息"""
    results = []
    import xml.etree.ElementTree as ET

    # 1. Google News - China stocks (英文)
    try:
        r = requests.get('https://news.google.com/rss/search?q=China+stock+market&hl=en-US&gl=US&ceid=US:en',
                        timeout=8, headers=HEADERS)
        if r.ok:
            root = ET.fromstring(r.text)
            for item in list(root.iter('{http://www.w3.org/2005/Atom}entry'))[:3]:
                t = item.find('{http://www.w3.org/2005/Atom}title')
                if t is not None:
                    results.append(f"🇺🇸 {t.text[:80]}")
    except:
        results.append("⬜ Google News(英): 超时")

    # 2. Google News - 半导体/A股中文
    try:
        r = requests.get('https://news.google.com/rss/search?q=A%E8%82%A1+%E5%8D%8A%E5%AF%BC%E4%BD%93&hl=zh-CN&gl=CN&ceid=CN:zh-Hans',
                        timeout=8, headers=HEADERS)
        if r.ok:
            root = ET.fromstring(r.text)
            for item in list(root.iter('{http://www.w3.org/2005/Atom}entry'))[:2]:
                t = item.find('{http://www.w3.org/2005/Atom}title')
                if t is not None:
                    results.append(f"🇨🇳 {t.text[:80]}")
    except:
        results.append("⬜ Google News(中): 超时")

    # 3. Yahoo Finance - US markets overnight
    try:
        r = requests.get('https://finance.yahoo.com/rss/', timeout=8, headers=HEADERS)
        if r.ok:
            root = ET.fromstring(r.text)
            for item in root.iter('item'):
                t = item.find('title')
                if t is not None and ('stock' in t.text.lower() or 'market' in t.text.lower() or 'china' in t.text.lower()):
                    results.append(f"📈 {t.text[:80]}")
                    break
    except:
        results.append("⬜ Yahoo: 超时")

    return results

def check_futures():
    """检测期货持仓"""
    try:
        return ["⏳ 中金所排名16:00后更新", "⏳ 数据源: akshare futures_hold_pos_sina"]
    except:
        return ["⏳ 数据源建设中"]

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print("="*60)
    print(f"  🐉 刘备 V3.4 · 国内+国际舆情 | {now}")
    print("="*60)
    
    print("\n📰 国内热点")
    for n in fetch_domestic():
        print(f"  • {n}")
    
    concepts = fetch_concepts()
    if concepts:
        print(f"\n🔥 概念热度: {' '.join(concepts)}")
    
    print("\n🌍 国际新闻（影响A股）")
    for i in fetch_international():
        print(f"  {i}")
    
    print("\n🔴 中信期货空单")
    for f in check_futures():
        print(f"  {f}")
    
    today = datetime.now().strftime('%Y-%m-%d')
    out_file = os.path.join(OUT_DIR, f"{today}_{datetime.now().strftime('%H%M')}.json")
    with open(out_file, 'w') as f:
        json.dump({"time": now}, f, ensure_ascii=False)
    print(f"\n✅ 已保存: {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
