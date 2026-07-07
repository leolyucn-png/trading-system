#!/tmp/whisper_venv/bin/python3
"""
隔夜美股扫描 → 明日A股方向预判

每天早上05:30（美股04:00收盘后）自动运行。
输出：美股方向 + 中概股异动 + 明日A股影响板块 + 埋伏候选
"""

import json
import sys
import os

# Ensure we can import from whisper_venv
WHISPER_VENV = "/tmp/whisper_venv"
site_pkg = os.path.join(WHISPER_VENV, "lib", os.listdir(os.path.join(WHISPER_VENV, "lib"))[0], "site-packages")
if site_pkg not in sys.path:
    sys.path.insert(0, site_pkg)


def scan_us_market():
    """Scan US market close data for A-share prediction"""
    import yfinance as yf

    results = {}

    # US indices
    indices = {
        "^IXIC": "纳斯达克",
        "^GSPC": "标普500",
        "^DJI": "道琼斯",
    }
    results["indices"] = {}
    for sym, name in indices.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if len(h) >= 2:
                c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                pct = (c - p) / p * 100
                results["indices"][name] = {"price": round(c, 2), "change_pct": round(pct, 2)}
        except:
            pass

    # Key tech → A-share mapping
    tech_map = {
        "NVDA": ("英伟达", "算力/光模块"),
        "MRVL": ("迈威尔科技", "光通信/CPO"),
        "AMD": ("AMD", "芯片/半导体"),
        "AAPL": ("苹果", "消费电子"),
        "TSLA": ("特斯拉", "新能源车"),
        "QCOM": ("高通", "通信设备/手机链"),
        "MU": ("美光科技", "存储/半导体"),
        "AMZN": ("亚马逊", "云计算/AI"),
        "MSFT": ("微软", "AI/软件"),
        "GOOGL": ("谷歌", "AI/算力"),
    }
    results["tech"] = {}
    for sym, (name, sector) in tech_map.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if len(h) >= 2:
                c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                pct = (c - p) / p * 100
                results["tech"][name] = {
                    "symbol": sym, "price": round(c, 2),
                    "change_pct": round(pct, 2), "a_share_sector": sector
                }
        except:
            pass

    # China ADRs
    adr_map = {
        "BABA": ("阿里巴巴", "互联网/AI"),
        "JD": ("京东", "电商"),
        "BIDU": ("百度", "AI/自动驾驶"),
        "LI": ("理想汽车", "新能源车"),
        "NIO": ("蔚来", "新能源车"),
        "XPEV": ("小鹏", "新能源车"),
        "KWEB": ("中概互联ETF", "中概整体"),
        "FXI": ("中国大盘ETF", "中国整体"),
    }
    results["adr"] = {}
    for sym, (name, sector) in adr_map.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if len(h) >= 2:
                c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                pct = (c - p) / p * 100
                vol = h["Volume"].iloc[-1]
                results["adr"][name] = {
                    "symbol": sym, "price": round(c, 2),
                    "change_pct": round(pct, 2), "volume": int(vol)
                }
        except:
            pass

    return results


def generate_prediction(data):
    """Generate tomorrow's A-share prediction from US market data"""
    lines = []
    lines.append("🌙 昨夜美股复盘 → 明日A股预判")
    lines.append("")

    # Indices summary
    idx = data.get("indices", {})
    if idx:
        lines.append("📊 美股指数：")
        for name, v in idx.items():
            e = "🔴" if v["change_pct"] > 0 else ("🟢" if v["change_pct"] < 0 else "⚪")
            lines.append(f"  {e} {name}: {v['price']}（{v['change_pct']:+.2f}%）")

    lines.append("")

    # Key tech movers (>1.5%)
    tech = data.get("tech", {})
    movers = {k: v for k, v in tech.items() if abs(v["change_pct"]) > 1.5}
    if movers:
        lines.append("⚡ 科技龙头异动（>1.5%）：")
        for name, v in sorted(movers.items(), key=lambda x: abs(x[1]["change_pct"]), reverse=True):
            e = "🔴" if v["change_pct"] > 0 else ("🟢" if v["change_pct"] < 0 else "⚪")
            a_sector = v["a_share_sector"]
            direction = "利好" if v["change_pct"] > 0 else "利空"
            lines.append(f"  {e} {name} {v['change_pct']:+.2f}% → {a_sector} {direction}")

    lines.append("")

    # China ADR signals
    adr = data.get("adr", {})
    adr_movers = {k: v for k, v in adr.items() if abs(v["change_pct"]) > 2}
    if adr_movers:
        lines.append("🇨🇳 中概异动（>2%）：")
        for name, v in sorted(adr_movers.items(), key=lambda x: abs(x[1]["change_pct"]), reverse=True):
            e = "🔴" if v["change_pct"] > 0 else ("🟢" if v["change_pct"] < 0 else "⚪")
            lines.append(f"  {e} {name}: {v['change_pct']:+.2f}%")
    else:
        lines.append("🇨🇳 中概股：整体平稳")

    lines.append("")
    lines.append("=" * 40)
    lines.append("🎯 明日A股方向预判：")

    # Generate directional prediction
    positive_sectors = set()
    negative_sectors = set()
    for name, v in tech.items():
        if v["change_pct"] > 1:
            positive_sectors.add(v["a_share_sector"])
        elif v["change_pct"] < -1.5:
            negative_sectors.add(v["a_share_sector"])

    if positive_sectors:
        lines.append(f"  ✅ 偏强方向：{'、'.join(positive_sectors)}")
    if negative_sectors:
        lines.append(f"  ⚠️ 偏弱方向：{'、'.join(negative_sectors)}")

    return "\n".join(lines)


if __name__ == "__main__":
    data = scan_us_market()
    output = generate_prediction(data)
    print(output)
    print("\n" + "=" * 40)
    print(json.dumps(data, ensure_ascii=False, indent=2))
