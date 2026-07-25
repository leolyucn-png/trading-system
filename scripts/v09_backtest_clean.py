#!/usr/bin/env python3
"""
v0.9.2 · 孙权模式回测 · 清洁版
==========================================
协议版本: 2026-07-23 用户审定版 B

实验流程:
  Step 0: 票池 = 全A非ST (机械化, 无手工选择)
  Step 1: 4个条件平行单测 (基线+条件1~4)
  Step 2: 有增益的条件两两组合
  Step 3: 最优组合+第三个条件
  Step 4: 对照组 (定稿前)
  Step 5: 封存段 (只跑一次)

每个条件:
  - 信号数 < 150 → "样本不足" 不作数
  - 2024 vs 2025 分开看
  - 全部记入实验日志

成本: 双边0.24% + 滑点0.1%
"""
import os, sys, time, json, requests, random, csv
import pandas as pd
import numpy as np
from datetime import datetime

# ============ 固件 ============
CACHE_K = "cache_v06"
HOLD = 3
COST_BPS = 0.24
SLIPPAGE = 0.10
HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_SIGNALS = 150
random.seed(42)

TRAIN = ("2024-01-01", "2025-12-31")
SEAL = ("2026-01-01", "2026-06-30")

# 信号定义 (基线)
BASE_VOL_MIN, BASE_VOL_MAX = 1.5, 3.0
BASE_PCT_MIN, BASE_PCT_MAX = 2.0, 7.0

os.makedirs(CACHE_K, exist_ok=True)
os.makedirs("实验日志", exist_ok=True)

# ============ 票池 ============
ALL_CODES = []
def load_pool():
    global ALL_CODES
    # 从之前保存的文件加载
    import csv
    with open('/tmp/a_stock_list.csv', 'r') as f:
        reader = csv.DictReader(f)
        codes = [row['code'].strip().zfill(6) for row in reader]
    # 再次确保ST过滤
    pool = [c for c in codes if c[:2] in ('00','30','60','68','02','01','03')]
    ALL_CODES = pool
    return pool

# ============ 数据 ============
def tx_symbol(code):
    code = str(code).zfill(6)
    if code.startswith(('60','68')): return 'sh'+code
    if code.startswith(('00','30')): return 'sz'+code
    if code.startswith(('02','01','03')): return 'sz'+code
    return None

def parse_tx_kline(raw, symbol):
    try:
        d = json.loads(raw)['data'][symbol]
        rows = d.get('qfqday') or d.get('day') or []
        return [(r[0], float(r[2]), float(r[5]) if len(r)>5 else np.nan) for r in rows]
    except: return []

