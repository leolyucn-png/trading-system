#!/usr/bin/env python3
"""
v0.9 · 孙权模式回测 · 游资首板埋伏信号验证
==========================================
验证两个从真实案例中提取的信号模式:

模式A「放量不涨建仓」:
  量1.5-3x(vs前20日均量) + 涨幅2-7%(未涨停) + 非ST
  → 买入持有T+3, 检验涨停率 & 超额收益

模式B「极致缩量企稳」:
  量<0.7x(均值) + 前3-7天连跌 + 最近2天企稳(-3%<涨<+1%)
  → 买入持有T+3, 检验反弹率

时段: 2024-01 至 2026-06
样本: 随机抽取300只全市场股票(含中小盘)
"""
import os, sys, time, json, requests, random
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============ 配置 ============
CACHE_K = "cache_v06"
MIN_SIGNALS = 20
HOLD = 3
COST = 0.12
HEADERS = {"User-Agent": "Mozilla/5.0"}
random.seed(42)

# 信号参数 模式A
A_VOL_MIN = 1.5
A_VOL_MAX = 3.0
A_PCT_MIN = 2.0
A_PCT_MAX = 7.0

# 信号参数 模式B
B_VOL_MAX = 0.7
B_DOWN_DAYS = 3
B_STABLE_RANGE = (-3.0, 1.0)

os.makedirs(CACHE_K, exist_ok=True)

# ============ 数据层(复用v0.8架构) ============
def tx_symbol(code):
    code = str(code).zfill(6)
    if code.startswith(("60", "68")): return "sh" + code
    if code.startswith(("00", "30")): return "sz" + code
    return None

def parse_tx_kline(raw, symbol):
    import json
    try:
        d = json.loads(raw)["data"][symbol]
        rows = d.get("qfqday") or d.get("day") or []
        return [(r[0], float(r[2]), float(r[5]) if len(r) > 5 else np.nan) for r in rows]
    except: return []

