"""
S8-S12: 补充Setup定义（写入setups.py用）
这里先独立测试，验证后再合并
"""

import pandas as pd
import numpy as np

# ============================================
# S8: 半导体恐慌大跌后的反弹
# ============================================
def signal_S8_恐慌买入(data, idx):
    """
    条件：半导体单日跌>3% + 量>1.5x均值 + 大盘没崩（非系统性风险）
    逻辑：恐慌性抛售后的超跌反弹
    """
    if idx < 0 or idx >= len(data):
        return False
    row = data.iloc[idx]

    # 半导体跌>3%
    semi = row.get('半导体ETF_pct')
    if pd.isna(semi) or semi > -3.0:
        return False

    # 量>1.5x
    vol_ratio = row.get('半导体ETF_vol_ratio')
    if pd.isna(vol_ratio) or vol_ratio < 1.5:
        return False

    # 大盘非系统性崩盘（上证不跌>3%）
    sz = row.get('上证指数_pct')
    if pd.isna(sz) or sz < -3.0:
        return False

    return True


# ============================================
# S10: 板块轮动——有色转弱+新能源转强
# ============================================
def signal_S10_板块轮动_有色to新能源(data, idx):
    """
    条件：有色跌 + 新能源涨 + 新能源反超有色的前一天
    捕捉板块轮动节点
    """
    if idx < 1 or idx >= len(data):
        return False
    row = data.iloc[idx]
    prev = data.iloc[idx - 1]

    # 有色今天跌
    ys = row.get('有色ETF_pct')
    if pd.isna(ys) or ys > -0.5:
        return False

    # 新能源今天涨
    xny = row.get('新能源ETF_pct')
    if pd.isna(xny) or xny < 0.5:
        return False

    # 新能源反超有色（今天和昨天比较）
    ys_prev = prev.get('有色ETF_pct')
    xny_prev = prev.get('新能源ETF_pct')
    if pd.isna(ys_prev) or pd.isna(xny_prev):
        return False

    # 昨天有色涨更多，今天新能源涨更多 = 切换
    if ys_prev > xny_prev and xny > ys:
        return True

    return False


# ============================================
# S11: 半导体连续2日上涨（温和走强）
# ============================================
def signal_S11_半导体连续走强(data, idx):
    """
    条件：半导体连续2日涨幅>0%，量比>1.0
    信号：温和放量走强，非高潮
    """
    if idx < 1 or idx >= len(data):
        return False

    for d in range(2):
        row = data.iloc[idx - d]
        pct = row.get('半导体ETF_pct')
        vol_ratio = row.get('半导体ETF_vol_ratio')
        if pd.isna(pct) or pd.isna(vol_ratio):
            return False
        if pct < 0 or vol_ratio < 0.8:
            return False

    return True


# ============================================
# S12: 大盘跌但半导体缩量不跌（企稳信号）
# ============================================
def signal_S12_缩量企稳(data, idx):
    """
    条件：大盘跌>0.5%，半导体跌幅<0.3%且量<0.8x均值
    信号：抛压衰竭，企稳
    """
    if idx < 1 or idx >= len(data):
        return False
    row = data.iloc[idx]

    # 大盘跌
    sz = row.get('上证指数_pct')
    if pd.isna(sz) or sz > -0.5:
        return False

    # 半导体几乎不跌
    semi = row.get('半导体ETF_pct')
    if pd.isna(semi) or semi < -0.3:
        return False

    # 缩量
    vol_ratio = row.get('半导体ETF_vol_ratio')
    if pd.isna(vol_ratio) or vol_ratio > 0.8:
        return False

    return True


# ============================================
# 批量回测函数
# ============================================
def run_extra_backtests(data):
    """跑S8-S12的回测"""
    new_setups = {
        "S8_恐慌买入": {"func": signal_S8_恐慌买入, "name": "半导体恐慌大跌后的反弹",
                      "lookahead": [1, 3, 5]},
        "S10_板块轮动_有色to新能源": {"func": signal_S10_板块轮动_有色to新能源, "name": "有色转弱+新能源转强",
                            "lookahead": [1, 3, 5]},
        "S11_半导体连续走强": {"func": signal_S11_半导体连续走强, "name": "半导体连续2日温和走强",
                         "lookahead": [1, 3, 5]},
        "S12_缩量企稳": {"func": signal_S12_缩量企稳, "name": "大盘跌但半导体缩量不跌",
                      "lookahead": [1, 3, 5]},
    }

    print("\n" + "=" * 70)
    print("📊 补充Setup回测 (S8-S12)")
    print("=" * 70)

    for sid, s in new_setups.items():
        func = s["func"]
        lookahead = s["lookahead"]

        signal_indices = []
        for i in range(len(data)):
            if func(data, i):
                signal_indices.append(i)

        total = len(signal_indices)
        print(f"\n{sid} — {s['name']}")
        print(f"  信号数: {total}")

        if total == 0:
            continue

        for days in lookahead:
            wins = 0
            valid = 0
            returns = []
            for idx in signal_indices:
                target = idx + days
                if target >= len(data):
                    continue
                entry = data.iloc[idx].get('半导体ETF_close')
                exit_ = data.iloc[target].get('半导体ETF_close')
                if pd.notna(entry) and pd.notna(exit_) and entry > 0:
                    ret = (exit_ / entry - 1) * 100
                    returns.append(ret)
                    valid += 1
                    if ret > 0:
                        wins += 1

            win_rate = wins / valid * 100 if valid > 0 else 0
            avg_ret = np.mean(returns) if returns else 0
            flag = "✅" if win_rate > 50 else ("🟡" if win_rate > 40 else "💀")
            print(f"  {flag} {days}日: {win_rate:.0f}% ({wins}/{valid}) 均值{avg_ret:+.1f}%")

    return new_setups


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/lyu/.openclaw/workspace/memory/probability_trading')
    from backtest_v2 import prepare_limited_data

    data, _, _ = prepare_limited_data()
    if data is not None:
        results = run_extra_backtests(data)