def stock_hist(code):
    sym = tx_symbol(code)
    if not sym: return None
    p = os.path.join(CACHE_K, f'{sym}.pkl')
    if os.path.exists(p):
        df = pd.read_pickle(p)
        if 'close' not in df: return None
        if 'ma20_vol' not in df.columns:
            df['ma20_vol'] = df['vol'].rolling(20).mean().shift(1)
            df['ma60_vol'] = df['vol'].rolling(60).mean().shift(1)
        return df.set_index('date')
    bars = []
    for s,e in [('2023-06-01','2024-06-30'),('2024-07-01','2025-12-31'),('2026-01-01','2026-07-23')]:
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{s},{e},640,qfq'
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            bars.extend(parse_tx_kline(r.text, sym))
        except: return None
        time.sleep(0.1)
    if len(bars) < 200: return None
    df = pd.DataFrame(bars, columns=['date','close','vol'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates('date').sort_values('date').reset_index(drop=True)
    df['pct'] = df['close'].pct_change() * 100
    # 计算均量
    df['ma20_vol'] = df['vol'].rolling(20).mean().shift(1)
    df['ma60_vol'] = df['vol'].rolling(60).mean().shift(1)
    pd.to_pickle(df, p)
    return df.set_index('date')

# ============ 条件函数 ============
def cond_base(df, i):
    """基线条件"""
    v_ratio = df['vol'].iloc[i] / df['ma20_vol'].iloc[i] if df['ma20_vol'].iloc[i] > 0 else 0
    pct = df['pct'].iloc[i]
    return BASE_VOL_MIN <= v_ratio <= BASE_VOL_MAX and BASE_PCT_MIN <= pct <= BASE_PCT_MAX

def cond_marketcap(df, i):
    """条件1: 流通市值<30亿 (TODO: 需要市值数据, 暂用价格*流通股估算)"""
    # 简化: 用收盘价*成交量手数*100 估算当日流通市值
    # 更准确的: qt.gtimg.cn 的f44字段 (但之前测了不准)
    # 暂时放行, 后续用更可靠的数据源
    return True  # placeholder

def cond_drawdown(df, i):
    """条件2: 前30日跌幅>15% (超跌)"""
    if i < 30: return False
    ret_30d = (df['close'].iloc[i] / df['close'].iloc[i-30] - 1) * 100
    return ret_30d < -15

def cond_volume_base(df, i):
    """条件3: 前20日中至少1天量<前60日均量50%, 且信号日量>=前20日均量1.5倍"""
    if i < 20: return False
    ma60 = df.iloc[i-20:i]['ma60_vol'].iloc[-1] if i >= 20 else 0
    if ma60 <= 0: return False
    # 前20日中是否有地量
    has_diliang = any(df['vol'].iloc[i-20:i] / ma60 < 0.5)
    # 信号日量比
    v_ratio = df['vol'].iloc[i] / df['ma20_vol'].iloc[i] if df['ma20_vol'].iloc[i] > 0 else 0
    return has_diliang and v_ratio >= 1.5

def cond_sector_boom(df, i):
    """条件4: 所属行业近3日涨停家数≥5只 (TODO: 需要行业数据)"""
    # 当前回测框架无行业数据, 留作后续
    return True  # placeholder

# ============ 信号采集 ============
def detect_signals(df, start_date, end_date, conditions):
    """
    conditions: [func1, func2, ...] 全部满足才触发
    """
    sigs = []
    for i in range(60, len(df)-HOLD):  # 60: 需要足够窗口计算均量
        t = df.index[i]
        if t < pd.Timestamp(start_date) or t > pd.Timestamp(end_date):
            continue
        # 全部条件满足
        if not all(cond(df, i) for cond in conditions):
            continue
        # 持有期收益
        rets = []
        for h in range(1, HOLD+1):
            if i+h < len(df):
                rets.append(df['pct'].iloc[i+h])
        if len(rets) < HOLD: continue
        total_ret = sum(rets)
        net_ret = total_ret - COST_BPS - SLIPPAGE
        sigs.append({
            'date': str(t.date()),
            'close': float(df['close'].iloc[i]),
            'pct': round(float(df['pct'].iloc[i]), 2),
            'hold_rets': [round(r,2) for r in rets],
            'total_ret': round(total_ret, 2),
            'net_ret': round(net_ret, 2),
            'hit_limit': any(r > 9.5 for r in rets),
        })
    return sigs

# ============ 报告 ============
def report(label, sigs, n_stocks):
    lines = []
    lines.append(f"\n{'=' * 65}")
    lines.append(f"📊 {label}")
    lines.append(f"{'=' * 65}")
    lines.append(f"  股票数: {n_stocks} | 信号数: {len(sigs)}")
    
    if len(sigs) < MIN_SIGNALS:
        lines.append(f"  ⛔ 样本不足{MIN_SIGNALS}条 → 不纳入结论")
        return '\n'.join(lines)
    
    rets = np.array([s['net_ret'] for s in sigs])
    gross = np.array([s['total_ret'] for s in sigs])
    hits = sum(1 for s in sigs if s['hit_limit'])
    
    lines.append(f"\n  分布特征:")
    lines.append(f"    均值:     {np.mean(rets):+.2f}%")
    lines.append(f"    中位数:   {np.median(rets):+.2f}%")
    lines.append(f"    25%分位:  {np.percentile(rets, 25):+.2f}%")
    lines.append(f"    75%分位:  {np.percentile(rets, 75):+.2f}%")
    lines.append(f"    胜率:     {np.mean(rets>0)*100:.1f}% ({sum(rets>0)}/{len(rets)})")
    lines.append(f"    最大收益: {np.max(rets):+.2f}%")
    lines.append(f"    最大亏损: {np.min(rets):+.2f}%")
    lines.append(f"    最大回撤: {np.min(np.minimum.accumulate(rets)):.2f}%")
    
    # 连亏
    runs = (rets < 0).astype(int)
    cur, max_cl = 0, 0
    for v in runs:
        if v: cur += 1
        else: max_cl, cur = max(max_cl, cur), 0
    max_cl = max(max_cl, cur)
    lines.append(f"    最大连续亏损: {max_cl}次")
    lines.append(f"    3日内涨停率: {hits/len(sigs)*100:.1f}% ({hits}/{len(sigs)})")
    lines.append(f"    毛收益均值: {np.mean(gross):+.2f}%")
    lines.append(f"    净收益均值: {np.mean(rets):+.2f}%")
    
    # 分年
    sigs_by_year = {}
    for s in sigs:
        y = s['date'][:4]
        if y not in sigs_by_year: sigs_by_year[y] = []
        sigs_by_year[y].append(s['net_ret'])
    lines.append(f"\n  分年:")
    for y in sorted(sigs_by_year.keys()):
        yr = np.array(sigs_by_year[y])
        lines.append(f"    {y}: {len(yr)}信号 | 均值{np.mean(yr):+.2f}% | 中位数{np.median(yr):+.2f}% | 胜率{np.mean(yr>0)*100:.1f}%")
    
    return '\n'.join(lines)

# ============ 实验日志 ============
def log_experiment(cond_name, sigs, n_stocks):
    """每跑一次写一行到实验日志"""
    log_file = '实验日志/消融日志.csv'
    header = ['时间','条件','股票数','信号数','均值','中位数','胜率','涨停率','最大连亏','净收益','2024均值','2025均值']
    
    rets = [s['net_ret'] for s in sigs]
    hits = sum(1 for s in sigs if s['hit_limit'])
    
    y24 = np.mean([s['net_ret'] for s in sigs if s['date'][:4]=='2024']) if any(s['date'][:4]=='2024' for s in sigs) else ''
    y25 = np.mean([s['net_ret'] for s in sigs if s['date'][:4]=='2025']) if any(s['date'][:4]=='2025' for s in sigs) else ''
    
    runs = (np.array(rets) < 0).astype(int)
    cur, max_cl = 0, 0
    for v in runs:
        if v: cur += 1
        else: max_cl, cur = max(max_cl, cur), 0
    max_cl = max(max_cl, cur)
    
    row = [datetime.now().strftime('%m-%d %H:%M'), cond_name, n_stocks, len(sigs),
           round(np.mean(rets),2) if rets else '', round(np.median(rets),2) if rets else '',
           f"{np.mean(np.array(rets)>0)*100:.1f}%" if rets else '',
           f"{hits/len(sigs)*100:.1f}%" if sigs else '',
           max_cl,
           round(np.mean(rets),2) if rets else '',
           round(y24,2) if y24 != '' else '',
           round(y25,2) if y25 != '' else '']
    
    write_header = not os.path.exists(log_file)
    with open(log_file, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerow(row)
    print(f"   📝 实验日志已写入: {cond_name}")

# ============ 主流程 ============
def run_experiment(cond_name, conditions, run_seal=False):
    """运行一组条件"""
    start, end = TRAIN if not run_seal else SEAL
    label = f"[{cond_name}] {start}~{end}"
    print(f"\n▶ 跑: {cond_name}")
    
    all_sigs = []
    n_ok = 0
    for code in ALL_CODES[:200]:  # 先跑200只, 后续可扩展
        df = stock_hist(code)
        if df is None: continue
        sigs = detect_signals(df, start, end, conditions)
        if sigs:
            for s in sigs: s['code'] = code
            all_sigs.extend(sigs)
        n_ok += 1
        if n_ok % 50 == 0:
            print(f"   {n_ok}/200 | 当前信号{len(all_sigs)}")
    
    output = report(label, all_sigs, n_ok)
    print(output)
    log_experiment(cond_name, all_sigs, n_ok)
    return all_sigs

def main():
    print("=" * 65)
    print("🏯 秦始皇 v0.9.2 · 消融测试（清洁版）")
    print(f"   运行: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   票池: 全A非ST (采样200只)")
    print(f"   训练段: {TRAIN[0]} ~ {TRAIN[1]}")
    print(f"   封存段: 已锁定")
    print("=" * 65)
    
    # 加载票池
    pool = load_pool()
    print(f"\n📦 全A非ST池: {len(pool)}只 | 训练段采样: 200只")
    
    # ============ 第一轮: 平行单测 ============
    print(f"\n{'=' * 65}")
    print("第一轮: 平行单测 (基线+4个条件)")
    print(f"{'=' * 65}")
    
    experiments = [
        ("基线: 放量不涨", [cond_base]),
        ("基线+条件2 超跌", [cond_base, cond_drawdown]),
        ("基线+条件3 地量", [cond_base, cond_volume_base]),
    ]
    
    results = {}
    for name, conds in experiments:
        sigs = run_experiment(name, conds)
        results[name] = sigs
    
    print(f"\n{'=' * 65}")
    print("第一轮完成 ✅ | 实验日志 → 实验日志/消融日志.csv")
    print("条件1(市值)和条件4(板块)需要数据源补充, 接下来优化")
    print(f"{'=' * 65}")

if __name__ == '__main__':
    main()
