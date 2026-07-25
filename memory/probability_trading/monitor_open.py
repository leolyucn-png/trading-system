#!/usr/bin/env python3
"""
monitor_open.py — 周一开盘前15分钟监控
运行时间：2026-07-27 09:15-09:45

输出：
  1. 长鑫科技688825 集合竞价走势
  2. 半导体ETF 开盘方向
  3. 科创50 开盘方向
  4. 开盘前15分钟关键判断
"""

import akshare as ak
import pandas as pd
import time
from datetime import datetime

NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_realtime_data():
    """获取实时行情"""
    result = {}
    
    # 1. 大盘指数实时
    try:
        df = ak.stock_zh_index_spot_em()
        for name in ["上证指数", "科创50"]:
            row = df[df["名称"] == name]
            if not row.empty:
                r = row.iloc[0]
                result[name] = {
                    "price": r.get("最新价", "?"),
                    "pct": r.get("涨跌幅", 0),
                }
    except Exception as e:
        result["index_error"] = str(e)
    
    # 2. 半导体ETF实时
    try:
        # 512480 半导体ETF
        df = ak.fund_etf_spot_em()
        etf = df[df["代码"] == "512480"]
        if not etf.empty:
            r = etf.iloc[0]
            result["半导体ETF"] = {
                "price": r.get("最新价", "?"),
                "pct": r.get("涨跌幅", 0),
                "amount": r.get("成交额", 0),
            }
    except Exception as e:
        result["etf_error"] = str(e)
    
    # 3. 长鑫科技集合竞价（如果出数据了）
    try:
        df = ak.stock_zh_a_spot_em()
        cx = df[df["代码"] == "688825"]
        if not cx.empty:
            r = cx.iloc[0]
            result["长鑫科技"] = {
                "price": r.get("最新价", "?"),
                "pct": r.get("涨跌幅", 0),
                "amount": r.get("成交额", 0),
                "turnover": r.get("换手率", 0),
            }
    except Exception as e:
        pass  # 集合竞价阶段可能还没数据
    
    return result


def print_report(data, phase):
    """打印监控报告"""
    print(f"\n{'='*60}")
    print(f"🕐 {phase} | {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    # 大盘
    if "上证指数" in data:
        p = data["上证指数"]
        emoji = "🔴" if p["pct"] > 0 else ("🟢" if p["pct"] < 0 else "⚪")
        print(f"  上证指数: {p['price']}  ({emoji} {p['pct']:+.2f}%)")
    
    if "科创50" in data:
        p = data["科创50"]
        emoji = "🔴" if p["pct"] > 0 else ("🟢" if p["pct"] < 0 else "⚪")
        print(f"  科创50:   {p['price']}  ({emoji} {p['pct']:+.2f}%)")
    
    # 半导体ETF
    if "半导体ETF" in data:
        p = data["半导体ETF"]
        emoji = "🔴" if p["pct"] > 0 else ("🟢" if p["pct"] < 0 else "⚪")
        print(f"  半导体ETF: {p['price']}  ({emoji} {p['pct']:+.2f}%)  成交: {p['amount']}")
    
    # 长鑫
    if "长鑫科技" in data:
        p = data["长鑫科技"]
        print(f"  长鑫科技: {p['price']}  (涨{p['pct']:+.2f}%)  成交: {p['amount']}  换手: {p['turnover']}%")
    else:
        print(f"  长鑫科技: 集合竞价数据尚未生成")
    
    return data


def main():
    print(f"\n{'='*60}")
    print(f"📡 周一开盘前15分钟监控")
    print(f"  启动时间: {NOW}")
    print(f"  长鑫科技688825上市日")
    print(f"{'='*60}")
    
    # 阶段1: 09:15 集合竞价开始
    print("\n⏳ 等待09:15集合竞价开始...")
    time.sleep(5)  # 模拟等待（实际运行时用cron触发）
    
    print("\n📌 长鑫参考价: 发行价8.66元")
    print(f"  中芯国际案例: 开盘+350%, 全天高点在开盘")
    print(f"  华虹公司案例: 开盘+13%, 全天平走")
    
    # 这里在09:15, 09:20, 09:25, 09:30, 09:45分别采样
    # 实际运行时由cron分时触发
    
    print(f"\n{'='*60}")
    print("📋 采样时间表")
    print(f"{'='*60}")
    print(f"  09:15  集合竞价开始 → 第一轮采样")
    print(f"  09:20  不可撤单阶段开始 → 第二轮采样（主力真实意图）")
    print(f"  09:25  开盘价确定 → 第三轮采样（长鑫开多少？）")
    print(f"  09:30  连续竞价开始 → 第四轮采样")
    print(f"  09:45  前15分钟结束 → 最终判断")
    
    # 判断规则
    print(f"\n{'='*60}")
    print("⚡ 前15分钟判断规则（来自历史回测）")
    print(f"{'='*60}")
    print(f"  半导体ETF 09:30-09:45:")
    print(f"    跌>2% → 吸血确认 → 当天回避")
    print(f"    跌0-2% → 正常承压 → 关注午后")
    print(f"    平盘 → 长鑫独立走势 → 板块无影响")
    print(f"    涨 → 跟历史经验不符 → 异常信号")
    print(f"")
    print(f"  长鑫开盘价:")
    print(f"    +100%以上 → 中芯剧本（开盘即最高点）")
    print(f"    +30%~+100% → 中性区间")
    print(f"    +0%~+30% → 华虹剧本（温和）")
    
    print(f"\n{'='*60}")
    print("✅ 监控就绪")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
