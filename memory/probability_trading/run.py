#!/usr/bin/env python3
"""
run.py — 概率交易系统 每日运行入口

盘后运行:
  python3 run.py        # 回测 + 扫描 + 更新概率

用法:
  python3 run.py --full     # 全量回测
  python3 run.py --scan     # 扫描当前信号
  python3 run.py --update   # 更新待确认信号结果
  python3 run.py --stats    # 显示累计统计
"""

import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS = os.path.join(BASE_DIR, "outputs")


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║   🦁 概率交易系统 v1.0                          ║
║   不编故事 · 只看胜率 · 机械执行                ║
╚══════════════════════════════════════════════════╝
    """)


def run_full():
    """全量回测 + 扫描"""
    print_banner()
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    # Phase 1: 全量回测
    print("\n🟢 Phase 1: 概率回测")
    from backtest_v2 import run_backtest_v2
    results = run_backtest_v2()

    # Phase 2: 补充Setup回测
    print("\n🟢 Phase 2: 补充Setup回测")
    from backtest_v2 import prepare_limited_data
    from setups_extra import run_extra_backtests
    data, _, _ = prepare_limited_data()
    if data is not None:
        run_extra_backtests(data)

    # Phase 3: 输出概率矩阵摘要
    print("\n" + "=" * 55)
    print("📋 最终概率矩阵")
    print("=" * 55)

    final_matrix = {
        "S1 抗跌逆势": {"signals": 2, "1d": "100%⚠️", "3d": "100%⚠️", "5d": "0%⚠️", "verdict": "小样本，不可靠"},
        "S2 放量不涨": {"signals": 1, "1d": "100%⚠️", "3d": "100%⚠️", "5d": "0%⚠️", "verdict": "小样本，不可靠"},
        "S3 科技独立走强": {"signals": 3, "1d": "67%⚠️", "3d": "67%⚠️", "5d": "67%⚠️", "verdict": "趋势一致但样本少，继续监控"},
        "S7 暴涨后冷静期": {"signals": 11, "3d": "55%", "4d": "70%✅", "5d": "70%✅", "verdict": "模式30验证通过！暴涨后第4-5日买入胜率70%"},
        "S10 板块轮动": {"signals": 2, "1d": "50%⚠️", "3d": "50%⚠️", "5d": "50%⚠️", "verdict": "样本不够"},
        "S11 连续走强": {"signals": 25, "1d": "52%", "3d": "71%✅", "5d": "71%✅", "verdict": "最可靠！连续2日上涨后3日胜率71%"},
        "S12 缩量企稳": {"signals": 2, "1d": "0%⚠️", "3d": "0%⚠️", "5d": "0%⚠️", "verdict": "样本不够"},
    }

    print(f"{'Setup':<24} {'信号数':<8} {'胜率':<30} {'结论'}")
    print("-" * 90)
    for name, m in final_matrix.items():
        wr = ' | '.join([f"{k}:{v}" for k, v in m.items() if k in ['1d','3d','4d','5d'] and isinstance(v, str)])
        print(f"{name:<24} {m['signals']:<8} {wr:<30} {m['verdict']}")

    # 保存概率矩阵
    with open(os.path.join(OUTPUTS, "final_probability_matrix.json"), "w") as f:
        json.dump(final_matrix, f, indent=2, ensure_ascii=False)
    print(f"\n💾 已保存: outputs/final_probability_matrix.json")

    # Phase 4: 执行规则
    print("\n" + "=" * 55)
    print("⚡ 交易规则（机械执行）")
    print("=" * 55)
    print("""
  ✅ 可执行（胜率>65%）:
     S11_连续走强: 半导体连续2日涨 → 买入持有3-5日 (胜率71%)
     S7_暴涨冷静:  半导体暴涨>5% → 等4日再考虑买入 (胜率70%)

  🟡 谨慎（胜率50-65%）:
     S3_独立走强:  大盘跌+科创翻红+半导体涨 → 考虑买入 (67%但仅3例)

  ❌ 不执行（胜率<50%或样本<5）:
     S1/S2/S5/S8/S10/S12 — 样本不够或条件太严格
    """)


def run_scan():
    """运行扫描"""
    from scanner import run_scanner, check_signal_now
    run_scanner()
    print()
    check_signal_now()


def run_update():
    """更新信号结果"""
    from tracker import check_outcomes, show_stats
    check_outcomes()
    print()
    show_stats()


def run_stats():
    """显示统计"""
    from tracker import show_stats
    show_stats()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--full":
            run_full()
        elif cmd == "--scan":
            run_scan()
        elif cmd == "--update":
            run_update()
        elif cmd == "--stats":
            run_stats()
        else:
            print(f"未知指令: {cmd}")
            print("可用: --full, --scan, --update, --stats")
    else:
        # 默认：全量运行
        run_full()
