#!/usr/bin/env python3
"""
赵云 V2.0 · 每日复盘总督
========================
收盘后自动运行，整合全系统数据，生成统一的日报。
输出到 ~/Desktop/龙虾炒股/YYYY-MM-DD.md

数据来源: 刘彻、关羽、关平、诸葛亮、刘备、持仓
监管: 赵云负责归因+异常报警
"""
import json, os, sys
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop", "龙虾炒股")
WS = os.path.join(HOME, ".openclaw/workspace")
MEMORY = os.path.join(WS, "memory")

os.makedirs(DESKTOP, exist_ok=True)

today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def read_json(path):
    try:
        with open(path) as f: return json.load(f)
    except: return None

def read_text(path):
    try:
        with open(path) as f: return f.read()
    except: return ""

def safe_float(v, default=0):
    try: return float(v)
    except: return default

# ─── 1. 持仓 ───
holdings = []
trades_path = os.path.join(MEMORY, "trades.md")
trades_text = read_text(trades_path)
# 读取SESSION-STATE
state_path = os.path.join(WS, "SESSION-STATE.md")
state_text = read_text(state_path)

# ─── 2. 刘彻 ───
liuche_report = read_text(os.path.join(MEMORY, "刘彻扫描", f"{today}.md"))

# ─── 3. 关羽 ───
dark_flows = read_json(os.path.join(MEMORY, "暗流历史", f"{today}.json"))
last_flow = dark_flows[-1] if dark_flows else None

# ─── 4. 关平 ───
guanping_report = read_text(os.path.join(MEMORY, "关平扫描", f"{today}.md"))

# ─── 5. 诸葛亮 ───
zhuge_report = read_text(os.path.join(MEMORY, "诸葛亮长期池", f"{today}.md"))

# ─── 6. 大盘数据（从关羽存档读取，非实时API） ───
index_lines = []
if last_flow:
    # 从暗流存档拿ETF数据
    pass

# 从关羽guanyu_status读大盘
state_json = read_json(os.path.join(WS, "scripts", "guanyu_status.json"))
if state_json:
    index_lines.append(f"对账时间: {state_json.get('timestamp','')}")
    index_lines.append(f"对账许可: {'✅' if state_json.get('live_trade_permitted') else '🔴'}")
index_data = '\n'.join(index_lines) if index_lines else '(收盘后数据)'

# ─── 7. 生成日报 ───
report = f"""# 🦞 龙虾炒股日报 | {today}

---

## 📊 大盘

| 指数 | 收盘 | 涨跌 |
|:----|:---:|:---:|
{index_data}

---

## 📦 持仓

```
{trades_text[-500:] if trades_text else '(见 memory/trades.md)'}
```

---

## 🐉 刘彻 · 板块轮动

```
{liuche_report[:2000]}
```

---

## ⚔️ 关羽 · 资金暗流

"""

if last_flow:
    report += f"**时间**: {last_flow['timestamp']}\n\n"
    report += "### ETF方向 TOP5\n\n"
    for name, pct in last_flow.get('etf_top5', []):
        bar = '🚀' if pct>2 else ('🟢' if pct>0 else '🔴')
        report += f"| {bar} {name} | {pct:+.1f}% |\n"
    report += "\n### 暗流 TOP10\n\n"
    report += "| 概念板块 | 涨跌 | 主力流入(亿) |\n"
    report += "|:----|:---:|:---:|\n"
    for f in last_flow.get('dark_flow', []):
        report += f"| {f['board']} | {f['pct']:+.2f}% | {f['inflow_yi']}亿 |\n"
    report += "\n"

report += f"""
---

## 🕊️ 关平 · 科技细分

```
{guanping_report[:1500]}
```

---

## 🏯 诸葛亮 · 长期牛股

```
{zhuge_report[:2000]}
```

---

## 🏹 赵云 · 归因

```
今日操作归因由赵云负责。见 memory/赵云归因/{today}.md
```

---

## 📋 明日预判

```
见关羽14:25尾盘扫描输出
```

---

> 自动生成于 {datetime.now().strftime('%H:%M')} | 赵云 V2.0 总督
"""

out_path = os.path.join(DESKTOP, f"{today}.md")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"✅ 日报 → {out_path}")
print(f"   大小: {len(report)}字符")
print(f"   包含: 大盘/刘彻/关羽/关平/诸葛亮/赵云")
