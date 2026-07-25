# -*- coding: utf-8 -*-
"""
v0.8 · 旭光签名 · 历史大考(分析方交付)
==========================================
假设受审: "量价背离 + 筹码收缩(按公告日对齐)的标的,
          未来10个交易日相对全市场有超额收益"

信号定义(2026-07-15注册, 跑后不改):
  A. 量价背离: 当日成交量 >= 前20日均量×2, 且当日涨跌幅在±1%以内
  B. 筹码收缩: 信号日之前最近一期【已披露】(公告日<=信号日)的
     股东户数, 较其前一期下降>=10%
  C. 流动性: 当日成交额(收盘价×成交量近似) >= 5000万
  D. 非ST; 同一票10个交易日内重复信号只取首个
持有: 信号日收盘买入, 第10个交易日收盘卖出, 往返成本0.12%
对照: 全市场(评分宇宙)等权同窗口收益
时段: 2021-01 起至可结算终点
判读(注册): 逐年超额 >=80%年正→领证 / 约一半→开关型 / <40%→砍
           信号总数<50 → 判决C(样本不足)
声明: ①无历史流通市值数据, 500亿过滤不设(如实声明);
     ②股东户数来自东财(akshare stock_zh_a_gdhs_detail_em),
       严格按"公告日"对齐, 杜绝未来函数;
     ③成分为当前名单(幸存者偏差, 两组同受, 组间对比有效)。
用法: 与既有缓存同目录, 净化环境运行。首跑需拉全市场股东户数
     (~4000次东财请求, 预计1.5-2.5小时, cache_gdhs/断点续传)。
"""

import os
import time
import requests
import akshare as ak
import pandas as pd
import numpy as np
from typing import Optional

VOL_MULT = 2.0
PCT_BAND = 1.0
GDHS_DROP = -10.0          # 环比降幅阈值(%)
TURNOVER_FLOOR = 5e7       # 5000万
HOLD = 10
COST = 0.12
DEDUP_DAYS = 10
MIN_SIGNALS = 50
MAX_CONS = 100
CACHE_K = "cache_v06"      # 复用K线缓存(date/close/vol/pct)
CACHE_G = "cache_gdhs"
os.makedirs(CACHE_G, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}
YEARS_CHUNKS = [("2020-06-01", "2022-12-31"),
                ("2023-01-01", "2024-12-31"),
                ("2025-01-01", "2026-06-30")]


def tx_symbol(code: str) -> Optional[str]:
    code = str(code).zfill(6)
    if code.startswith(("60", "68")):
        return "sh" + code
    if code.startswith(("00", "30")):
        return "sz" + code
    return None


def parse_tx_kline(raw: str, symbol: str) -> list:
    import json
    try:
        d = json.loads(raw)["data"][symbol]
        rows = d.get("qfqday") or d.get("day") or []
        return [(r[0], float(r[2]), float(r[5]) if len(r) > 5 else np.nan)
                for r in rows]
    except Exception:
        return []


