#!/tmp/stock_venv/bin/python3.14
"""
汉武帝计划 - 早盘扫描 2026-05-28 09:15
1. 大盘情绪/涨跌停数据
2. 完美世界(002624)实时行情
3. 行业资金流向 TOP5
4. 候选股扫描
"""

import akshare as ak
import pandas as pd
import sys
from datetime import datetime

print("=" * 60)
print("🦁 汉武帝早盘扫描 | 2026-05-28 09:15")
print("=" * 60)

# ============================================================
# 1. 大盘实时行情
# ============================================================
print("\n【1】📊 大盘指数行情")
try:
    df_index = ak.stock_zh_index_spot_em()
    watch_indices = ["上证指数", "深证成指", "创业板指", "科创50"]
    for _, row in df_index[df_index["名称"].isin(watch_indices)].iterrows():
        pct = row.get("涨跌幅", 0)
        emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
        print(f"  {emoji} {row['名称']}: {row['最新价']}  ({pct:+.2f}%)  成交额: {row.get('成交额', 0)}")
except Exception as e:
    print(f"  ⚠️ {e}")

# ============================================================
# 2. 涨跌停统计 (今日)
# ============================================================
print("\n【2】🌡️ 市场情绪")
try:
    now = datetime.now()
    today = now.strftime("%Y%m%d")
    df_zt = ak.stock_zt_pool_em(date=today)
    print(f"  今日涨停: {len(df_zt)} 家")
    # top 10 by 封板时间
    if len(df_zt) > 0:
        print(f"  最新涨停(前10):")
        for _, row in df_zt.head(10).iterrows():
            print(f"    ✅ {row.get('名称','?')}({row.get('代码','?')}) "
                  f"现价:{row.get('最新价','?')} 封板:{row.get('封板资金','?')}")
except Exception as e:
    print(f"  涨停数据: 集合竞价阶段暂未出数据 ({e})")

try:
    df_dt = ak.stock_zt_pool_dtgc_em(date=today)
    print(f"  今日跌停(实体跌幅): {len(df_dt)} 家")
except Exception as e:
    print(f"  跌停数据暂未出或接口限流 ({e})")

# ============================================================
# 3. 完美世界(002624) — 核心持仓监测
# ============================================================
print("\n【3】🎯 完美世界 002624")
try:
    df_spot = ak.stock_zh_a_spot_em()
    wanmei = df_spot[df_spot["代码"] == "002624"]
    if not wanmei.empty:
        r = wanmei.iloc[0]
        pct = r.get("涨跌幅", 0)
        vol_ratio = r.get("量比", 0)
        amount = r.get("成交额", 0)
        turnover = r.get("换手率", 0)
        high = r.get("最高", 0)
        low = r.get("最低", 0)
        emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
        print(f"  {emoji} 开盘/现价: {r.get('今开','?')} / {r.get('最新价','?')}")
        print(f"  昨收: {r.get('昨收','?')}")
        print(f"  涨跌幅: {pct:+.2f}%")
        print(f"  最高/最低: {high}/{low}")
        print(f"  成交额: {amount}  量比: {vol_ratio}  换手: {turnover}%")
        print(f"  总市值: {r.get('总市值','?')}")
    else:
        print("  ⚠️ 未获取到002624数据")
except Exception as e:
    print(f"  ⚠️ 接口错误: {e}")

# ============================================================
# 4. 行业资金流向 TOP5
# ============================================================
print("\n【4】💰 行业资金流向")
try:
    df_flow = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
    if df_flow is not None and len(df_flow) > 0:
        print(f"  今日行业净流入 TOP5:")
        df_sorted = df_flow.sort_values("主力净流入-净额", ascending=False)
        for _, row in df_sorted.head(5).iterrows():
            net = row.get("主力净流入-净额", 0)
            net_ratio = row.get("主力净流入-净占比", "")
            print(f"    💵 {row['名称']}: {net:.2f}亿  (净占比:{net_ratio})")
        print(f"  今日行业净流出 TOP3:")
        for _, row in df_sorted.tail(3).iterrows():
            net = row.get("主力净流入-净额", 0)
            print(f"    📉 {row['名称']}: {net:.2f}亿")
    else:
        print("  数据尚未更新")
except Exception as e:
    print(f"  ⚠️ {e}")

# ============================================================
# 5. 外网信号扫描 (快速轮询)
# ============================================================
print("\n【5】🔭 昨夜外网信号")
try:
    print("  * 美东5/27收盘数据正在获取...")
    # 美股三大指数
    print("  美股已收盘，非实时数据需查阅微博/快讯")
except Exception as e:
    print(f"  {e}")

# ============================================================
# 6. 完美世界昨日K线(5月最后几天)
# ============================================================
print("\n【6】📉 完美世界近5日K线")
try:
    df_hist = ak.stock_zh_a_hist(symbol="002624", period="daily",
                                  start_date="20260520", end_date="20260528",
                                  adjust="qfq")
    if df_hist is not None and len(df_hist) > 0:
        for _, row in df_hist.iterrows():
            pct = row["涨跌幅"]
            emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
            vol_str = f"{row['成交量']/10000:.0f}万" if row['成交量'] > 10000 else f"{row['成交量']:.0f}"
            print(f"  {emoji} {row['日期']} 开:{row['开盘']} 收:{row['收盘']} "
                  f"高:{row['最高']} 低:{row['最低']}  {pct:+.2f}% 量:{vol_str}")
    else:
        print("  无近5日数据")
except Exception as e:
    print(f"  ⚠️ {e}")

print("\n" + "=" * 60)
print("✅ 早盘扫描完成 | 等待09:25开盘价确认")
print("=" * 60)
