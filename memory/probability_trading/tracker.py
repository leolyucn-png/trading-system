"""
tracker.py — 信号追踪 & 贝叶斯更新引擎

每个信号被记录为一条记录：
  - setup_id, trigger_date, signal_price
  - outcome (checked after N days): win/loss, return%

每次outcome更新后，重新计算该setup的全局胜率。
系统自我校准，不需要重新开发。
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime, timedelta

TRACK_DIR = os.path.join(os.path.dirname(__file__), "outputs")
SIGNAL_LOG = os.path.join(TRACK_DIR, "signal_log.csv")
PROB_FILE = os.path.join(TRACK_DIR, "probability_matrix.json")

# CSV列
SIGNAL_COLS = [
    "setup_id", "setup_name", "trigger_date", "signal_price",
    "semi_pct", "sz_pct", "note",
    "check_date_1d", "outcome_1d", "return_1d",
    "check_date_3d", "outcome_3d", "return_3d",
    "check_date_5d", "outcome_5d", "return_5d",
]


def init_log():
    """初始化信号日志"""
    if not os.path.exists(SIGNAL_LOG):
        with open(SIGNAL_LOG, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(SIGNAL_COLS)
        print(f"  ✅ 信号日志已创建: {SIGNAL_LOG}")
    return SIGNAL_LOG


def log_signal(setup_id, setup_name, trigger_date, signal_price,
               semi_pct=None, sz_pct=None, note=""):
    """记录一个信号"""
    init_log()

    # 确保日期格式
    if hasattr(trigger_date, 'strftime'):
        trigger_date = trigger_date.strftime('%Y-%m-%d')

    with open(SIGNAL_LOG, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            setup_id, setup_name, trigger_date, signal_price,
            semi_pct, sz_pct, note,
            "", "", "",  # 1d results (TBD)
            "", "", "",  # 3d results (TBD)
            "", "", "",  # 5d results (TBD)
        ])
    print(f"  📝 信号已记录: {setup_name} @ {trigger_date} 价格={signal_price}")


def check_outcomes():
    """
    检查所有待确认的信号（outcome为空的行）
    需要市场数据来判断
    """
    if not os.path.exists(SIGNAL_LOG):
        print("❌ 无信号日志")
        return

    # 加载最新数据
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import prepare_limited_data
    df, _, _ = prepare_limited_data()
    if df is None:
        print("❌ 无市场数据")
        return

    # 构建日期→价格映射
    price_map = {}
    for _, row in df.iterrows():
        d = row['date']
        price_map[d] = {
            '半导体ETF_close': row.get('半导体ETF_close'),
            '上证指数_close': row.get('上证指数_close'),
        }

    # 读取日志
    rows = []
    updated = 0
    with open(SIGNAL_LOG, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trigger_date = pd.to_datetime(row['trigger_date'])
            signal_price = float(row['signal_price']) if row['signal_price'] else None

            # 检查1日、3日、5日结果
            for days, prefix in [(1, '1d'), (3, '3d'), (5, '5d')]:
                check_col = f'check_date_{prefix}'
                outcome_col = f'outcome_{prefix}'
                return_col = f'return_{prefix}'

                if row[outcome_col] != "":
                    continue  # 已有结果

                target_date = trigger_date + timedelta(days=days)
                # 因为周末/节假日，找最近的交易日
                closest_price = None
                for d in sorted(price_map.keys()):
                    if d >= target_date:
                        closest_price = price_map[d].get('半导体ETF_close')
                        break

                if closest_price is not None and signal_price and signal_price > 0:
                    ret = (closest_price / signal_price - 1) * 100
                    row[check_col] = target_date.strftime('%Y-%m-%d')
                    row[outcome_col] = "win" if ret > 0 else "loss"
                    row[return_col] = f"{ret:.2f}"
                    updated += 1

            rows.append(row)

    if updated > 0:
        # 重写日志
        with open(SIGNAL_LOG, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=SIGNAL_COLS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  ✅ {updated} 个信号结果已更新")

        # 更新概率矩阵
        update_probability_matrix(rows)
    else:
        print("  ⏹️  无待确认的信号")


def update_probability_matrix(rows):
    """从信号日志重新计算每个Setup的胜率"""
    if not rows:
        print("  ⚠️ 无信号数据")
        return

    # 加载现有概率矩阵
    prob = {}
    if os.path.exists(PROB_FILE):
        with open(PROB_FILE, 'r') as f:
            prob = json.load(f)

    # 按setup_id分组
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        sid = r['setup_id']
        groups[sid].append(r)

    for sid, signals in groups.items():
        # 只统计有结果的行
        for prefix in ['1d', '3d', '5d']:
            wins = sum(1 for s in signals if s.get(f'outcome_{prefix}') == 'win')
            total = sum(1 for s in signals if s.get(f'outcome_{prefix}') in ['win', 'loss'])
            if total > 0:
                if sid not in prob:
                    prob[sid] = {'total_signals': 0, 'win_rates': {}}
                prob[sid]['total_signals'] = len(signals)
                prob[sid]['win_rates'][f'{prefix}'] = round(wins / total * 100, 1)

                # 更新到SETUPS模块（运行中）
                try:
                    from setups import SETUPS
                    if sid in SETUPS:
                        SETUPS[sid]['stats']['total_signals'] = total
                except:
                    pass

    # 保存
    with open(PROB_FILE, 'w') as f:
        json.dump(prob, f, indent=2, ensure_ascii=False)
    print(f"  💾 概率矩阵已更新 ({len(prob)} 个Setup)")


def show_stats():
    """显示所有Setup的最新统计"""
    if not os.path.exists(SIGNAL_LOG):
        print("❌ 无信号日志")
        return

    print("\n" + "=" * 70)
    print("📊 信号追踪统计")
    print("=" * 70)

    df = pd.read_csv(SIGNAL_LOG)
    print(f"总信号数: {len(df)}")

    # 按setup分组
    for sid in df['setup_id'].unique():
        subset = df[df['setup_id'] == sid]
        name = subset.iloc[0]['setup_name']
        total = len(subset)

        wins_1d = (subset['outcome_1d'] == 'win').sum()
        total_1d = subset['outcome_1d'].notna().sum()
        wr_1d = wins_1d / total_1d * 100 if total_1d > 0 else 0

        wins_3d = (subset['outcome_3d'] == 'win').sum()
        total_3d = subset['outcome_3d'].notna().sum()
        wr_3d = wins_3d / total_3d * 100 if total_3d > 0 else 0

        avg_ret_1d = subset['return_1d'].dropna().astype(float).mean()
        avg_ret_3d = subset['return_3d'].dropna().astype(float).mean()

        print(f"\n  {sid} ({name})")
        print(f"    总信号: {total}")
        print(f"    1日: {wr_1d:.0f}% ({wins_1d}/{total_1d}) 均值{avg_ret_1d:+.1f}%" if total_1d > 0 else "    1日: 无数据")
        print(f"    3日: {wr_3d:.0f}% ({wins_3d}/{total_3d}) 均值{avg_ret_3d:+.1f}%" if total_3d > 0 else "    3日: 无数据")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_outcomes()
    elif len(sys.argv) > 1 and sys.argv[1] == "--stats":
        show_stats()
    else:
        print("用法: python3 tracker.py [--check | --stats]")
        print("  --check : 检查所有待确认信号的结果")
        print("  --stats : 显示累计统计")
