#!/usr/bin/env python3
"""
刘备 V3.1 · 主运行器
依次执行三大模块，生成综合舆情报告
用法：python3 liubei_runner.py
"""
import sys
import os
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from social_scanner import main as scan_social
from hot_rank import main as scan_hotrank
from longhubang import main as scan_longhubang

def main():
    print("""
╔══════════════════════════════════════════════╗
║     🐉 刘备 V3.1 · 舆情验证引擎              ║
║     社交媒体 + 热搜排名 + 龙虎榜               ║
╚══════════════════════════════════════════════╝
    """)
    
    report = {
        "time": datetime.now().isoformat(),
        "social": {"status": "not_run"},
        "hotrank": {"status": "not_run"},
        "longhubang": {"status": "not_run"},
    }
    
    # 模块1：社交媒体扫描
    print("\n" + "▸" * 30)
    print("  📱 模块1/3：社交媒体异常检测")
    print("▸" * 30)
    try:
        alerts = scan_social()
        report["social"] = {
            "status": "ok",
            "alert_count": len(alerts) if alerts else 0,
            "alerts": alerts
        }
    except Exception as e:
        report["social"]["status"] = f"error: {e}"
        print(f"  ❌ 社交媒体扫描失败: {e}")
    
    # 模块2：热搜排名
    print("\n" + "▸" * 30)
    print("  📊 模块2/3：热搜排名追踪")
    print("▸" * 30)
    try:
        stocks = scan_hotrank()
        report["hotrank"] = {
            "status": "ok",
            "stock_count": len(stocks) if stocks else 0
        }
    except Exception as e:
        report["hotrank"]["status"] = f"error: {e}"
        print(f"  ❌ 热搜排名扫描失败: {e}")
    
    # 模块3：龙虎榜（仅交易日有效）
    print("\n" + "▸" * 30)
    print("  🐉 模块3/3：龙虎榜监控")
    print("▸" * 30)
    try:
        signals = scan_longhubang()
        report["longhubang"] = {
            "status": "ok",
            "signals": signals
        }
    except Exception as e:
        report["longhubang"]["status"] = f"error: {e}"
        print(f"  ❌ 龙虎榜扫描失败: {e}")
    
    # 综合报告
    print("\n" + "=" * 60)
    print("  📋 刘备 V3.1 · 综合舆情报告")
    print("=" * 60)
    
    social_ok = report["social"]["status"] == "ok"
    hotrank_ok = report["hotrank"]["status"] == "ok"
    lhb_ok = report["longhubang"]["status"] == "ok"
    
    print(f"  📱 社交媒体: {'✅' if social_ok else '❌'} {report['social']['status']}")
    if social_ok:
        print(f"     异动警报: {report['social']['alert_count']}条")
    
    print(f"  📊 热搜排名: {'✅' if hotrank_ok else '❌'} {report['hotrank']['status']}")
    if hotrank_ok:
        print(f"     热门股数: {report['hotrank']['stock_count']}只")
    
    print(f"  🐉 龙虎榜:   {'✅' if lhb_ok else '❌'} {report['longhubang']['status']}")
    
    # 保存综合报告
    report_path = SCRIPT_DIR.replace("scripts", "") + f"刘备V3.1_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    try:
        with open(report_path, "w") as f:
            # 简化report避免json序列化问题
            json.dump({
                "time": report["time"],
                "social_status": report["social"]["status"],
                "hotrank_status": report["hotrank"]["status"],
                "longhubang_status": report["longhubang"]["status"]
            }, f, ensure_ascii=False, indent=2)
    except:
        pass
    
    print(f"\n  📁 综合报告: {report_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
