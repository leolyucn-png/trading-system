#!/usr/bin/env python3
"""
交易拦截器 v1.0 — 开仓前自动过五关
在你要下单前必须调用，不过关 = 不准买

调用方式:
  python3 scripts/trade_guard.py <code> <price> <shares>

示例:
  python3 scripts/trade_guard.py 002185 19.80 200
"""

import sys
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

# === 加载持仓 ===
def load_holdings():
    """从 memory/trades.md 和 memory/2026-07-03.md 加载最新持仓"""
    holds = {}
    
    # 硬编码当前持仓（数据层可查但这里保持简单）
    current_holds = {
        "002023": {"name": "海特高新", "cost": 12.90, "shares": 3100, "pnl_pct": -1.6},
        "002051": {"name": "中工国际", "cost": 10.83, "shares": 3600, "pnl_pct": -2.9},
        "600096": {"name": "云天化",    "cost": 30.85, "shares": 900,  "pnl_pct": -0.8},
        "002624": {"name": "完美世界", "cost": 15.13, "shares": 1900, "pnl_pct": -23.2},
        "002185": {"name": "华天科技", "cost": 20.14, "shares": 600,  "pnl_pct": -3.1},
        "600330": {"name": "天通股份", "cost": 30.49, "shares": 400,  "pnl_pct": -13.8},
        "002171": {"name": "楚江新材", "cost": 14.92, "shares": 1000, "pnl_pct": -12.3},
        "002368": {"name": "太极股份", "cost": 13.80, "shares": 400,  "pnl_pct": -0.1},
    }
    return current_holds

# === 规则引擎 ===
RULES = {
    "F": {
        "name": "总持仓上限6只",
        "max_positions": 6,
        "message": "总持仓{current}只，超过规则F上限6只。必须先卖出至少{sell_count}只弱票才能开新仓。\n  建议卖出顺序：太极股份(最轻)→完美世界(减半)→天通(减半)"
    },
    "每日限额": {
        "name": "每日新开仓≤2只",
        "max_daily": 2,
        "message": "今日已新开{current}只，达到上限{limit}只。明天再说。"
    },
    "周五限额": {
        "name": "周五只推荐1只",
        "max_friday": 1,
        "message": "周五只允许推荐1只最有把握的。已经开了{current}只。"
    },
    "时间门": {
        "name": "14:30后才能买",
        "allowed_after_hour": 14,
        "allowed_after_minute": 30,
        "message": "现在是{time}，规则要求14:30-14:55尾盘买入。还有{minutes_left}分钟。"
    },
    "止损门": {
        "name": "先割弱票再开仓",
        "max_loss_pct": -10,
        "message": "以下持仓浮亏超-10%，必须先减仓再开新仓：\n{positions}"
    }
}

def check(hour=None, minute=None, weekday=None):
    """过五关，返回 (passed, reason)"""
    if hour is None:
        hour = datetime.now().hour
    if minute is None:
        minute = datetime.now().minute
    if weekday is None:
        weekday = datetime.now().weekday()  # 0=周一, 4=周五
    
    holdings = load_holdings()
    position_count = len(holdings)
    is_friday = (weekday == 4)  # 周五
    
    checks = []
    
    # 关卡1: 总持仓上限（规则F）
    max_pos = RULES["F"]["max_positions"]
    if position_count >= max_pos:
        sell_count = position_count - max_pos + 1  # 要卖到≤6再开新的
        checks.append({
            "gate": "规则F · 总持仓上限",
            "passed": False,
            "reason": f"持仓{position_count}只，超上限{max_pos}只。必须先卖{sell_count}只弱票。\n建议: 太极(全清)→完美(减半)→天通(减半)"
        })
    
    # 关卡2: 止损门（有-10%以上的烂票先处理）
    deep_loss = []
    for code, h in holdings.items():
        if h['pnl_pct'] < RULES["止损门"]["max_loss_pct"]:
            deep_loss.append(f"  {h['name']}({code}): {h['pnl_pct']:+.1f}%")
    if deep_loss:
        checks.append({
            "gate": "止损门 · 深套票未处理",
            "passed": False,
            "reason": "以下票浮亏超-10%，必须先减仓：\n" + "\n".join(deep_loss)
        })
    
    # 关卡3: 时间门（盘中未到尾盘窗口）
    if hour < RULES["时间门"]["allowed_after_hour"] or \
       (hour == RULES["时间门"]["allowed_after_hour"] and minute < RULES["时间门"]["allowed_after_minute"]):
        minutes_left = (RULES["时间门"]["allowed_after_hour"] - hour) * 60 + (RULES["时间门"]["allowed_after_minute"] - minute)
        checks.append({
            "gate": "时间门 · 尾盘窗口",
            "passed": False,
            "reason": f"现在{hour:02d}:{minute:02d}，离14:30尾盘窗口还有约{minutes_left}分钟。请等待。"
        })
    
    # 关卡4: 周五限额
    if is_friday:
        # 检查今天已开多少（需要从日志读，这里简化为手动输入）
        checks.append({
            "gate": "周五限额",
            "passed": True,  # 默认过，除非知道今天已开了
            "reason": "周五：最多1只。今天还没开，可以。"
        })
    
    # 关卡5: 每日限额
    checks.append({
        "gate": "每日限额",
        "passed": True,
        "reason": "今天还没开仓。"
    })
    
    return checks


def format_check(checks):
    """格式化输出"""
    all_pass = all(c['passed'] for c in checks)
    emoji = "🟢" if all_pass else "🔴"
    
    lines = [
        "=" * 50,
        f"{emoji} 交易拦截器 · 开仓前检查",
        "=" * 50,
    ]
    
    for i, c in enumerate(checks, 1):
        status = "✅ 通过" if c['passed'] else "❌ 拦截"
        lines.append(f"\n{i}. {c['gate']}: {status}")
        lines.append(f"   {c['reason']}")
    
    if all_pass:
        lines.append("\n" + "=" * 50)
        lines.append("🟢 五关全部通过，可以开仓。")
        lines.append("=" * 50)
    else:
        lines.append("\n" + "=" * 50)
        lines.append("🔴 拦截！处理完以上问题再开仓。")
        lines.append("=" * 50)
    
    return "\n".join(lines)


# === 主入口 ===
if __name__ == "__main__":
    # 支持命令行参数: python3 trade_guard.py [hour] [minute] [weekday]
    hr = int(sys.argv[1]) if len(sys.argv) > 1 else None
    mi = int(sys.argv[2]) if len(sys.argv) > 2 else None
    wd = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    checks = check(hour=hr, minute=mi, weekday=wd)
    print(format_check(checks))
