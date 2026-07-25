#!/usr/bin/env python3
"""
刘备 V3.6 · 最早消息追踪 + 国际/国内新闻
抓最早爆出的消息源，不是二手新闻
"""
import requests, json, os
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE, 'memory/liubei_opinion_v2/news_raw')
TRACK_FILE = os.path.join(OUT_DIR, 'first_seen.json')
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
HK = timezone(timedelta(hours=8))
NOW = datetime.now(HK)

def fetch_sina_earliest():
    """新浪 \u6700\u65e9\u65b0\u95fb\uff08\u5b9e\u65f6\u5237\u65b0\uff09"""
    results = []
    try:
        r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20&page=1', timeout=8)
        if r.ok:
            for item in r.json().get('result',{}).get('data',[]):
                t = item.get('ctime','')
                if t:
                    d = datetime.fromtimestamp(int(t), tz=HK)
                    results.append((d, item.get('title',''), '新浪'))
    except:
        pass
    results.sort(key=lambda x: x[0])
    return results[:10]

def fetch_google_earliest():
    """Google News - 今日最早的国际新闻"""
    results = []
    for query, label in [('China+stock+market+semiconductor', 'Reuters/Bloomberg'), ('A%E8%82%A1', 'CN')]:
        try:
            url = f'https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en'
            r = requests.get(url, timeout=8, headers=HEADERS)
            items = ET.fromstring(r.text).find('channel').findall('item')
            for item in items:
                title = item.find('title')
                pub = item.find('pubDate')
                src = item.find('source')
                if title is not None and pub is not None:
                    try:
                        d = datetime.strptime(pub.text[:25].replace('GMT','').strip(), '%a, %d %b %Y %H:%M:%S')
                        d = d.replace(tzinfo=timezone.utc).astimezone(HK)
                        if d.date() == NOW.date():  # 只取今天
                            results.append((d, title.text[:80], src.text if src is not None else '?'))
                    except:
                        pass
        except:
            pass
    results.sort(key=lambda x: x[0])
    return results[:5]

def fetch_yahoo_earliest():
    """Yahoo Finance - 隔夜美股最早消息"""
    results = []
    try:
        r = requests.get('https://finance.yahoo.com/rss/', timeout=8, headers=HEADERS)
        for item in ET.fromstring(r.text).find('channel').findall('item')[:10]:
            title = item.find('title')
            pub = item.find('pubDate')
            if title is not None and pub is not None:
                try:
                    d = datetime.strptime(pub.text[:25].strip(), '%a, %d %b %Y %H:%M:%S %z')
                    d = d.astimezone(HK)
                    if d.date() == NOW.date():
                        results.append((d, title.text[:80], 'Yahoo'))
                except:
                    pass
    except:
        pass
    return results[:3]

def main():
    print("="*65)
    print(f"  🐉 刘备 V3.6 · 最早消息追踪 | {NOW.strftime('%Y-%m-%d %H:%M')}")
    print("="*65)

    # 1. 国内最早
    print("\n📰 国内最早（新浪实时）")
    for d, title, src in fetch_sina_earliest():
        ts = d.strftime('%H:%M')
        marker = "🆕" if (NOW - d).total_seconds() < 3600 else "  "
        print(f"  {marker} [{ts}] {title[:65]}")

    # 2. 国际最早（今日）
    print("\n🌍 国际今天最早（Reuters/Bloomberg/Google News）")
    intl = fetch_google_earliest() + fetch_yahoo_earliest()
    intl.sort(key=lambda x: x[0])
    for d, title, src in intl[:5]:
        ts = d.strftime('%H:%M')
        print(f"  [{ts}] [{src}] {title[:65]}")

    # 3. 概念热度
    try:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f3,f14'
        r = requests.get(url, timeout=5)
        if r.ok:
            hot = [it['f14'] for it in r.json().get('data',{}).get('diff',[]) if it.get('f14')]
            if hot:
                print(f"\n🔥 概念热度: {' '.join(hot)}")
    except:
        pass

    print(f"\n🔴 中信空单: ⏳ 中金所16:00后更新")

    today = NOW.strftime('%Y-%m-%d')
    out_file = os.path.join(OUT_DIR, f"{today}_{NOW.strftime('%H%M')}.json")
    with open(out_file, 'w') as f:
        json.dump({"time": NOW.isoformat()}, f, ensure_ascii=False)
    print(f"\n✅ {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
