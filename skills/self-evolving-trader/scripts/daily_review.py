#!/usr/bin/env python3
"""
汉武帝 — 每日自我复盘+进化脚本

收盘后运行：
1. 读取当日交易记录
2. 对比预测 vs 实际
3. 提取新模式/教训
4. 追加到经验教训库
5. 更新汉武帝计划版本号
"""

import os
import sys
from datetime import datetime



HOME = os.path.expanduser("~")
WORKSPACE = os.path.join(HOME, ".openclaw", "workspace")
TRADES_FILE = os.path.join(WORKSPACE, "memory", "trades.md")
LESSONS_FILE = os.path.join(WORKSPACE, "memory", "经验教训库.md")
LOG_DIR = os.path.join(WORKSPACE, "memory", "交易日志")
FRAMEWORK_FILE = os.path.join(WORKSPACE, "memory", "汉武帝计划.md")


def read_trades():
    """Read current trades to get state"""
    if not os.path.exists(TRADES_FILE):
        return "无持仓数据"
    with open(TRADES_FILE) as f:
        return f.read()


def append_lesson(tag, title, content):
    """Append a new lesson to the lessons database"""
    date = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n### {date} — {title}\n\n**标签：** {tag}\n{content}\n"

    if os.path.exists(LESSONS_FILE):
        with open(LESSONS_FILE) as f:
            existing = f.read()
        # Insert before "## 待验证的假设"
        if "## 待验证的假设" in existing:
            parts = existing.split("## 待验证的假设")
            existing = parts[0] + entry + "\n## 待验证的假设" + parts[1]
        else:
            existing += entry
        with open(LESSONS_FILE, "w") as f:
            f.write(existing)
    else:
        with open(LESSONS_FILE, "w") as f:
            f.write(f"# 经验教训库 — 汉武帝自我进化\n{entry}\n## 待验证的假设\n")
    return f"✅ 已追加教训：{title}"


def write_daily_log(content):
    """Write daily review log"""
    os.makedirs(LOG_DIR, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(LOG_DIR, f"{date}.md")
    with open(path, "w") as f:
        f.write(f"# 汉武帝交易日志 — {date}\n\n{content}")
    return f"✅ 已写入日志：{path}"


def update_framework_version():
    """Update framework version in 汉武帝计划"""
    if not os.path.exists(FRAMEWORK_FILE):
        return "⚠️ 框架文件不存在"

    today = datetime.now().strftime("%Y-%m-%d")
    with open(FRAMEWORK_FILE) as f:
        content = f.read()

    # Update version if it has one
    if "框架版本：" in content:
        import re
        content = re.sub(
            r"框架版本：v\d+\.\d+",
            lambda m: f"框架版本：{m.group(0).split('：')[0]}：v1.{datetime.now().day}",
            content
        )
        with open(FRAMEWORK_FILE, "w") as f:
            f.write(content)
        return f"✅ 框架版本已更新"


def run_daily_review(trades_summary="", lessons="", hypothesis=""):
    """Main daily review function"""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    print("=" * 50)
    print(f"  🧠 汉武帝每日进化 | {date}")
    print("=" * 50)

    # 1. Read current state
    print(f"\n📂 当前持仓：")
    trades = read_trades()
    print(f"    {trades[:100]}...")

    # 2. Process lessons
    if lessons:
        for tag, title, content in lessons:
            result = append_lesson(tag, title, content)
            print(f"   {result}")

    # 3. Write daily log
    log_content = f"## 当日总结\n{trades_summary}\n\n## 新教训\n{lessons}\n\n## 待验证\n{hypothesis}"
    log_result = write_daily_log(log_content)
    print(f"   {log_result}")

    # 4. Update framework
    ver_result = update_framework_version()
    if ver_result:
        print(f"   {ver_result}")

    print(f"\n{'=' * 50}")
    print(f"  ✅ 今日进化完成")
    print(f"  📍 经验教训库：{LESSONS_FILE}")
    print(f"  📍 交易日志：{LOG_DIR}/")
    print(f"{'=' * 50}")

    return True


if __name__ == "__main__":
    run_daily_review(
        trades_summary="请手动填写当日操作",
        lessons=[],
        hypothesis="请手动填写待验证假设"
    )
