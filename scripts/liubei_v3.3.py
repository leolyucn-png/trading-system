#!/usr/bin/env python3
"""
刘备 V3.3 · 舆情验证 + 国际新闻 + 主力持仓检测
数据源: 国内新闻 + Reuters/BBC/WSJ + 期货持仓
"""
import requests, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE, 'memory/liubei_opinion_v2/news_raw')
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_domestic():
    """国内新闻（Sina滚动）"""
    results = []
    try:
        r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=15&page=1', timeout=8)
        if r.ok:
            data = r.json()
            for item in data.get('result',{}).get('data',[])[:5]:
                results.append(item.get('title',''))
    except:
        results.append("(接口超时)")
    return results

def fetch_concepts():
    """热门概念板块"""
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
    """国际新闻（Reuters/BBC/WSJ影响A股的关键信息）"""
    results = []
    
    # 1. Reuters - US markets/China news
    try:
        r = requests.get('https://www.reuters.com/tag/china-stocks/', timeout=8, 
                        headers={'User-Agent': 'Mozilla/5.0'})
        if r.ok:
            results.append("✅ Reuters 中国股市新闻: 可达")
        else:
            results.append("⬜ Reuters: 不可达")
    except:
        results.append("⬜ Reuters: 超时")
    
    # 2. BBC - China business
    try:
        r = requests.get('https://www.bbc.com/news/business', timeout=8,
                        headers={'User-Agent': 'Mozilla/5.0'})
        if r.ok:
            results.append("✅ BBC 商业新闻: 可达")
        else:
            results.append("⬜ BBC: 不可达")
    except:
        results.append("⬜ BBC: 超时")
    
    # 3. WSJ / MarketWatch for overnight US moves
    try:
        # Use a proxy API for WSJ headlines
        r = requests.get('https://feeds.content.dowjones.io/public/rss/mw_top_stories', timeout=8,
                        headers={'User-Agent': 'Mozilla/5.0'})
        if r.ok:
            results.append("✅ MarketWatch: 可达")
        else:
            results.append("⬜ MarketWatch: 不可达")
    except:
        results.append("⬜ MarketWatch: 超时")
    
    return results

def check_futures():
    """检测期货持仓（中信空单）"""
    try:
        # 中金所数据要通过东方财富接口获取
        url = 'https://datacenter.eastmoney.com/stock/data/api?type=1&sty=all&code=IF00&p=1&ps=20&sr=1&st=date&token='
        # 这个接口可能不通，先返回占位
        return ["⏳ 中金所排名16:00后更新", "⏳ 数据源建设中(akshare futures_hold_pos_sina)"]
    except:
        return ["⏳ 数据源建设中"]

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print("="*60)
    print(f"  🐉 刘备 V3.3 · 国内+国际舆情 | {now}")
    print("="*60)
    
    # 1. 国内新闻
    print("\n📰 国内热点")
    for n in fetch_domestic():
        print(f"  • {n}")
    
    # 2. 热门概念
    concepts = fetch_concepts()
    if concepts:
        print(f"\n🔥 概念热度: {' '.join(concepts)}")
    
    # 3. 国际新闻
    print("\n🌍 国际媒体（影响A股）")
    for i in fetch_international():
        print(f"  {i}")
    
    # 4. 中信空单
    print("\n🔴 中信期货空单检测")
    for f in check_futures():
        print(f"  {f}")
    
    # Save
    today = datetime.now().strftime('%Y-%m-%d')
    out_file = os.path.join(OUT_DIR, f"{today}_{datetime.now().strftime('%H%M')}.json")
    with open(out_file, 'w') as f:
        json.dump({"time": now}, f, ensure_ascii=False)
    print(f"\n✅ 已保存: {os.path.basename(out_file)}")

if __name__ == '__main__':
    main()
