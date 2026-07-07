#!/tmp/stock_venv/bin/python3.14
"""
汉武帝计划 - mootdx实时行情补充扫描
"""
import asyncio
import sys

# Apply time_frame patch
import tdxpy.hq
tdxpy.hq.time_frame = lambda: True

from mootdx.quotes import Quotes

async def main():
    print("=" * 60)
    print("汉武帝 | 实时行情扫描 09:15")
    print("=" * 60)

    client = Quotes.factory(market='std')
    
    # 1. 完美世界 002624
    print("\n[1] 完美世界 002624 (集合竞价)")
    try:
        df = client.quotes(symbol="002624")
        if df is not None and len(df) > 0:
            r = df.iloc[0]
            price = float(r.get('price', 0))
            last_close = float(r.get('last_close', 0))
            open_ = float(r.get('open', 0))
            high = float(r.get('high', 0))
            low = float(r.get('low', 0))
            vol = int(r.get('volume', 0))
            amount = float(r.get('amount', 0))
            
            pct = (price - last_close) / last_close * 100 if last_close > 0 else 0
            emoji = chr(0x1F534) if pct > 0 else (chr(0x1F7E2) if pct < 0 else chr(0x26AA))
            print(f"  {emoji} 竞价价: {price:.2f}  涨跌: {pct:+.2f}%")
            print(f"  昨收: {last_close:.2f}  今开: {open_:.2f}")
            print(f"  高/低: {high:.2f}/{low:.2f}  量:{vol}  额:{amount:.0f}")
            
            bid1 = float(r.get('bid1', 0))
            bv1 = int(r.get('bid_vol1', 0))
            ask1 = float(r.get('ask1', 0))
            av1 = int(r.get('ask_vol1', 0))
            print(f"  买一: {bid1:.2f}({bv1}手)  卖一: {ask1:.2f}({av1}手)")
        else:
            print("  - 无数据 (集合竞价未生成)")
    except Exception as e:
        print(f"  - {e}")

    # 2. 京东方 000725
    print("\n[2] 京东方A 000725")
    try:
        df = client.quotes(symbol="000725")
        if df is not None and len(df) > 0:
            r = df.iloc[0]
            price = float(r.get('price', 0))
            last_close = float(r.get('last_close', 0))
            pct = (price - last_close) / last_close * 100 if last_close > 0 else 0
            emoji = chr(0x1F534) if pct > 0 else (chr(0x1F7E2) if pct < 0 else chr(0x26AA))
            print(f"  {emoji} 竞价价: {price:.2f}  涨跌: {pct:+.2f}%  量:{int(r.get('volume',0))}")
        else:
            print("  - 无数据")
    except Exception as e:
        print(f"  - {e}")

    # 3. 候选扫描 (主板/深市，非300)
    print("\n[3] 候选扫描")
    candidates = [
        ("002555", "三七互娱"), ("603444", "吉比特"),
        ("002230", "科大讯飞"), ("600570", "恒生电子"),
        ("600839", "四川长虹"), ("000100", "TCL科技"),
    ]
    for code, name in candidates:
        try:
            df = client.quotes(symbol=code)
            if df is not None and len(df) > 0:
                r = df.iloc[0]
                price = float(r.get('price', 0))
                lc = float(r.get('last_close', 0))
                pct = (price - lc) / lc * 100 if lc > 0 else 0
                emoji = chr(0x1F534) if pct > 0 else (chr(0x1F7E2) if pct < 0 else chr(0x26AA))
                print(f"  {emoji} {name}({code}): {price:.2f}  {pct:+.2f}%")
        except:
            pass

    # 4. 上证指数
    print("\n[4] 上证指数")
    try:
        df = client.quotes(symbol="000001")
        if df is not None and len(df) > 0:
            r = df.iloc[0]
            price = float(r.get('price', 0))
            lc = float(r.get('last_close', 0))
            pct = (price - lc) / lc * 100 if lc > 0 else 0
            emoji = chr(0x1F534) if pct > 0 else (chr(0x1F7E2) if pct < 0 else chr(0x26AA))
            print(f"  {emoji} {price:.2f}  ({pct:+.2f}%)")
    except Exception as e:
        print(f"  - {e}")

    print("\n" + "=" * 60)
    print("扫描结束 | 09:25确认开盘价后推送策略")
    print("=" * 60)

asyncio.run(main())
