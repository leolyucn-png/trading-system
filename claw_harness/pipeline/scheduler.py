"""
pipeline/scheduler.py — 定时任务调度器
"""

import datetime

SCHEDULES = {
    "trading_market_open": {
        "time": "09:25",
        "task": "竞价扫描",
        "enabled": True
    },
    "trading_midday": {
        "time": "11:30",
        "task": "上午复盘",
        "enabled": True
    },
    "trading_tail_start": {
        "time": "14:20",
        "task": "尾盘准备",
        "enabled": True
    },
    "trading_close": {
        "time": "15:00",
        "task": "收盘复盘+记忆写入",
        "enabled": True
    },
    "memory_daily_maintenance": {
        "time": "22:00",
        "task": "每日日志+记忆整理",
        "enabled": True
    }
}

def get_due_tasks():
    """获取当前时间应执行的任务"""
    now = datetime.datetime.now().strftime("%H:%M")
    due = []
    for name, info in SCHEDULES.items():
        if info["enabled"] and info["time"] == now:
            due.append((name, info))
    return due

def list_all():
    """列出所有定时任务"""
    return SCHEDULES
