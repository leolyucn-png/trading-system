#!/usr/bin/env python3
"""
v0.9.1 · 孙权模式回测 · 用户审定版
==========================================
回测协议（2026-07-23 用户审定）:

阶段一: 训练段 2024/1/1 ~ 2025/12/31
  → 所有条件调试、参数搜索随便试

阶段二: 封存段 2026/1/1 ~ 2026/6/30
  → 脚本定稿后只跑一次, 数字即为真实结果

阶段三: 前向记录
  → 每日收盘生成孙权信号并存档, 一个月后复盘

对照组: 每个信号配对1只同市值区间(±20%)的随机股
输出: 中位数 | 分位数 | 最大回撤 | 连亏 | 扣成本后
"""
import os, sys, time, json, requests, random
import pandas as pd
import numpy as np
from datetime import datetime

# ============ 配置 ============
CACHE_K = "cache_v06"
HOLD = 3
COST_BPS = 0.24    # 双边佣金+印花税%
SLIPPAGE = 0.10    # 滑点%
HEADERS = {"User-Agent": "Mozilla/5.0"}
random.seed(42)

# ============ 时段 ============
TRAIN_START, TRAIN_END = "2024-01-01", "2025-12-31"
SEAL_START, SEAL_END = "2026-01-01", "2026-06-30"

os.makedirs(CACHE_K, exist_ok=True)

# ============ 数据层 ============
def tx_symbol(code):
    code = str(code).zfill(6)
    if code.startswith(("60", "68")): return "sh" + code
    if code.startswith(("00", "30")): return "sz" + code
    return None

def parse_tx_kline(raw, symbol):
    try:
        d = json.loads(raw)["data"][symbol]
        rows = d.get("qfqday") or d.get("day") or []
        return [(r[0], float(r[2]), float(r[5]) if len(r) > 5 else np.nan) for r in rows]
    except: return []

def stock_hist(code, start, end):
    sym = tx_symbol(code)
    if not sym: return None
    p = os.path.join(CACHE_K, f"{sym}.pkl")
    if os.path.exists(p):
        df = pd.read_pickle(p)
        return df.set_index("date") if "close" in df else None
    bars = []
    chunks = [("2023-06-01","2024-06-30"), ("2024-07-01","2025-12-31"), ("2026-01-01","2026-07-23")]
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

# ============ 信号V1(原始基线) ============
VOL_MIN, VOL_MAX = 1.5, 3.0
PCT_MIN, PCT_MAX = 2.0, 7.0

def detect_signals(df, start_date, end_date):
    """在指定时段内检测信号"""
    vol = df["vol"]
    ma20 = vol.rolling(20).mean().shift(1)
    turn = df["close"] * vol * 100
    
    sigs = []
    for i in range(21, len(df)-HOLD):
        t = df.index[i]
        if t < pd.Timestamp(start_date) or t > pd.Timestamp(end_date):
            continue
        v_ratio = vol.iloc[i] / ma20.iloc[i] if ma20.iloc[i] > 0 else 0
        pct = df["pct"].iloc[i]
        if not (VOL_MIN <= v_ratio <= VOL_MAX and PCT_MIN <= pct <= PCT_MAX):
            continue
        rets = []
        for h in range(1, HOLD+1):
            if i+h < len(df):
                rets.append(df["pct"].iloc[i+h])
        if len(rets) < HOLD: continue
        total_ret = sum(rets)
        # 扣成本
        net_ret = total_ret - COST_BPS - SLIPPAGE
        sigs.append({
            "date": str(t.date()),
            "close": float(df["close"].iloc[i]),
            "vol_ratio": round(v_ratio, 2),
            "pct": round(pct, 2),
            "hold_rets": [round(r, 2) for r in rets],
            "total_ret": round(total_ret, 2),
            "net_ret": round(net_ret, 2),
            "hit_limit": any(r > 9.5 for r in rets),
        })
    return sigs

# ============ 样本池 ============
def sample_pool(n=200):
    pool = [
        "002197","605299","603221","002879","001258","000815",
        "002529","002369","002813","002888","002943","003008",
        "300095","300100","300105","300106","300107","300108",
        "300110","300111","300112","300113","300120","300121",
        "300122","300123","300124","300125","300126","300127",
        "300128","300129","300150","300151","300152","300153",
        "300154","300155","300156","300157","300158","300159",
        "002354","002355","002356","002357","002358","002359",
        "002360","002361","002362","002363","002364","002365",
        "002600","002601","002602","002603","002604","002605",
        "002606","002607","002608","002609","002610","002611",
        "002680","002681","002682","002683","002684","002685",
        "002686","002687","002688","002689","002690","002691",
        "605001","605002","605003","605005","605006","605007",
        "605008","605009","605010","605011","605100","605101",
        "605102","605103","605105","605106","605107","605108",
        "605111","605112","605113","605115","605116","605117",
        "605118","605119","605120","605121","605122","605123",
        "605125","605126","605127","605128","605129","605130",
        "605131","605132","605133","605135","605136","605137",
    ]
    random.shuffle(pool)
    return pool[:n]

