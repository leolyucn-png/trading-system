#!/usr/bin/env python3
"""
汉武帝二进制决策引擎 v2.0
调用方式：python3 scripts/binary_gates.py <action>
Actions: market_check | score <code> <price> <change_pct> <volume_ratio> | daily_summary
"""

import json, sys, os
from datetime import datetime

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
TRADES_FILE = os.path.join(WORKSPACE, "memory", "trades.md")
LESSONS_FILE = os.path.join(WORKSPACE, "memory", "经验教训库.md")

def gate0_market_context(zhonggai_down=False, beixiang_outflow=False, 
                          volume_down=False, sector_rotation_days=0,
                          is_afternoon=False, sentiment=""):
    """GATE 0: 大盘环境判断"""
    fails = []
    if zhonggai_down:
        fails.append("G0.1 中概隔夜下跌→防守")
    if beixiang_outflow:
        fails.append("G0.2 北向流出→防守")
    if volume_down:
        fails.append("G0.3 放量下跌→不买")
    if sector_rotation_days > 5:
        fails.append("G0.4 板块轮动到期→切换")
    if not is_afternoon:
        fails.append("G0.5 非尾盘时段→不买")
    if sentiment in ("高潮", "退潮"):
        fails.append("G0.6 情绪高潮/退潮→防守")
    
    passed = len(fails) == 0
    return {
        "gate": "GATE 0",
        "passed": 1 if passed else 0,
        "verdict": "✅ 可操作" if passed else f"❌ 防守日：{'；'.join(fails)}"
    }

def gate2_score(plate_score, volume_score, price_score, rule_score, quant_score):
    """GATE 2: 综合评分"""
    total = plate_score + volume_score + price_score + rule_score + quant_score
    return {
        "gate": "GATE 2",
        "score": total,
        "passed": 1 if total >= 6 else 0,
        "verdict": f"✅ 评分{total}/10→可执行" if total >= 6 else f"❌ 评分{total}/10→强制放弃（<6）"
    }

def record_trade(stock, direction, signal, score, actual_return):
    """记录交易到经验教训库"""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = 1 if score >= 6 else 0
    correct = 1 if actual_return > 0 else 0
    
    entry = f"""
### {date} — {stock} {direction}
| 字段 | 值 |
|:----|:---|
| 信号 | {signal} |
| 评分 | {score}/10（GATE判定：{"✅通过" if passed else "❌否决"}）|
| 实际收益 | {actual_return:+.1f}% |
| 验证 | {"✅" if correct else "❌"} |
| 规则生效 | {"评分≥6可买" if passed else "评分<6不买"} |
"""
    if os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE, 'a') as f:
            f.write(entry)
    return entry

def daily_summary():
    """输出今日二进制状态"""
    return json.dumps({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "v2.0",
        "gates": {
            "GATE 0": "市场环境",
            "GATE 1": "信号检测",
            "GATE 2": "评分≥6",
            "GATE 3": "执行合规"
        },
        "philosophy": "每个决策点只有0和1。灰色地带=犯错。"
    }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if action == "market_check":
        result = gate0_market_context(
            zhonggai_down=True,
            is_afternoon=False,
            sentiment="发酵偏弱"
        )
        print(json.dumps(result, ensure_ascii=False))
    
    elif action == "score":
        args = sys.argv[2:]
        score = gate2_score(int(args[0]), int(args[1]), int(args[2]), int(args[3]), int(args[4]))
        print(json.dumps(score, ensure_ascii=False))
    
    elif action == "record":
        record_trade(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), float(sys.argv[6]))
    
    elif action == "summary":
        print(daily_summary())
    
    else:
        print("用法：python3 binary_gates.py market_check|score|record|summary")