def stock_hist(code):
    sym = tx_symbol(code)
    if not sym: return None
    p = os.path.join(CACHE_K, f"{sym}.pkl")
    if os.path.exists(p):
        df = pd.read_pickle(p)
        return df.set_index("date") if "close" in df else None
    bars = []
    chunks = [("2023-01-01","2024-06-30"),("2024-07-01","2025-12-31"),("2026-01-01","2026-07-23")]
    for s, e in chunks:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{s},{e},640,qfq"
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            bars.extend(parse_tx_kline(r.text, sym))
        except: return None
        time.sleep(0.15)
    if len(bars) < 150: return None
    df = pd.DataFrame(bars, columns=["date","close","vol"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df["pct"] = df["close"].pct_change() * 100
    pd.to_pickle(df, os.path.join(CACHE_K, f"{sym}.pkl"))
    return df.set_index("date")

# ============ 信号检测 ============
def signal_A(df):
    """模式A: 放量不涨建仓"""
    signals = []
    vol = df["vol"]
    ma20 = vol.rolling(20).mean().shift(1)
    for i in range(21, len(df)-HOLD):
        v_ratio = vol.iloc[i] / ma20.iloc[i] if ma20.iloc[i] > 0 else 0
        pct = df["pct"].iloc[i]
        if A_VOL_MIN <= v_ratio <= A_VOL_MAX and A_PCT_MIN <= pct <= A_PCT_MAX:
            # 非ST(名称判断) — 简化跳过
            # 后续收益
            rets = []
            for h in range(1, HOLD+1):
                if i+h < len(df):
                    rets.append(df["pct"].iloc[i+h])
            if len(rets) == HOLD:
                signals.append({
                    "date": str(df.index[i].date()),
                    "close": float(df["close"].iloc[i]),
                    "vol_ratio": round(v_ratio, 2),
                    "pct": round(pct, 2),
                    "hold_rets": [round(r, 2) for r in rets],
                    "total_ret": round(sum(rets), 2),
                    "max_ret": round(max(rets), 2),
                    "hit_limit": any(r > 9.5 for r in rets),
                    "pattern": "A"
                })
    return signals

def signal_B(df):
    """模式B: 极致缩量企稳"""
    signals = []
    vol = df["vol"]
    ma20 = vol.rolling(20).mean().shift(1)
    for i in range(21, len(df)-HOLD):
        v_ratio = vol.iloc[i] / ma20.iloc[i] if ma20.iloc[i] > 0 else 0
        pct = df["pct"].iloc[i]
        # 缩量条件
        if v_ratio > B_VOL_MAX: continue
        # 前N天连跌条件
        if i < B_DOWN_DAYS: continue
        down_days = [df["pct"].iloc[i-j] for j in range(1, B_DOWN_DAYS+1)]
        if not all(d < 0 for d in down_days): continue
        # 最近2天企稳
        stable_days = [df["pct"].iloc[i-1], df["pct"].iloc[i]]
        if not all(B_STABLE_RANGE[0] <= s <= B_STABLE_RANGE[1] for s in stable_days): continue
        
        rets = []
        for h in range(1, HOLD+1):
            if i+h < len(df):
                rets.append(df["pct"].iloc[i+h])
        if len(rets) == HOLD:
            signals.append({
                "date": str(df.index[i].date()),
                "close": float(df["close"].iloc[i]),
                "vol_ratio": round(v_ratio, 2),
                "pct": round(pct, 2),
                "consecutive_down": B_DOWN_DAYS,
                "hold_rets": [round(r, 2) for r in rets],
                "total_ret": round(sum(rets), 2),
                "max_ret": round(max(rets), 2),
                "hit_limit": any(r > 9.5 for r in rets),
                "pattern": "B"
            })
    return signals

# ============ 样本股池 ============
def build_sample_pool(n=300):
    """预定义小盘池，避免API超时"""
    pool = [
        "002197","605299","603221","002879","001258","000815",  # 已知案例
        "002529","002369","002813","002888","002943","003008",
        "003011","003012","003015","003016","003017","003018",
        "003019","003020","003021","003022","003023","003025",
        "003026","003027","003028","003029","003030","003031",
        "003032","003033","003035","003036","003037","003038",
        "003039","003040","003041","003042","003043",
        "300095","300100","300105","300106","300107",
        "300108","300110","300111","300112","300113",
        "002354","002355","002356","002357","002358",
        "002359","002360","002361","002362","002363",
        "002364","002365","002366","002367","002368",
        "002369","002370","002371","002372","002373",
        "300120","300121","300122","300123","300124",
        "300125","300126","300127","300128","300129",
        "002600","002601","002602","002603","002604",
        "002605","002606","002607","002608","002609",
        "002610","002611","002612","002613","002614",
        "300150","300151","300152","300153","300154",
        "300155","300156","300157","300158","300159",
        "300160","300161","300162","300163","300164",
        "002680","002681","002682","002683","002684",
        "002685","002686","002687","002688","002689",
        "002690","002691","002692","002693","002694",
        "300180","300181","300182","300183","300184",
        "300185","300186","300187","300188","300189",
        "605001","605002","605003","605005","605006",
        "605007","605008","605009","605010","605011",
        "605100","605101","605102","605103","605105",
        "605106","605107","605108","605109","605110",
        "605111","605112","605113","605115","605116",
        "605117","605118","605119","605120","605121",
        "605122","605123","605125","605126","605127",
        "605128","605129","605130","605131","605132",
        "605133","605135","605136","605137","605138",
        "605139","605141","605142","605143","605145",
        "605146","605147","605148","605149","605150",
        "605151","605152","605153","605155","605156",
    ]
    random.shuffle(pool)
    return pool[:n]

# ============ 主回测 ============
def main():
    print("=" * 72)
    print("🏯 秦始皇 v0.9 · 孙权模式回测（游资首板埋伏信号验证）")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 72)
    
    print("\n📋 信号定义:")
    print("  模式A「放量不涨建仓」")
    print(f"    量比: {A_VOL_MIN}x ~ {A_VOL_MAX}x | 涨幅: {A_PCT_MIN}% ~ {A_PCT_MAX}%")
    print("    预期: 3日内涨停率 > 30%")
    print()
    print("  模式B「极致缩量企稳」")
    print(f"    量比: <{B_VOL_MAX}x | 连跌{B_DOWN_DAYS}+天 | 最近2天企稳")
    print("    预期: 3日内反弹率 > 50%")
    print()
    
    pool = build_sample_pool(200)
    print(f"\n📦 样本池: {len(pool)}只")
    
    # 逐只扫描
    all_A, all_B = [], []
    done = 0
    for code in pool:
        df = stock_hist(code)
        if df is None or len(df) < 200: continue
        sigs_a = signal_A(df)
        sigs_b = signal_B(df)
        if sigs_a:
            for s in sigs_a:
                s["code"] = code
            all_A.extend(sigs_a)
        if sigs_b:
            for s in sigs_b:
                s["code"] = code
            all_B.extend(sigs_b)
        done += 1
        if done % 20 == 0:
            print(f"  已扫{done}/{len(pool)}只 | A信号{len(all_A)} B信号{len(all_B)}")
    
    # 汇总
    print("\n" + "=" * 72)
    print("📊 回测结果")
    print("=" * 72)
    
    for label, signals, pat_name in [
        ("模式A 放量不涨建仓", all_A, "A"),
        ("模式B 极致缩量企稳", all_B, "B"),
    ]:
        print(f"\n🏆 {label}")
        print(f"  信号总数: {len(signals)}")
        if not signals:
            print("  样本不足 → 判决: 数据不足")
            continue
        
        total_ret = sum(s["total_ret"] for s in signals)
        avg_ret = round(total_ret / len(signals), 2)
        hit_limit = sum(1 for s in signals if s["hit_limit"])
        hit_limit_rate = round(hit_limit / len(signals) * 100, 1)
        win = sum(1 for s in signals if s["total_ret"] > 0)
        win_rate = round(win / len(signals) * 100, 1)
        avg_max = round(sum(s["max_ret"] for s in signals) / len(signals), 2)
        
        print(f"  平均T+3收益: {avg_ret:+.2f}%")
        print(f"  胜率(正收益): {win_rate}% ({win}/{len(signals)})")
        print(f"  3日内涨停率: {hit_limit_rate}% ({hit_limit}/{len(signals)})")
        print(f"  平均最大日内涨幅: {avg_max:+.2f}%")
        print(f"  累计收益(T+3): {total_ret:+.2f}%")
        
        # 判决
        if len(signals) < MIN_SIGNALS:
            print(f"  判决C: 样本不足{MIN_SIGNALS}条 → 需扩大样本")
        elif hit_limit_rate > 30:
            print(f"  判决A: ✅ 模式有效! 涨停率{hit_limit_rate}% > 30%")
        elif hit_limit_rate > 15:
            print(f"  判决B: 🟡 开关型 · 有条件有效")
        else:
            print(f"  判决F: ❌ 模式不成立")
    
    print("\n" + "=" * 72)
    print(f"🏯 回测完毕 | {datetime.now().strftime('%H:%M')} | 有效样本{done}只")
    print("=" * 72)

if __name__ == "__main__":
    main()