# ============ 输出 ============
def report(label, sigs, n_stocks):
    print(f"\n{'=' * 65}")
    print(f"📊 {label}")
    print(f"{'=' * 65}")
    print(f"  股票数: {n_stocks} | 信号数: {len(sigs)}")
    if not sigs:
        print("  无信号")
        return
    
    rets = np.array([s["net_ret"] for s in sigs])
    hits = sum(1 for s in sigs if s["hit_limit"])
    
    print(f"\n  分布特征:")
    print(f"    均值:     {np.mean(rets):+.2f}%")
    print(f"    中位数:   {np.median(rets):+.2f}%")
    print(f"    25%分位:  {np.percentile(rets, 25):+.2f}%")
    print(f"    75%分位:  {np.percentile(rets, 75):+.2f}%")
    print(f"    胜率:     {np.mean(rets > 0)*100:.1f}% ({sum(rets>0)}/{len(rets)})")
    print(f"    最大收益: {np.max(rets):+.2f}%")
    print(f"    最大亏损: {np.min(rets):+.2f}%")
    print(f"    最大回撤: {np.min(np.minimum.accumulate(rets)):.2f}%")
    
    # 连亏
    runs = (rets < 0).astype(int)
    max_consec_loss = 0
    cur = 0
    for v in runs:
        if v: cur += 1
        else:
            max_consec_loss = max(max_consec_loss, cur)
            cur = 0
    max_consec_loss = max(max_consec_loss, cur)
    print(f"    最大连续亏损: {max_consec_loss}次")
    
    print(f"\n  涨停相关:")
    print(f"    3日内涨停率: {hits/len(sigs)*100:.1f}% ({hits}/{len(sigs)})")
    
    # 成本影响
    gross = np.mean([s["total_ret"] for s in sigs])
    net = np.mean(rets)
    print(f"\n  成本影响:")
    print(f"    毛收益均值: {gross:+.2f}%")
    print(f"    净收益均值: {net:+.2f}% (扣双边{COST_BPS}%+滑点{SLIPPAGE}%)")
    print(f"    成本吞噬:   {gross-net:.2f}%")

# ============ Main ============
def main():
    print("=" * 65)
    print("🏯 秦始皇 v0.9.1 · 孙权模式回测（用户审定版）")
    print(f"   运行: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)
    
    print("\n📋 回测协议:")
    print(f"  训练段: {TRAIN_START} ~ {TRAIN_END}")
    print(f"  封存段: {SEAL_START} ~ {SEAL_END}")
    print(f"  持有期: T+{HOLD}")
    print(f"  成本: 双边{COST_BPS}% + 滑点{SLIPPAGE}%")
    print(f"  信号V1基线: 量比{VOL_MIN}-{VOL_MAX}x + 涨幅{PCT_MIN}-{PCT_MAX}%")
    print()
    
    pool = sample_pool(150)
    print(f"📦 样本池: {len(pool)}只")
    
    # 训练段
    train_sigs = []
    n_ok = 0
    for code in pool:
        df = stock_hist(code, TRAIN_START, TRAIN_END)
        if df is None or len(df) < 200: continue
        sigs = detect_signals(df, TRAIN_START, TRAIN_END)
        if sigs:
            for s in sigs: s["code"] = code
            train_sigs.extend(sigs)
        n_ok += 1
        if n_ok % 30 == 0:
            print(f"  训练段: {n_ok}/{len(pool)}只 | 信号{len(train_sigs)}")
    
    report(f"🏋️ 训练段 {TRAIN_START}~{TRAIN_END}", train_sigs, n_ok)
    
    # 封存段
    print(f"\n\n{'🔒' * 10} 封存段以下为定稿后一次性执行 {'🔒' * 10}")
    print(f"\n{'=' * 65}")
    print(f"📦 阶段二: 封存段 {SEAL_START}~{SEAL_END}")
    print(f"{'=' * 65}")
    print("  ⛔ 定稿前禁止执行此段")
    print(f"  {'=' * 65}\n")

if __name__ == "__main__":
    main()
