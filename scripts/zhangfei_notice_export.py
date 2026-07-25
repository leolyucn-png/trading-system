#!/usr/bin/env python3
"""
张飞 v2.0 — notice_export 信号输出层
========================================
将张飞所有判定结果写入龙虾日志，供赵云复盘读取。

输出目录: memory/longxia_log/YYYY-MM-DD_zhangfei.json
          memory/zhangfei_output/ （中间结果）

用法：python3 zhangfei_notice_export.py
      python3 zhangfei_notice_export.py --full  # 全量运行(data_fetch→calc→risk_watch→export)
"""

import os, sys, json, datetime as dt, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "zhangfei_output")
LONGXIA_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "longxia_log")
os.makedirs(LONGXIA_DIR, exist_ok=True)

CONFIG = {
    "name": "张飞模型V2.0",
    "version": "2.0",
    "created": "2026-07-25",
    "algorithm": "20日价格分位+量价四象限+情绪辅助验证",
    "data_sources": ["akshare ETF日K", "akshare 指数日K"],
}


def run_all():
    """全量运行：data_fetch → calc → risk_watch → export"""
    print("=" * 60)
    print("🗡️ 张飞 notice_export · 全流水线")
    print("=" * 60)

    # 1. data_fetch
    print("\n[1/4] 数据采集...")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "zhangfei_data_fetch.py")])

    # 2. calc
    print("\n[2/4] 指标计算...")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "zhangfei_calc_indicator.py")])

    # 3. risk_watch
    print("\n[3/4] 风险监控...")
    subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "zhangfei_risk_watch.py")])

    # 4. export
    print("\n[4/4] 导出日志...")
    export()


def export():
    """将张飞结果写入龙虾日志"""
    calc_path = os.path.join(OUT_DIR, "zhangfei_calc_result.json")
    watch_path = os.path.join(OUT_DIR, "zhangfei_watch_result.json")

    if not os.path.exists(calc_path):
        print("❌ 无计算结果，跳过导出")
        return

    with open(calc_path) as f:
        calc = json.load(f)

    watch = {}
    if os.path.exists(watch_path):
        with open(watch_path) as f:
            watch = json.load(f)

    today = dt.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(LONGXIA_DIR, f"{today}_zhangfei.json")

    # 构建龙虾日志
    log = {
        "date": today,
        "model": CONFIG,
        "summary": calc.get('summary', {}),
        "watch": {
            "high_risk": watch.get('high_risk', []),
            "mid_risk": watch.get('mid_risk', []),
            "low_opportunity": watch.get('low_opportunity', []),
            "position_advice": watch.get('position_advice', {}),
        },
        "detail_count": len(calc.get('results', [])),
        "compare_yesterday": _compare_yesterday(today),
    }

    with open(log_path, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 龙虾日志已写入: {log_path}")
    print(f"  📊 {log['detail_count']}只板块完成判定")
    print(f"  🔴 高风险: {len(log['watch']['high_risk'])} | "
          f"🟡 中风险: {len(log['watch']['mid_risk'])} | "
          f"🟢 低位机会: {len(log['watch']['low_opportunity'])}")

    return log


def _compare_yesterday(today_str):
    """对比昨日判定结果"""
    yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_log = os.path.join(LONGXIA_DIR, f"{yesterday}_zhangfei.json")
    if os.path.exists(yesterday_log):
        with open(yesterday_log) as f:
            y = json.load(f)
        return {
            "昨日高位预警": len(y.get('watch', {}).get('high_risk', [])),
            "今日高位预警": 0,  # 等待fill
            "变化": "有昨日数据",
        }
    return None


def list_logs():
    """列出所有龙虾日志"""
    logs = sorted([f for f in os.listdir(LONGXIA_DIR) if f.endswith('_zhangfei.json')], reverse=True)
    print(f"\n📋 龙虾日志列表 ({len(logs)}条):")
    for f in logs[:10]:
        path = os.path.join(LONGXIA_DIR, f)
        try:
            with open(path) as fh:
                data = json.load(fh)
            hr = len(data.get('watch', {}).get('high_risk', []))
            lo = len(data.get('watch', {}).get('low_opportunity', []))
            print(f"  {f[:10]}  🔴{hr}  🟢{lo}")
        except:
            print(f"  {f[:10]}")


if __name__ == "__main__":
    if "--full" in sys.argv:
        run_all()
    elif "--list" in sys.argv:
        list_logs()
    else:
        export()
