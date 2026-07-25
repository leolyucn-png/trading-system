#!/usr/bin/env python3
"""
刘备 V3.5 · 舆情验证 + 国际新闻(带时间戳) + 中信空单
"""
import requests, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE, 'memory/liubei_opinion_v2/news_raw')
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def fetch_domestic():
    results = []
    try:
        r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=10&page=1', timeout=8)
        if r.ok:
            data = r.json()
            for item in data.get('result',{}).get('data',[])[:5]:
                t = item.get('ctime','')
                d = datetime.fromtimestamp(int(t)) if t else datetime.now()
                results.append((d.strftime('%m/%d %H:%M'), item.get('title','')))
    except:
        results.append(('','接口超时'))
    return results

def fetch_concepts():
    try:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f3,f14'
        r = requests.get(url, timeout=5)
        if r.ok:
            return [it['f14'] for it in r.json().get('data',{}).get('diff',[]) if it.get('f14')]
    except:
        pass
    return []

def fetch_international():
    results = []
    import xml.etree.ElementTree as ET

    # 1. Google News - China stocks (RSS format)
    try:
        r = requests.get('https://news.google.com/rss/search?q=China+stock+market&hl=en-US&gl=US&ceid=US:en',
                        timeout=8, headers=HEADERS)
        if r.ok:
            for item in ET.fromstring(r.text).find('channel').findall('item')[:3]:
                title = item.find('title')
                pub = item.find('pubDate')
                src = item.find('source')
                if title is not None:
                    t = pub.text if pub is not None else '?'
                    s = src.text if src is not None else '?'
                    results.append((t, s, title.text[:80]))
    except:
        results.append(('','','⬜ Google News超时'))

    # 2. Yahoo Finance
    try:
        r = requests.get('https://finance.yahoo.com/rss/', timeout=8, headers=HEADERS)
        if r.ok:
            for item in ET.fromstring(r.text).find('channel').findall('item')[:2]:
                title = item.find('title')
                pub = item.find('pubDate')
                if title is not None and ('stock' in title.text.lower() or 'market' in title.text.lower() or 'semi' in title.text.lower()):
                    t = pub.text if pub is not None else '?'
                    results.append((t, 'Yahoo', title.text[:80]))
    except:
        results.append(('','','⬜ Yahoo超时'))

    return results

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print("="*65)
    print(f"  🐉 刘备 V3.5 · 国内+国际舆情 | {now}")
    print("="*65)

    print("\n📰 国内热点")
    for t, n in fetch_domestic():
        print(f"  [{t}] {n[:60]}")

    concepts = fetch_concepts()
    if concepts:
        print(f"\n🔥 概念热度: {' '.join(concepts)}")

    print("\n🌍 国际新闻")
    for item in fetch_international():
        if len(item) == 3:
            t, src, title = item
            print(f"  [{t}] [{src}] {title[:70]}")
        else:
            print(f"  {item[0]}")

    print("\n🔴 中信空单")
    print("  ⏳ 中金所排名16:00后更新")

    today = datetime.now().strftime('%Y-%m-%d')
    out_file = os.path.join(OUT_DIR, f"{today}_{datetime.now().strftime('%H%M')}.json")
    with open(out_file, 'w') as f:
        json.dump({"time": now}, f, ensure_ascii=False)
    print(f"\n✅ {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
