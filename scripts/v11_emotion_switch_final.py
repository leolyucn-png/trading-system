#!/usr/bin/env python3
"""
v1.1 · 情绪开关终审
测试A: 指标2(溢价≥2%) AND 指标3(连板≥4)
测试B: 国证2000 > MA20
通过标准: ON基准中位>OFF基准中位 | 两年方向一致 | ON段数≥30 | ON占比15%-60%
"""
import os, sys, numpy as np, pandas as pd
from collections import defaultdict
sys.stdout.reconfigure(line_buffering=True)
CACHE_K = "cache_v06"

klines = {}
for f in os.listdir(CACHE_K):
    if f.endswith('.pkl'):
        df = pd.read_pickle(os.path.join(CACHE_K, f))
        if 'close' in df:
            code = f.replace('.pkl',''); 
            if code.startswith(('sh','sz')): code = code[2:]
            klines[code] = df.set_index('date')

def limit_up_factor(code): return 1.20 if code.zfill(6).startswith(('300','688')) else 1.10
def is_limit_up(code, prev, close):
    return abs(close - round(prev * limit_up_factor(code), 2)) < 0.005 if prev > 0 else False

dates = sorted(set(str(t.date()) for k in klines.values() for t in k.index if str(t.year) in ('2024','2025')))

# 涨停池
zt_pool = {}
for code, df in klines.items():
    for t in df.index:
        d = str(t.date()); idx = df.index.get_loc(t)
        if idx > 0 and is_limit_up(code, df['close'].iloc[idx-1], df['close'].iloc[idx]):
            if d not in zt_pool: zt_pool[d] = set()
            zt_pool[d].add(code)

# 连板高度
chain_height = {}
for d in dates:
    heights = []
    for code in zt_pool.get(d, set()):
        h = 1; di = dates.index(d)
        for j in range(1, 10):
            pd_ = dates[di-j] if di-j >= 0 else None
            if pd_ and pd_ in zt_pool and code in zt_pool[pd_]: h += 1
            else: break
        heights.append(h)
    chain_height[d] = max(heights) if heights else 0

# 溢价数据
premium_by_day = {}
for i in range(1, len(dates)):
    d, dy = dates[i], dates[i-1]
    yzt = zt_pool.get(dy, set())
    rets = []
    for code in yzt:
        df = klines.get(code)
        if df is None: continue
        t_ts = pd.Timestamp(d)
        if t_ts not in df.index: continue
        r = df['pct'].loc[t_ts]
        if not np.isnan(r): rets.append(r)
    premium_by_day[d] = np.mean(rets) if rets else 0

# 国证2000数据
idx = pd.read_csv('index_sz399303.csv')
idx['date'] = pd.to_datetime(idx['date'])
idx = idx.sort_values('date').set_index('date')
# 算MA20
idx['ma20'] = idx['close'].rolling(20).mean()
# 存成字典
index_above_ma20 = {}
for t, r in idx.iterrows():
    d = str(t.date())
    index_above_ma20[d] = r['close'] > r['ma20']

def run_test(label, is_on_func):
    """通用测试框架"""
    print(f"\n{'='*65}", flush=True)
    print(f"📊 {label}", flush=True)
    print(f"{'='*65}", flush=True)
    
    results = []
    for i in range(1, len(dates)-4):  # 需要i+3有效
        d = dates[i]
        if not is_on_func(d, i): continue
        t1, t3 = dates[i+1], dates[i+3]
        t1_ts, t3_ts = pd.Timestamp(t1), pd.Timestamp(t3)
        rets = []
        for code, df in klines.items():
            if t1_ts not in df.index or t3_ts not in df.index: continue
            # 排除一字板: T+1开盘涨停
            i1 = df.index.get_loc(t1_ts)
            if i1 > 0 and is_limit_up(code, df['close'].iloc[i1-1], df['close'].iloc[i1]): continue
            r = (df['close'].loc[t3_ts] / df['close'].loc[t1_ts] - 1) * 100
            if not np.isnan(r): rets.append(r)
        if rets:
            results.append({'date': d, 'bench_median': np.median(rets), 'bench_mean': np.mean(rets)})
    
    # 分年报告
    for yr in ['2024','2025']:
        yr_r = [r for r in results if r['date'].startswith(yr)]
        if not yr_r: continue
        # OFF基准(同年所有非ON日)
        off_benches = []
        for j in range(1, len(dates)-4):
            dj = dates[j]
            if dj.startswith(yr) and not is_on_func(dj, j):
                t1, t3 = dates[j+1], dates[j+3]
                t1_ts, t3_ts = pd.Timestamp(t1), pd.Timestamp(t3)
                rets = []
                for code, df in klines.items():
                    if t1_ts not in df.index or t3_ts not in df.index: continue
                    i1 = df.index.get_loc(t1_ts)
                    if i1 > 0 and is_limit_up(code, df['close'].iloc[i1-1], df['close'].iloc[i1]): continue
                    r = (df['close'].loc[t3_ts] / df['close'].loc[t1_ts] - 1) * 100
                    if not np.isnan(r): rets.append(r)
                if rets: off_benches.append(np.median(rets))
        
        on_m = np.mean([r['bench_median'] for r in yr_r])
        off_m = np.mean(off_benches) if off_benches else 0
        passed = on_m > off_m
        
        # 独立段数
        segs = 0; in_seg = False
        for d in dates:
            if not d.startswith(yr): continue
            di = dates.index(d)
            is_on = premium_by_day.get(d, 0) >= 2.0 and chain_height.get(d, 0) >= 4
            if '国证' in label:
                is_on = index_above_ma20.get(d, False)
            if 'AND' in label:
                is_on = (premium_by_day.get(d, 0) >= 2.0 and chain_height.get(d, 0) >= 4 
                         and index_above_ma20.get(d, False))
            if is_on:
                if not in_seg: segs += 1; in_seg = True
            else:
                in_seg = False
        on_pct = len(yr_r) / (len(yr_r) + len(off_benches)) * 100
        
        print(f"  {yr}: ON={len(yr_r)}天 OFF={len(off_benches)}天 | "
              f"ON基准中位{on_m:+.2f}% | OFF基准中位{off_m:+.2f}% | "
              f"差{on_m-off_m:+.2f}% {'✅' if passed else '❌'}", flush=True)
        print(f"    独立段数: {segs} | ON占比: {on_pct:.0f}%", flush=True)

# ==== 测试A: 指标2 AND 指标3 ====
def test_a(d, i):
    return premium_by_day.get(d, 0) >= 2.0 and chain_height.get(d, 0) >= 4

run_test("测试A: 溢价≥2% AND 连板≥4", test_a)

# ==== 测试B: 国证2000 > MA20 ====
def test_b(d, i):
    return index_above_ma20.get(d, False)

run_test("测试B: 国证2000 > MA20", test_b)

# ==== 测试A+B: 二者同时 ====
def test_ab(d, i):
    return test_a(d, i) and test_b(d, i)

run_test("测试A+B: 溢价≥2% AND 连板≥4 AND 国证>MA20", test_ab)

print(f"\n{'='*65}", flush=True)
print(f"🏁 情绪开关终审完成")
print(f"{'='*65}", flush=True)
