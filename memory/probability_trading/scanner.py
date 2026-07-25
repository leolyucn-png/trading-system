"""
scanner.py — 实时扫描引擎

每天运行：
  1. 拉最新市场数据
  2. 检查每个Setup是否触发
  3. 输出信号 + 对应历史胜率
  4. 不编原因，只输出概率
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from setups import SETUPS

# 从缓存加载概率矩阵
PROB_DIR = os.path.join(os.path.dirname(__file__), "outputs")
PROB_FILE = os.path.join(PROB_DIR, "probability_matrix.json")


def load_probability_matrix():
    """加载已计算的概率矩阵"""
    if os.path.exists(PROB_FILE):
        with open(PROB_FILE, 'r') as f:
            return json.load(f)
    return {}


def format_win_rate(wr_dict):
    """格式化胜率文本"""
    parts = []
    for k, v in sorted(wr_dict.items()):
        if isinstance(v, float) or isinstance(v, int):
            emoji = "✅" if v > 50 else ("🟡" if v > 40 else "💀")
            parts.append(f"{emoji} {k}: {v}%")
    return " | ".join(parts) if parts else "暂无数据"


def run_scanner():
    """运行盘中扫描"""
    print("\n" + "=" * 70)
    print(f"🔍 实时扫描 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # 加载概率矩阵
    prob = load_probability_matrix()
    if not prob:
        print("⚠️ 概率矩阵为空（尚未运行回测）")
        return {}

    print(f"\n📋 概率矩阵已加载: {len(prob)} 个Setup")

    # 加载最新市场数据（从缓存）
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_all_sectors, load_all_indices

    sectors = load_all_sectors(force_refresh=False)
    indices = load_all_indices(force_refresh=False)

    # 获取最新日期
    latest = None
    for name, df in sectors.items():
        if df is not None and len(df) > 0:
            d = df['date'].max()
            if latest is None or d > latest:
                latest = d

    if latest is None:
        print("❌ 无市场数据")
        return {}

    print(f"\n📅 最新数据日期: {latest.date()}")
    print("-" * 70)

    # 获取最新一行
    signals_found = False
    for sid, setup in SETUPS.items():
        if not setup.get("enabled", False):
            continue

        win_rates = prob.get(sid, {}).get("win_rates", {})
        total_signals = prob.get(sid, {}).get("total_signals", 0)
        wr_str = format_win_rate(win_rates)

        # 检查这个setup的名字是否在可用数据中
        print(f"\n{sid}")
        print(f"  {setup['name']}")
        print(f"  历史信号: {total_signals}次")
        if wr_str:
            print(f"  历史胜率: {wr_str}")
        else:
            print(f"  历史胜率: <未回测>")

    print("\n" + "=" * 70)
    print("📌 说明")
    print("=" * 70)
    print("• 所有Setup已列出，但盘中实时触发检查需盘后运行")
    print("• 概率矩阵来自历史回测，非预测")
    print("• 当Setup触发时，参考其历史胜率做决策")
    print("  - 胜率>65%: 可执行")
    print("  - 胜率50-65%: 谨慎（带止损）")
    print("  - 胜率<50%: 不执行")
    print("• 信号数<10的Setup暂不可靠")
    print("• 每次交易后更新Setup胜率（贝叶斯更新）")

    return prob


def check_signal_now():
    """
    检查当前是否有Setup触发
    在交易时段调用（09:30-15:00）
    """
    print("\n🚦 盘中信号检查")
    print("-" * 40)

    data = _get_latest_row()
    if data is None:
        print("❌ 无法获取实时数据")
        return

    # 导入信号函数
    from backtest_v2 import (
        signal_S1_抗跌逆势, signal_S2_放量不涨, signal_S3_科技独立走强,
        signal_S5_跌幅收窄, signal_S7_暴涨后冷静, signal_S9_半导体领涨
    )
    from data_loader import prepare_limited_data

    df, _, _ = prepare_limited_data()
    if df is None or len(df) < 2:
        print("❌ 无历史数据用于对比")
        return

    # 检查最新一行是否触发信号
    last_idx = len(df) - 1

    for name, func in [
        ("S1_抗跌逆势_半导体", signal_S1_抗跌逆势),
        ("S2_暗流建仓_放量不涨", signal_S2_放量不涨),
        ("S3_科技独立走强_大盘掩护", signal_S3_科技独立走强),
        ("S5_深V反转_空头衰竭", signal_S5_跌幅收窄),
        ("S7_暴涨后冷静期", signal_S7_暴涨后冷静),
    ]:
        triggered = func(df, last_idx)
        if triggered:
            row = df.iloc[last_idx]
            semi_pct = row.get('半导体ETF_pct', '?')
            print(f"  🚨 {name} 触发！(半导体{'+' if semi_pct != '?' and semi_pct > 0 else ''}{semi_pct})")
        else:
            print(f"  ⏹️  {name} 未触发")

    print("-" * 40)


def _get_latest_row():
    """获取最新的市场数据行"""
    try:
        from data_loader import prepare_limited_data
        df, _, _ = prepare_limited_data()
        if df is not None and len(df) > 0:
            return df.iloc[-1]
    except:
        pass
    return None


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    run_scanner()
