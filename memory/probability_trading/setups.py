"""
setups.py — 交易情景定义层

每个 Setup = 一组可测量的条件 + 历史胜率
不编故事，只记录：当条件X出现时，后续Y日涨跌概率P%

每次交易后更新胜率 → 系统自我校准
"""

# 可用条件类型（可组合）：
# market_change  : 大盘当日涨跌 (%)
# sector_change  : 板块ETF当日涨跌 (%)
# sector_flow    : 板块主力资金净流入 (元)
# stock_volume   : 个股量比
# stock_pos      : 个股在板块内位置（涨幅排名/成交额排名）
# prev_day       : 前一日的某项值
# consecutive    : 连续满足某条件的天数

SETUPS = {
    "S1_抗跌逆势_半导体": {
        "name": "半导体抗跌逆势",
        "description": "大盘跌>1%，半导体ETF涨>0%，主力资金加速流入",
        "conditions": {
            "market_change": {"max": -1.0},
            "sector": "半导体ETF",
            "sector_change": {"min": 0.0},
            "sector_flow": {"min": 10_0000_0000},  # 10亿
        },
        "lookahead_days": [1, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S2_暗流建仓_放量不涨": {
        "name": "板块放量不涨（暗流建仓）",
        "description": "板块连续2日量>1.3x均量，价格波动<1%，主力净流入",
        "conditions": {
            "sector": "ANY",
            "consecutive_days": 2,
            "volume_ratio": {"min": 1.3},
            "price_change_range": {"max": 1.0},
            "sector_flow": {"min": 5_0000_0000},  # 5亿
        },
        "lookahead_days": [1, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S3_科技独立走强_大盘掩护": {
        "name": "科技独立走强（大盘掩护）",
        "description": "全市场4900+下跌背景下，科创50翻红，半导体逆势涨",
        "conditions": {
            "market_decline_count": {"min": 4000},  # 下跌家数
            "sector": "半导体ETF",
            "sector_change": {"min": 1.0},
            "kechuang50_change": {"min": 0.0},
        },
        "lookahead_days": [1, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S4_板块切换_新主线起势": {
        "name": "新主线反超老主线（龙头赛马）",
        "description": "老主线连续强势3天+新主线在旧主线强势中悄然走强+午后反超",
        "conditions": {
            "sector_old": None,  # 动态赋值
            "sector_new": None,  # 动态赋值
            "old_streak_days": {"min": 2},
            "new_overtake": True,  # 新板块午后涨幅 > 老板块
        },
        "lookahead_days": [1, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S5_深V反转_空头衰竭": {
        "name": "深V反转（空头衰竭）",
        "description": "板块/大盘早盘崩溃-3~4%，午后V转反攻，收盘跌幅收窄",
        "conditions": {
            "sector": "ANY",
            "intraday_low": {"max": -3.0},  # 盘中最低跌幅
            "intraday_recovery": {"min": 2.0},  # 从最低点反弹幅度
            "close_not_reversed": True,  # 尾盘未反噬
        },
        "lookahead_days": [1, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S6_全球暴跌后V反": {
        "name": "全球同步暴跌后快速修复",
        "description": "全球同步暴跌（非A股独立问题），2-3日内修复",
        "conditions": {
            "global_crash_day": True,
            "day_offset": 0,  # Day 0 = 暴跌日
        },
        "lookahead_days": [1, 2, 3, 5],
        "stats": {"total_signals": 0, "wins_1d": 0, "wins_2d": 0, "wins_3d": 0, "wins_5d": 0},
        "enabled": True
    },

    "S7_暴涨后冷静期": {
        "name": "单日暴涨后3日回调（模式30）",
        "description": "单日板块暴涨>6%→后3日回调, 第4-5日企稳",
        "conditions": {
            "sector": "ANY",
            "sector_spike": {"min": 6.0},  # 单日暴涨>6%
        },
        "lookahead_days": [-1, -2, -3, 3, 4, 5],  # -N = 回调日, +N = 企稳后
        "stats": {"total_signals": 0, "wins_3d": 0, "wins_4d": 0, "wins_5d": 0},
        "enabled": True
    },
}


def get_enabled_setups():
    """返回所有启用的setup"""
    return {k: v for k, v in SETUPS.items() if v.get("enabled", False)}


def get_setup_summary():
    """打印所有setup的当前胜率"""
    lines = []
    for sid, s in SETUPS.items():
        if not s.get("enabled", False):
            continue
        t = s["stats"]["total_signals"]
        if t == 0:
            lines.append(f"{sid} ({s['name']}) — 尚无信号")
        else:
            rates = []
            for k, v in s["stats"].items():
                if k != "total_signals":
                    rates.append(f"{k}: {v/t*100:.0f}%({v}/{t})")
            lines.append(f"{sid} ({s['name']}) — {t}次信号 — {' | '.join(rates)}")
    return "\n".join(lines)
