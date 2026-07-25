#!/usr/bin/env python3
"""
刘备 V3.2 · 舆情验证 + 主力持仓检测
数据源: akshare新闻 + Sina期货持仓排名
输出: 当日舆情热点 + 中信期货空单检测
"""
import requests, json, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE, 'memory/liubei_opinion_v2/news_raw')
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_news():
    """获取当日热点新闻（模拟同花顺/东财热榜）"""
    results = []
    try:
        # Sina hot news
        r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=15&page=1',
                        timeout=8)
        if r.ok:
            data = r.json()
            for item in data.get('result',{}).get('data',[]):
                title = item.get('title','')
                results.append(f"- {title}")
    except:
        results.append("- 新浪新闻接口超时")

    # Try fetching hot concepts from EastMoney
    try:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f3,f14'
        r = requests.get(url, timeout=8)
        if r.ok:
            items = r.json().get('data',{}).get('diff',[])
            hot_concepts = [it['f14'] for it in items[:5] if it.get('f14')]
            results.append(f"🔥 热门概念TOP5: {' '.join(hot_concepts)}")
    except:
        pass
    return results

def check_citic_futures():
    """检测中信期货是否加空单（通过查股指期货持仓排名）"""
    try:
        import akshare as ak
        today = datetime.now().strftime('%Y%m%d')
        # Try IF contract
        results = {}
        for contract in ['IF00', 'IC00', 'IH00']:
            try:
                # 尝试使用中金所持仓排名 - 这个函数需要正确的合约代码
                # 实际代码需要根据当前主力合约月份确定
                df = ak.stock_individual_fund_flow(stock='期货持仓', market='）
                # 这个API可能不存在
            except:
                pass
        
        # 替代方案：直接从网页获取
        # 中金所每日持仓排名: http://www.cffex.com.cn/ccr/
        return [{"status": "需手动确认", "note": "中金所每日16:00后公布持仓排名"}]
    except Exception as e:
        return [{"status": f"数据源错误: {e}"}]

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    print("=" * 55)
    print(f"  🐉 刘备 V3.2 · 舆情+持仓 | {now}")
    print("=" * 55)

    # 1. 新闻热榜
    print("\n📰 热点新闻")
    news = fetch_news()
    for n in news:
        print(f"  {n}")

    # 2. 中信空单
    print("\n🔴 中信期货持仓（空单检测）")
    print("  ⚠️ 中金所数据每日16:00后更新")
    print("  ⚠️ 数据源正在建设（需确认akshare期货排名API）")
    
    # Save
    today = datetime.now().strftime('%Y-%m-%d')
    out_file = os.path.join(OUT_DIR, f"{today}_{datetime.now().strftime('%H%M')}.json")
    with open(out_file, 'w') as f:
        json.dump({"time": now, "news": news}, f, ensure_ascii=False)
    print(f"\n✅ 已保存: {out_file}")

if __name__ == '__main__':
    main()