def stock_hist(code: str) -> Optional[pd.DataFrame]:
    sym = tx_symbol(code)
    if sym is None:
        return None
    p = os.path.join(CACHE_K, f"{sym}.pkl")
    if os.path.exists(p):
        df = pd.read_pickle(p)
        return df.set_index("date") if "close" in df else None
    bars = []
    for s, e in YEARS_CHUNKS:
        url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
               f"param={sym},day,{s},{e},640,qfq")
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            bars.extend(parse_tx_kline(r.text, sym))
        except requests.RequestException:
            return None
        time.sleep(0.2)
    if len(bars) < 150:
        return None
    df = pd.DataFrame(bars, columns=["date", "close", "vol"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df["pct"] = df["close"].pct_change() * 100
    pd.to_pickle(df, os.path.join(CACHE_K, f"{sym}.pkl"))
    return df.set_index("date")


def gdhs_events(code: str) -> Optional[pd.DataFrame]:
    """股东户数事件表: 公告日 -> 环比变化%。按公告日对齐, 无未来函数。"""
    p = os.path.join(CACHE_G, f"{code}.pkl")
    if os.path.exists(p):
        return pd.read_pickle(p)
    try:
        g = ak.stock_zh_a_gdhs_detail_em(symbol=str(code).zfill(6))
        time.sleep(0.6)
    except Exception:
        return None
    if g is None or g.empty:
        return None
    cols = {c: c for c in g.columns}
    date_col = next((c for c in g.columns if "公告日" in c or "公布" in c), None)
    cnt_col = next((c for c in g.columns if "股东户数" in c and "增减" not in c
                    and "本次" in c), None)
    if cnt_col is None:
        cnt_col = next((c for c in g.columns if c == "股东户数" or
                        ("股东户数" in c and "上次" not in c and "增减" not in c)), None)
    if date_col is None or cnt_col is None:
        return None
    ev = g[[date_col, cnt_col]].copy()
    ev.columns = ["ann_date", "cnt"]
    ev["ann_date"] = pd.to_datetime(ev["ann_date"], errors="coerce")
    ev["cnt"] = pd.to_numeric(ev["cnt"], errors="coerce")
    ev = ev.dropna().sort_values("ann_date").reset_index(drop=True)
    ev["chg_pct"] = ev["cnt"].pct_change() * 100      # 相对上一期
    ev = ev.dropna()
    pd.to_pickle(ev, p)
    return ev


def latest_disclosed_chg(ev: pd.DataFrame, t) -> Optional[float]:
    """信号日t之前(含)最近一期已披露的股东户数环比变化%。"""
    prior = ev[ev["ann_date"] <= t]
    if prior.empty:
        return None
    return float(prior["chg_pct"].iloc[-1])


def find_signals(s: pd.DataFrame, ev: pd.DataFrame) -> list:
    """s: 个股df(index=date, close/vol/pct)。返回信号日列表。纯函数。"""
    out, last_sig = [], None
    vol = s["vol"]
    ma20 = vol.rolling(20).mean().shift(1)            # 前20日均量, 不含当日
    turnover = s["close"] * vol * 100                 # 手→股近似
    for i in range(21, len(s)):
        t = s.index[i]
        if last_sig is not None and (i - last_sig) < DEDUP_DAYS:
            continue
        if np.isnan(ma20.iloc[i]) or ma20.iloc[i] <= 0:
            continue
        if vol.iloc[i] < VOL_MULT * ma20.iloc[i]:
            continue
        if abs(s["pct"].iloc[i]) > PCT_BAND:
            continue
        if turnover.iloc[i] < TURNOVER_FLOOR:
            continue
        chg = latest_disclosed_chg(ev, t)
        if chg is None or chg > GDHS_DROP:
            continue
        out.append(t)
        last_sig = i
    return out


def fwd_return(s: pd.DataFrame, t) -> Optional[float]:
    idx = s.index.get_loc(t)
    if idx + HOLD >= len(s):
        return None
    return (s["close"].iloc[idx + HOLD] / s["close"].iloc[idx] - 1) * 100 - COST


def main():
    secs = ak.stock_sector_spot(indicator="新浪行业")[["label", "板块"]].dropna()
    print(f"[数据] {len(secs)}板块 · K线缓存复用 · 股东户数按公告日对齐")

    universe, names = {}, {}
    for label, sname in secs.itertuples(index=False, name=None):
        cp = os.path.join(CACHE_K, f"cons_{label}.pkl")
        try:
            if os.path.exists(cp):
                cons = pd.read_pickle(cp)
            else:
                cd = ak.stock_sector_detail(sector=label)
                cons = list(zip(cd["code"].astype(str).str.zfill(6), cd["name"]))[:MAX_CONS]
                pd.to_pickle(cons, cp)
                time.sleep(1.0)
        except Exception as e:
            print(f"[fail] {sname}: {e}")
            continue
        for code, name in cons:
            if "ST" in str(name).upper() or code in universe:
                continue
            s = stock_hist(code)
            if s is not None:
                universe[code] = s
                names[code] = name
    print(f"[universe] {len(universe)}只")

    # 全市场等权前向收益基准(逐信号日现算, 先备市场矩阵)
    close_mat = pd.DataFrame({c: d["close"] for c, d in universe.items()})
    fwd_mkt = (close_mat.shift(-HOLD) / close_mat - 1) * 100 - COST

    records, done = [], 0
    for code, s in universe.items():
        ev = gdhs_events(code)
        done += 1
        if done % 200 == 0:
            print(f"  ...{done}/{len(universe)} 已处理, 信号累计{len(records)}")
        if ev is None or ev.empty:
            continue
        for t in find_signals(s, ev):
            r = fwd_return(s, t)
            if r is None:
                continue
            mkt = fwd_mkt.loc[t].mean() if t in fwd_mkt.index else np.nan
            if np.isnan(mkt):
                continue
            records.append({"t": t, "code": code, "name": names[code],
                            "ret": r, "mkt": mkt, "excess": r - mkt})

    T = pd.DataFrame(records)
    T.to_csv("v08_xuguang_signals.csv", index=False, encoding="utf-8-sig")
    print("\n" + "=" * 66)
    print(f"旭光签名 · 信号总数 {len(T)} · 持有{HOLD}日 vs 全市场等权")
    print("=" * 66)
    if T.empty:
        print("零信号。判决C: 样本不足。")
        return
    T["year"] = T["t"].dt.year
    pos = 0
    for y, g in T.groupby("year"):
        flag = "✅" if g["excess"].mean() > 0 else "❌"
        pos += int(g["excess"].mean() > 0)
        print(f"  {y}: 信号={len(g):>4}  组合均值{g['ret'].mean():+.2f}%"
              f"  超额均值{g['excess'].mean():+.3f}% {flag}")
    ny = T["year"].nunique()
    se = T["excess"].std(ddof=1) / np.sqrt(len(T)) if len(T) > 1 else float("nan")
    print("-" * 66)
    print(f"  总计: 超额均值 {T['excess'].mean():+.3f}% (±{1.96*se:.3f})"
          f"  为正年份 {pos}/{ny}  信号数 {len(T)}")
    if len(T) < MIN_SIGNALS:
        verdict = f"判决C: 信号{len(T)}<{MIN_SIGNALS}, 样本不足, 不下结论"
    elif pos / ny >= 0.8:
        verdict = "领证: 旭光签名成立, 进入宪法与小仓阶段"
    elif pos / ny >= 0.4:
        verdict = "开关型: 限定环境使用, 需配熔断"
    else:
        verdict = "砍: 旭光签名在本口径下不成立"
    print(f"  判读(对照注册标准): {verdict}")
    print("=" * 66)
    print("声明: 无历史市值数据,500亿过滤未设; 股东数据按公告日对齐;")
    print("      成分为当前名单(幸存者偏差,两组同受,组间对比有效)。")


if __name__ == "__main__":
    main()
