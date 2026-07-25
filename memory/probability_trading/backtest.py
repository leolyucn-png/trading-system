"""
backtest.py — 概率回测引擎

核心功能：
  对每个 Setup，回测历史数据 → 算出条件触发后的胜率
  输出：当条件X出现 → 后续Y日上涨的概率是Z%

不解释原因。只输出统计结果。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from setups import SETUPS, get_enabled_setups
from data_loader import (
    prepare_backtest_data, load_all_indices, load_all_sectors,
    SECTOR_ETFS
)


def run_backtest(setups=None):
    """
    对所有启用的Setup运行回测
    返回概率矩阵 {setup_id: {lookahead: win_rate}}
    """
    if setups is None:
        setups = get_enabled_setups()

    print("\n" + "=" * 70)
    print("🔄 概率回测引擎启动")
    print("=" * 70)

    # 加载数据
    indices = load_all_indices(force_refresh=False)
    sectors = load_all_sectors(force_refresh=False)
    data = prepare_backtest_data(indices, sectors)
    if data is None:
        print("❌ 无数据，回测中止")
        return {}

    probability_matrix = {}

    for sid, setup in setups.items():
        print(f"\n📊 回测: {sid} — {setup['name']}")
        print(f"   {setup['description']}")

        try:
            result = backtest_one(setup, data)
            probability_matrix[sid] = result

            # 更新setup中的stats
            total = result.get('total_signals', 0)
            setup['stats']['total_signals'] = total
            for k, v in result.get('win_rates', {}).items():
                setup['stats'][k] = int(v * total / 100) if total > 0 else 0

            # 打印结果
            if total == 0:
                print(f"   信号数: 0 (条件从未触发)")
            else:
                print(f"   信号数: {total}")
                for k, v in result.get('win_rates', {}).items():
                    print(f"   {k}: {v:.1f}% ({result['details'].get(k, '?')})")

        except Exception as e:
            print(f"   ❌ 回测失败: {e}")
            import traceback
            traceback.print_exc()

    return probability_matrix


def backtest_one(setup, data):
    """单个setup的回测"""
    conds = setup['conditions']
    lookahead = setup['lookahead_days']

    signals = []
    result = {
        'total_signals': 0,
        'win_rates': {},
        'details': {}
    }

    # 遍历所有日期
    for i in range(len(data)):
        row = data.iloc[i]

        # 检查条件
        if check_conditions(conds, row, data, i):
            signals.append(i)

    result['total_signals'] = len(signals)

    if len(signals) == 0:
        return result

    # 对每个lookahead计算胜率
    for days in lookahead:
        wins = 0
        valid = 0
        examples = []

        for idx in signals:
            target_idx = idx + days if days > 0 else idx + days  # days为负时往前查（回调）
            if target_idx < 0 or target_idx >= len(data):
                continue

            target_row = data.iloc[target_idx]

            # 用半导体ETF或基准指数的涨跌判断胜负
            sector_name = conds.get('sector', '半导体ETF')
            if sector_name == 'ANY':
                sector_name = list(SECTOR_ETFS.keys())[0]

            col = f"{sector_name}_close"
            if col not in data.columns:
                col = '上证指数_close'

            # 计算从信号日到目标日的涨跌
            entry_price = row[col]
            exit_price = target_row[col]

            if pd.notna(entry_price) and pd.notna(exit_price) and entry_price > 0:
                ret = (exit_price / entry_price - 1) * 100
                valid += 1
                if ret > 0:
                    wins += 1

                # 记录最近5个信号作为示例
                if len(examples) < 8:
                    examples.append({
                        'signal_date': row['date'].strftime('%m-%d'),
                        'entry': round(entry_price, 3),
                        f'{days}d_exit': round(exit_price, 3),
                        f'{days}d_ret': f"{ret:+.2f}%",
                        'win': ret > 0
                    })

        win_rate = (wins / valid * 100) if valid > 0 else 0
        result['win_rates'][f'{days}d'] = win_rate
        result['details'][f'{days}d'] = f"{wins}/{valid}"

        # 打印示例
        if examples:
            print(f"   {days}日: {win_rate:.0f}% ({wins}/{valid})")
            for ex in examples[:5]:
                mark = "✅" if ex['win'] else "❌"
                print(f"     {mark} {ex['signal_date']} @{ex['entry']} → {ex[f'{days}d_ret']}")

    return result


def check_conditions(conds, row, data, idx):
    """
    检查当前行是否满足所有条件
    条件名与数据列名之间的映射
    """
    for ckey, cval in conds.items():
        if ckey == 'sector':
            continue
        elif ckey == 'lookahead_days':
            continue
        elif ckey == 'consecutive_days':
            continue
        elif ckey == 'volume_ratio':
            continue
        elif ckey == 'price_change_range':
            continue
        elif ckey == 'market_change':
            # 大盘涨跌
            col = '上证指数_pct'
            if col in row and pd.notna(row[col]):
                if 'max' in cval and row[col] > cval['max']:
                    return False
                if 'min' in cval and row[col] < cval['min']:
                    return False
        elif ckey == 'sector_change':
            sector_name = conds.get('sector', '半导体ETF')
            if sector_name == 'ANY':
                continue
            col = f"{sector_name}_pct"
            if col in row and pd.notna(row[col]):
                if 'max' in cval and row[col] > cval['max']:
                    return False
                if 'min' in cval and row[col] < cval['min']:
                    return False
        elif ckey == 'market_decline_count':
            # 下跌家数（暂无法从K线数据获取）
            continue
        elif ckey == 'kechuang50_change':
            col = '科创50_pct'
            if col in row and pd.notna(row[col]):
                if 'max' in cval and row[col] > cval['max']:
                    return False
                if 'min' in cval and row[col] < cval['min']:
                    return False
        elif ckey == 'sector_flow':
            # 资金流向（暂无法历史回溯）
            continue
        elif ckey in ['sector_old', 'sector_new', 'old_streak_days', 'new_overtake',
                       'intraday_low', 'intraday_recovery', 'close_not_reversed',
                       'global_crash_day', 'day_offset', 'sector_spike',
                       'stock_volume', 'stock_pos', 'prev_day', 'volume_ma5']:
            # 暂不支持的条件
            continue
        else:
            # 未知条件，跳过
            continue

    return True


if __name__ == "__main__":
    probability_matrix = run_backtest()

    print("\n" + "=" * 70)
    print("📋 概率矩阵汇总")
    print("=" * 70)
    for sid, pm in sorted(probability_matrix.items()):
        if pm['total_signals'] > 0:
            wr = pm['win_rates']
            wr_str = ' | '.join([f"{k}: {v:.0f}%" for k, v in sorted(wr.items())])
            print(f"  {sid}: {pm['total_signals']}次信号 — {wr_str}")
        else:
            print(f"  {sid}: 无历史信号（条件太严格或缺失数据）")
