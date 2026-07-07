#!/usr/bin/env python3
"""
刘备 V3.1 · 龙虎榜监控
拉取每日龙虎榜数据，识别游资/机构动向
"""
import json
import os
from datetime import datetime

OUTPUT_DIR = "/Users/lyu/.openclaw/workspace/memory/liubei_opinion_v2/longhubang"

# 知名游资席位（部分示例，可扩展）
FAMOUS_YOUZI = [
    "华鑫证券上海分公司",     # 量化打板
    "中信证券上海溧阳路",     # 老牌游资
    "国泰君安上海江苏路",     # 章盟主
    "财通证券杭州上塘路",     # 上塘路
    "华泰证券深圳益田路",     # 深圳帮
    "中信证券上海分公司",
    "中国银河北京中关村",
    "东方财富拉萨团结路",     # 散户集中营（反向指标）
]

# 机构席位关键词
INSTITUTION_KEYWORDS = ["机构专用", "深股通专用", "沪股通专用"]

def fetch_longhubang(date=None):
    """使用akshare拉取龙虎榜数据"""
    try:
        import akshare as ak
    except ImportError:
        print("❌ akshare未安装，请先 pip install akshare")
        return []
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    try:
        # 拉取龙虎榜个股数据
        df = ak.stock_lhb_detail_em(date=date)
        return df
    except Exception as e:
        print(f"⚠️ 龙虎榜拉取失败: {e}")
        print("  （周日/非交易日属正常情况）")
        return []

def analyze_longhubang(df):
    """分析龙虎榜数据，提取关键信号"""
    if df is None or len(df) == 0:
        return {"error": "无数据"}
    
    signals = {
        "youzi_buy": [],      # 游资净买入>3000万
        "institution_buy": [], # 机构净买入>5000万
        "youzi_sell": [],      # 游资净卖出
        "one_day_tour": [],    # 一日游嫌疑
        "retail_trap": [],     # 散户接盘信号
    }
    
    # 按个股聚合
    stocks = {}
    for _, row in df.iterrows():
        code = str(row.get("代码", ""))
        name = str(row.get("名称", ""))
        seat = str(row.get("营业部名称", ""))
        buy = float(row.get("买入金额", 0) or 0)
        sell = float(row.get("卖出金额", 0) or 0)
        net = buy - sell
        
        key = f"{code}"
        if key not in stocks:
            stocks[key] = {
                "code": code,
                "name": name,
                "seats": [],
                "total_buy": 0,
                "total_sell": 0,
            }
        
        stocks[key]["seats"].append({
            "seat": seat,
            "buy": buy,
            "sell": sell,
            "net": net
        })
        stocks[key]["total_buy"] += buy
        stocks[key]["total_sell"] += sell
    
    # 分析每只票
    for key, stock in stocks.items():
        code = stock["code"]
        name = stock["name"]
        
        # 判断游资/机构/散户构成
        youzi_net = sum(s["net"] for s in stock["seats"] 
                       if any(yz in s["seat"] for yz in FAMOUS_YOUZI))
        inst_net = sum(s["net"] for s in stock["seats"]
                      if any(inst in s["seat"] for inst in INSTITUTION_KEYWORDS))
        
        # 游资净买入>3000万
        if youzi_net > 3000:
            signals["youzi_buy"].append({
                "code": code, "name": name,
                "net": round(youzi_net, 2),
                "signal": "🔥 游资净买入"
            })
        
        # 机构净买入>5000万
        if inst_net > 5000:
            signals["institution_buy"].append({
                "code": code, "name": name,
                "net": round(inst_net, 2),
                "signal": "✅ 机构净买入"
            })
        
        # 散户集中营信号（拉萨席位大量买入）
        lhasa_seats = [s for s in stock["seats"] if "拉萨" in s["seat"]]
        lhasa_net = sum(s["net"] for s in lhasa_seats)
        if lhasa_net > 5000:
            signals["retail_trap"].append({
                "code": code, "name": name,
                "net": round(lhasa_net, 2),
                "signal": "⚠️ 散户集中营大量买入"
            })
    
    return signals

def compare_with_previous(today_signals):
    """对比前一日龙虎榜，识别一日游"""
    files = sorted(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else []
    if len(files) < 1:
        return []
    
    yesterday_file = files[-1]
    with open(os.path.join(OUTPUT_DIR, yesterday_file), "r") as f:
        yesterday = json.load(f)
    
    one_day = []
    yesterday_codes = set()
    if yesterday.get("signals") and yesterday["signals"].get("youzi_buy"):
        yesterday_codes = {s["code"] for s in yesterday["signals"]["youzi_buy"]}
    
    if today_signals.get("youzi_sell"):
        for s in today_signals["youzi_sell"]:
            if s["code"] in yesterday_codes:
                one_day.append({
                    "code": s["code"],
                    "name": s["name"],
                    "signal": "💀 一日游！昨日游资买今日游资卖"
                })
    
    return one_day

def main():
    print("=" * 60)
    print(f"🐉 刘备 V3.1 · 龙虎榜监控")
    print(f"   时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 拉取今日龙虎榜
    today = datetime.now().strftime("%Y%m%d")
    print(f"\n📡 拉取龙虎榜数据 ({today})...")
    df = fetch_longhubang(today)
    
    if df is None or len(df) == 0:
        print("  ⚠️ 今日无龙虎榜数据（可能非交易日）")
        return
    
    print(f"  ✅ 获取到 {len(df)} 条席位数据")
    
    # 分析
    signals = analyze_longhubang(df)
    one_day = compare_with_previous(signals)
    
    # 输出
    print(f"\n🔥 游资净买入>3000万 ({len(signals.get('youzi_buy',[]))}只)：")
    print("-" * 60)
    if signals.get("youzi_buy"):
        for s in signals["youzi_buy"]:
            print(f"  {s['code']} {s['name']:<8} 净买入 ¥{s['net']/10000:.0f}万")
    else:
        print("  （无）")
    
    print(f"\n✅ 机构净买入>5000万 ({len(signals.get('institution_buy',[]))}只)：")
    print("-" * 60)
    if signals.get("institution_buy"):
        for s in signals["institution_buy"]:
            print(f"  {s['code']} {s['name']:<8} 净买入 ¥{s['net']/10000:.0f}万")
    else:
        print("  （无）")
    
    print(f"\n⚠️ 散户集中营信号 ({len(signals.get('retail_trap',[]))}只)：")
    print("-" * 60)
    if signals.get("retail_trap"):
        for s in signals["retail_trap"]:
            print(f"  {s['code']} {s['name']:<8} 拉萨席位 ¥{s['net']/10000:.0f}万")
    else:
        print("  （无）")
    
    if one_day:
        print(f"\n💀 一日游预警 ({len(one_day)}只)：")
        print("-" * 60)
        for s in one_day:
            print(f"  {s['code']} {s['name']:<8} {s['signal']}")
    
    # 保存
    output = {
        "date": today,
        "scan_time": datetime.now().isoformat(),
        "total_records": len(df),
        "signals": signals,
        "one_day_tour": one_day
    }
    
    filename = os.path.join(OUTPUT_DIR, f"{today}.json")
    with open(filename, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📁 报告已保存：{filename}")
    
    return signals

if __name__ == "__main__":
    main()
