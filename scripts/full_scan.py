#!/usr/bin/env python3
"""
全系统一键扫描 v1.0
输入股票代码，自动跑完全流水线，输出决策卡

用法:
  python3 scripts/full_scan.py <code>
  python3 scripts/full_scan.py 002185

也可在对话中说: "扫描 002185"
"""

import sys
import json
import os
from pathlib import Path

# 把根目录加入path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_layer import (
    get_quote, get_quotes_batch, get_kline, 
    get_concept_fund_flow, get_holdings_health, CACHE_DIR
)

def scan_stock(code):
    """
    对单只股票跑全流水线
    返回结构化结果
    """
    result = {
        "code": code,
        "timestamp": str(__import__('datetime').datetime.now()),
        "quote": None,
        "kline": None,
        "concept_flow": None,
        "ma5": 0, "ma20": 0,
        "near_support": [],
        "near_resistance": [],
    }
    
    # 关卡1: 行情 + K线
    quote = get_quote(code)
    kline = get_kline(code, days=30)
    
    if not quote and not kline:
        return {"error": f"无法获取{code}的任何数据"}
    
    result["quote"] = quote
    result["kline"] = kline
    
    # 计算关键价位
    if kline and len(kline) >= 5:
        closes = [k['close'] for k in kline]
        highs = [k['high'] for k in kline]
        lows = [k['low'] for k in kline]
        
        result["ma5"] = round(sum(closes[-5:]) / 5, 2)
        result["ma20"] = round(sum(closes[-20:]) / min(20, len(closes)), 2)
        result["week_high"] = max(highs[-5:])
        result["week_low"] = min(lows[-5:])
        result["month_high"] = max(highs)
        result["month_low"] = min(lows)
        result["trend_5d"] = "up" if closes[-1] > closes[-5] else "down"
        result["trend_20d"] = "up" if closes[-1] > sum(closes[-20:])/len(closes[-20:]) else "down"
        
        price = quote.get('price', closes[-1]) if quote else closes[-1]
        # 支撑位
        for level in [result["ma5"], result["ma20"], result["week_low"]]:
            if level and level < price:
                result["near_support"].append(round(level, 2))
        # 压力位
        for level in [result["ma5"], result["ma20"], result["week_high"]]:
            if level and level > price:
                result["near_resistance"].append(round(level, 2))
    
    return result


def format_scan(result):
    """格式化输出"""
    if "error" in result:
        return f"❌ {result['error']}"
    
    q = result["quote"] or {}
    name = q.get('name', '?')
    code = result["code"]
    price = q.get('price', 0)
    chg = q.get('change_pct', 0)
    pe = q.get('pe', 0)
    mkt = q.get('mkt_cap', 0)
    
    lines = [
        "=" * 55,
        f"🔍 全系统一键扫描 · {name} {code}",
        "=" * 55,
        "",
        f"📊 行情: {price:.2f} ({chg:+.2f}%) | PE: {pe:.0f} | 市值: {mkt:.0f}亿",
    ]
    
    if result.get("kline"):
        lines.append(f"📈 MA5: {result['ma5']:.2f} | MA20: {result['ma20']:.2f}")
        lines.append(f"📐 周高: {result.get('week_high',0):.2f} | 周低: {result.get('week_low',0):.2f}")
        lines.append(f"📉 5日趋势: {'⬆️ ' if result.get('trend_5d')=='up' else '⬇️ '}{result.get('trend_5d','?')} | 20日: {'⬆️' if result.get('trend_20d')=='up' else '⬇️'}{result.get('trend_20d','?')}")
    
    if result.get("near_support"):
        lines.append(f"🛡️ 支撑: {', '.join(f'{s:.2f}' for s in result['near_support'])}")
    if result.get("near_resistance"):
        lines.append(f"🎯 压力: {', '.join(f'{r:.2f}' for r in result['near_resistance'])}")
    
    # 近5日K线
    if result.get("kline"):
        lines.append(f"\n📈 近5日K线:")
        for k in result["kline"][-5:]:
            bar = "🟢" if k.get('change_pct', 0) >= 0 else "🔴"
            lines.append(f"  {k['date']} {bar} 收{k['close']:.2f} ({k.get('change_pct',0):+.2f}%)")
    
    return "\n".join(lines)


def scan_portfolio():
    """扫描全部持仓"""
    holds = {
        "002023": {"cost": 12.90, "shares": 3100},
        "002051": {"cost": 10.83, "shares": 3600},
        "600096": {"cost": 30.85, "shares": 900},
        "002624": {"cost": 15.13, "shares": 1900},
        "002185": {"cost": 20.14, "shares": 600},
        "600330": {"cost": 30.49, "shares": 400},
        "002171": {"cost": 14.92, "shares": 1000},
        "002368": {"cost": 13.80, "shares": 400},
    }
    
    h = get_holdings_health(holds)
    
    lines = [
        "=" * 55,
        "📊 全持仓一键扫描",
        "=" * 55,
    ]
    
    # 按浮亏排序
    sorted_holds = sorted(h.items(), key=lambda x: x[1]['pnl_pct'])
    
    total = 0
    for code, d in sorted_holds:
        total += d['pnl']
        s = '🔴' if d['pnl_pct'] < -10 else '🟡' if d['pnl_pct'] < -5 else '🟢'
        lines.append(
            f"  {s} {d['name']:<6} {d['price']:>7.2f} "
            f"浮亏¥{d['pnl']:>+7,.0f} ({d['pnl_pct']:>+5.1f}%) "
            f"PE{d['pe']:>6.0f} 换手{d['turnover']:>5.1f}%"
        )
    
    lines.append(f"\n  {'─'*45}")
    lines.append(f"  合计浮亏: ¥{total:+,.0f}")
    lines.append(f"  持仓数量: {len(h)}只 {'⚠️ 超限!' if len(h) > 6 else '✅'}")
    
    # 建议
    lines.append(f"\n🪓 建议清仓顺序:")
    for code, d in sorted_holds:
        if d['pnl_pct'] < -10:
            lines.append(f"  🔴 {d['name']}: 深套{d['pnl_pct']:+.1f}%，反弹减仓")
        elif d['pnl_pct'] < -5:
            lines.append(f"  🟡 {d['name']}: 浮亏{d['pnl_pct']:+.1f}%，观察")
        elif abs(d['pnl_pct']) < 1 and d['shares'] < 500:
            lines.append(f"  ⚪ {d['name']}: 仓位太轻，可清可留")
    
    return "\n".join(lines)


# === 主入口 ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(scan_portfolio())
    else:
        code = sys.argv[1]
        if code == "all" or code == "全部":
            print(scan_portfolio())
        else:
            r = scan_stock(code)
            print(format_scan(r))
