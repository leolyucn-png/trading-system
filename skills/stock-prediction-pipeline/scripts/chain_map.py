#!/tmp/whisper_venv/bin/python3
"""
产业链映射 + 领先指标预判工具

1. 查询美股→A股映射关系
2. 扫描最近财报日历
3. 自动匹配领先指标
"""

import sys, os, json
from datetime import datetime, timedelta

WHISPER_VENV = "/tmp/whisper_venv"
site_pkg = os.path.join(WHISPER_VENV, "lib", os.listdir(os.path.join(WHISPER_VENV, "lib"))[0], "site-packages")
if site_pkg not in sys.path:
    sys.path.insert(0, site_pkg)

# 产业链映射数据库（可扩展）
CHAIN_MAP = {
    "AMD": {
        "name": "超微半导体",
        "a_share": ["002156", "600584", "002463"],
        "a_share_names": ["通富微电", "长电科技", "沪电股份"],
        "relation": "封测合作伙伴/PCB供应商",
        "leading_indicators": ["PC出货量(IDC)", "数据中心资本开支", "Intel财报"],
    },
    "NVDA": {
        "name": "英伟达",
        "a_share": ["002463", "300308", "002916"],
        "a_share_names": ["沪电股份", "中际旭创(❌创业板)", "深南电路"],
        "relation": "GPU→PCB/光模块/散热",
        "leading_indicators": ["AI芯片需求", "云厂商资本开支", "CoWoS产能"],
    },
    "AAPL": {
        "name": "苹果",
        "a_share": ["002273", "002475", "002241"],
        "a_share_names": ["水晶光电", "立讯精密", "歌尔股份"],
        "relation": "光学/代工/声学",
        "leading_indicators": ["iPhone出货量(IDC)", "供应链订单传闻"],
    },
    "MRVL": {
        "name": "迈威尔科技",
        "a_share": ["002902", "600522"],
        "a_share_names": ["铭普光磁", "中天科技"],
        "relation": "光通信/CPO概念",
        "leading_indicators": ["光模块需求", "数据中心光互连升级"],
    },
    "TSLA": {
        "name": "特斯拉",
        "a_share": ["002594", "300750"],
        "a_share_names": ["比亚迪", "宁德时代(❌创业板)"],
        "relation": "新能源车竞争/供应链",
        "leading_indicators": ["月度销量(乘联会)", "FSD进展"],
    },
    "QCOM": {
        "name": "高通",
        "a_share": ["600498", "600487", "002396"],
        "a_share_names": ["烽火通信", "亨通光电", "星网锐捷"],
        "relation": "通信芯片→通信设备",
        "leading_indicators": ["手机出货量", "物联网需求"],
    },
}


def query_mapping(us_ticker):
    """Query A-share mapping for a US stock"""
    info = CHAIN_MAP.get(us_ticker.upper())
    if not info:
        return f"⚠️ 未找到 {us_ticker} 的A股映射"

    lines = [f"\n📡 {info['name']}({us_ticker.upper()}) → A股映射"]
    lines.append(f"  关联：{info['relation']}")
    lines.append(f"  A股标的：")
    for code, name in zip(info["a_share"], info["a_share_names"]):
        lines.append(f"    📌 {name}({code})")
    lines.append(f"  领先指标：")
    for ind in info["leading_indicators"]:
        lines.append(f"    🔍 {ind}")
    return "\n".join(lines)


def scan_earnings(days_ahead=14):
    """Scan upcoming earnings for mapped US stocks"""
    try:
        import yfinance as yf
    except:
        return "yfinance not installed"

    results = []
    for ticker in CHAIN_MAP.keys():
        try:
            t = yf.Ticker(ticker)
            earnings = t.earnings_dates
            if earnings is None or earnings.empty:
                continue
            now = datetime.now()
            for idx, row in earnings.iterrows():
                if isinstance(idx, datetime) and now <= idx <= now + timedelta(days=days_ahead):
                    eps_est = row.get("EPS Estimate", "N/A")
                    eps_act = row.get("EPS Actual", "N/A")
                    results.append((idx, ticker, CHAIN_MAP[ticker]["name"], eps_est, eps_act))
        except:
            continue

    if not results:
        return f"  未来{days_ahead}天无已知财报"

    lines = [f"\n📅 未来{days_ahead}天财报预告（产业链内）"]
    for dt, ticker, name, est, act in sorted(results):
        date_str = dt.strftime("%m/%d %a")
        lines.append(f"  {date_str} {ticker} {name} 预期EPS:{est}")
    return "\n".join(lines)


if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "help"

    if cmd == "map" and len(sys.argv) > 2:
        print(query_mapping(sys.argv[2]))
    elif cmd == "earnings":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 14
        print(scan_earnings(days))
    elif cmd == "list":
        print("\n📋 产业链映射总表：")
        for ticker, info in sorted(CHAIN_MAP.items()):
            names = ", ".join(info["a_share_names"])
            print(f"  {ticker:6s} → {names}")
    else:
        print("用法：")
        print("  python chain_map.py list              # 列出所有映射")
        print("  python chain_map.py map AMD           # 查AMD的A股映射")
        print("  python chain_map.py earnings 14       # 未来14天财报")
