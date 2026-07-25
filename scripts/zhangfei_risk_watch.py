#!/usr/bin/env python3
"""
张飞 v2.0 — risk_watch 盘中监控层
====================================
消费calc_indicator的计算结果，结合大盘+刘备舆情，输出盘中预警。
面向刘彻（交易执行）和秦始皇（GATE调整）。

用法：
  python3 zhangfei_risk_watch.py                 # 跑最新计算结果
  python3 zhangfei_risk_watch.py --with-liubei   # 结合刘备舆情
"""

import os, sys, json, datetime as dt

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "zhangfei_output")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "zhangfei_cache")

# ═══════════════════════════════════════════════
# 配置区
# ═══════════════════════════════════════════════
# 持仓联动
POSITION_LIMIT_HIGH_COUNT = 3   # 高位板块≥N只→限制总仓位50%
POSITION_CUT_RATIO = 0.33       # 高位风险确认→减仓比例
WATCH_INTERVAL_MIN = 90         # 刷新间隔(分钟)

# 大盘风险阈值
INDEX_AFTERNOON_DROP = 1.5      # 13:00后加速跌>X%报警
NORTH_FLOW_PANIC = 50           # 北向流出>X亿报警
LIMIT_DOWN_PANIC = 50           # 跌停>X家报警
POSITION_DROP_WARN = 5.0        # 单票日内跌>X%报警
POSITION_DROP_FORCE = 7.0       # 单票跌>X%强制止损评估
BATCH_DROP_WARN = 3             # N只持仓同时跌>3%报警


def get_latest_calc():
    """读取calc层最新结果"""
    path = os.path.join(OUT_DIR, "zhangfei_calc_result.json")
    if not os.path.exists(path):
        print("❌ 无计算结果，请先运行 zhangfei_calc_indicator.py")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ 计算结果文件损坏，请重新运行 zhangfei_calc_indicator.py")
        return None


def run(with_liubei=False):
    print("=" * 60)
    print("🗡️ 张飞 risk_watch · 盘中监控")
    print("=" * 60)

    data = get_latest_calc()
    if data is None:
        return

    results = data['results']
    summary = data['summary']

    now = dt.datetime.now()
    hour = now.hour
    minute = now.minute

    # 1. 大盘时段判断
    if 9 <= hour <= 11 or (13 <= hour <= 14):
        is_trading = True
    else:
        is_trading = False

    print(f"\n📅 时间: {now.strftime('%m-%d %H:%M')}  {'盘中' if is_trading else '盘后'}")

    # 2. 张飞预警输出
    print(f"\n🚨 张飞预警:")
    high_risk = [r for r in results if r.get('risk_level') == "🔴"]
    mid_risk = [r for r in results if r.get('risk_level') == "🟡"]
    low_opp = [r for r in results if r.get('risk_level') == "🟢" and r.get('zone') == "低位"]

    if high_risk:
        print(f"  🔴 高风险({len(high_risk)}只):")
        for r in high_risk:
            note = r.get('risk_note', '')
            print(f"     {r['name']:<10} [{r['zone']}] {r['quadrant']} — {note}")
    else:
        print(f"  🟢 无高风险信号")

    if mid_risk:
        print(f"  🟡 中等风险({len(mid_risk)}只):")
        for r in mid_risk[:5]:
            print(f"     {r['name']:<10} [{r['zone']}] {r['quadrant']}")

    if low_opp:
        print(f"  🟢 低位机会({len(low_opp)}只):")
        for r in low_opp[:5]:
            print(f"     {r['name']:<10} [{r['zone']}] {r['quadrant']} — {r.get('risk_note', '')}")
    else:
        print(f"  🔴 今日无低位机会信号")

    # 3. 仓位联动建议
    print(f"\n📋 仓位联动:")
    high_pos = [r['name'] for r in results if r.get('risk_level') == "🔴"]
    if len(high_pos) >= POSITION_LIMIT_HIGH_COUNT:
        print(f"  ⚠️ ≥{POSITION_LIMIT_HIGH_COUNT}只板块在高位区 → 总仓位上限降至50%")
    elif len(high_pos) > 0:
        print(f"  ⚠️ {len(high_pos)}只板块在高位 → 对应板块禁止新开仓")
    else:
        print(f"  ✅ 无高位预警，仓位不受张飞限制")

    # 4. 与刘备联动（可选）
    if with_liubei:
        liubei_path = os.path.join(os.path.dirname(__file__), "..", "memory", "liubei_output", "liubei_verify_result.json")
        if os.path.exists(liubei_path):
            with open(liubei_path) as f:
                lb = json.load(f)
            print(f"\n🤝 刘备验证: {lb.get('summary', '无')}")
        else:
            print(f"\n🤝 刘备验证: 无数据(未运行)")

    # 5. 保存监控结果
    watch_output = {
        "time": now.strftime("%Y-%m-%d %H:%M"),
        "is_trading": is_trading,
        "high_risk": high_risk,
        "mid_risk": mid_risk,
        "low_opportunity": low_opp,
        "position_advice": {
            "高位板块数": len(high_risk),
            "限制总仓位": len(high_pos) >= POSITION_LIMIT_HIGH_COUNT,
            "禁止新开仓板块": summary['高位预警'],
            "低位关注池": summary['低位机会'],
        }
    }
    with open(os.path.join(OUT_DIR, "zhangfei_watch_result.json"), "w") as f:
        json.dump(watch_output, f, indent=2, ensure_ascii=False)
    print(f"\n💾 已保存: zhangfei_watch_result.json")


if __name__ == "__main__":
    with_lb = "--with-liubei" in sys.argv
    run(with_liubei=with_lb)
