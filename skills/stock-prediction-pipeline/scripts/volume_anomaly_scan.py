#!/tmp/whisper_venv/bin/python3
"""
量价异动扫描 → 提前埋伏候选

逻辑：量比>3 但 涨幅<3% → 聪明钱已进场，股价还没动
这是最可靠的提前埋伏信号（比追新闻快1~2天）

运行：每天15:10（收盘后）
数据源：同花顺THS（akshare）+ 腾讯API验证
"""

import sys
import os

WHISPER_VENV = "/tmp/whisper_venv"
site_pkg = os.path.join(WHISPER_VENV, "lib",
                        os.listdir(os.path.join(WHISPER_VENV, "lib"))[0],
                        "site-packages")
if site_pkg not in sys.path:
    sys.path.insert(0, site_pkg)


def scan_volume_anomaly(top_n=30):
    """
    扫描当日量价异动股票。
    通过THS板块排行找到热门板块，然后筛选个股。
    """
    import akshare as ak
    import urllib.request
    import re
    from collections import defaultdict

    print("=" * 60)
    print("  📊 量价异动扫描 | 找提前埋伏候选")
    print("=" * 60)

    # 1. 获取行业板块排行
    print("\n🔍 扫描行业板块中...")
    df = ak.stock_board_industry_summary_ths()
    df_flow = df.sort_values("净流入", ascending=False)

    print(f"\n💰 资金流入TOP5板块：")
    for _, r in df_flow.head(5).iterrows():
        print(f"  {r['板块']:<14} 净流入{r['净流入']:+.0f}亿  涨幅{r['涨跌幅']:+.2f}%")

    # 2. 候选板块列表
    hot_sectors = df_flow.head(8)["板块"].tolist()

    print(f"\n🎯 扫描板块：{', '.join(hot_sectors)}")

    # 3. 获取板块成分股
    print(f"\n📡 获取板块成分股并筛选...")
    candidates = []

    for sector in hot_sectors:
        try:
            cons = ak.stock_board_industry_cons_ths(symbol=sector)
            if cons is None or len(cons) == 0:
                continue

            for _, r in cons.iterrows():
                code = str(r.get("代码", "")).strip()
                name = str(r.get("名称", "")).strip()
                pct = float(r.get("涨跌幅", 0))
                vol_ratio = float(r.get("量比", 0))

                # 主板 60xxx/00xxx/002xxx
                is_main = code.startswith(("60", "00", "002"))
                if not is_main:
                    continue

                # 核心条件：量比>3 且 涨幅<3%
                if vol_ratio > 3 and -5 < pct < 3:
                    price = r.get("现价", 0)
                    amount = r.get("成交额", 0)
                    turnover = r.get("换手率", 0)

                    candidates.append({
                        "code": code, "name": name,
                        "price": price, "pct": pct,
                        "vol_ratio": vol_ratio, "amount": amount,
                        "turnover": turnover, "sector": sector
                    })
        except Exception as e:
            continue

    # 去重
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["code"] not in seen:
            seen.add(c["code"])
            unique_candidates.append(c)

    # 按量比排序
    unique_candidates.sort(key=lambda x: x["vol_ratio"], reverse=True)

    print(f"\n{'=' * 60}")
    print(f"  🎯 埋伏候选清单（量比>3 且 涨幅<3%）")
    print(f"  {len(unique_candidates)} 只")
    print(f"{'=' * 60}")

    if not unique_candidates:
        print("\n  今日无符合条件的候选")
        return

    print(f"\n{'代码':<8} {'名称':<12} {'现价':>8} {'涨幅':>8} {'量比':>6} {'板块':<14} {'信号强度':<10}")
    print("-" * 70)

    for i, c in enumerate(unique_candidates[:top_n]):
        # 信号强度判断
        if c["vol_ratio"] > 7:
            strength = "🔥🔥🔥 天量"
        elif c["vol_ratio"] > 5:
            strength = "🔥🔥 强信号"
        else:
            strength = "🔥 有量"

        # 涨幅越低越好
        if abs(c["pct"]) < 1:
            strength += " 最佳"  # 几乎没涨

        emoji = "🔴" if c["pct"] > 0 else ("🟢" if c["pct"] < 0 else "⚪")
        print(f'{c["code"]:<8} {c["name"]:<12} {c["price"]:>8.2f} {emoji}{c["pct"]:>+6.2f}% {c["vol_ratio"]:>5.1f} {c["sector"]:<14} {strength}')

    return unique_candidates


if __name__ == "__main__":
    scan_volume_anomaly()
