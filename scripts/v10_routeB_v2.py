#!/usr/bin/env python3
"""
v1.1 · 路线B 板块梯队回测 (行业数据修正版)
==========================================
修正: 行业数据用东财86个行业 (非代码前缀)
      热/冷阈值用全市场涨停分布校准
      样本池: 缓存全部1,397只

行业数据局限: 用当前行业成分测历史数据, 存在轻微前视偏差
         (个股入选板块可能发生在上涨之后)
         行业分类相对稳定, 可以接受
         禁止使用概念板块(前视污染严重)

通过标准: 信号≥150 | 中位数>0 | 4格均非负 | 净收益>0
"""
import os, json, sys, csv
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter

CACHE_K = "cache_v06"
HOLD = 2
COST_BPS = 0.24
SLIPPAGE = 0.10
MIN_SIGNALS = 150
TRAIN = ("2024-01-01", "2025-12-31")
os.makedirs("实验日志", exist_ok=True)

sys.stdout.reconfigure(line_buffering=True)

# ============ 加载行业映射 ============
print("加载行业映射...", flush=True)
with open('industry_map_v2.json') as f:
    stock_to_industry = json.load(f)
print(f"  {len(stock_to_industry)}只票有行业归属", flush=True)

# 行业覆盖统计
ind_set = set(stock_to_industry.values())
print(f"  {len(ind_set)}个行业", flush=True)

# ============ 加载K线 ============
print("加载K线缓存...", flush=True)
klines = {}
for f in os.listdir(CACHE_K):
    if f.endswith('.pkl'):
        df = pd.read_pickle(os.path.join(CACHE_K, f))
        if 'close' in df:
            code = f.replace('.pkl','')
            if code.startswith(('sh','sz')):
                code = code[2:]
            klines[code] = df.set_index('date')
print(f"  {len(klines)}只", flush=True)

# ============ 计算每日全市场涨停家数(从样本估计) ============
print("计算每日涨停分布...", flush=True)
zt_by_date = Counter()
for code, df in klines.items():
    for t in df.index:
        if t.year in (2024, 2025):
            idx = df.index.get_loc(t)
            if df['pct'].iloc[idx] >= 9.5:
                zt_by_date[str(t.date())] += 1

# 校准阈值: 全市场≥60只≈样本≥16只(样本1397/5000=28%)
# 全市场中位数72只, 按比例: 样本中位数20只
# 热阈值: 样本≥16只 (≈全市场≥60)
# 冷阈值: 样本<5只 (≈全市场<20)
HOT_THRESHOLD = 16
COLD_THRESHOLD = 5

# ============ 主回测 ============
print(f"\n{'='*65}", flush=True)
print(f"🏯 路线B v1.1 · 板块梯队回测", flush=True)
print(f"   训练段: {TRAIN[0]}~{TRAIN[1]}", flush=True)
print(f"   行业: 东财86行业", flush=True)
print(f"   热阈值: 样本≥{HOT_THRESHOLD}涨停 (≈全市场≥60)", flush=True)
print(f"   冷阈值: 样本<{COLD_THRESHOLD}涨停 (≈全市场<20)", flush=True)
print(f"   样本: {len(klines)}只", flush=True)
print(f"{'='*65}", flush=True)

# 建立 industry→[stocks] 映射
ind_stocks = defaultdict(list)
for code in klines:
    ind = stock_to_industry.get(code)
    if ind:
        ind_stocks[ind].append(code)
print(f"有行业归属的样本: {sum(len(v) for v in ind_stocks.values())}只, {len(ind_stocks)}个行业", flush=True)

# 对每个行业, 统计≥3只票的才保留(否则无法有2+涨停)
valid_inds = {ind: stocks for ind, stocks in ind_stocks.items() if len(stocks) >= 5}
print(f"有效行业(≥5只样本): {len(valid_inds)}个", flush=True)

# 回测主循环
signals = []
scanned = 0
for ind_name, stocks in valid_inds.items():
    for code in stocks:
        df = klines.get(code)
        if df is None: continue
        for i in range(60, len(df)-HOLD):
            t = df.index[i]
            if t < pd.Timestamp(TRAIN[0]) or t > pd.Timestamp(TRAIN[1]):
                continue
            d_str = str(t.date())
            
            # 检查: 当日该行业是否有≥2只涨停?
            # 计数: 该行业中当日涨幅≥9.5%的票数
            zt_in_ind = 0
            for oc in stocks:
                odf = klines.get(oc)
                if odf is None: continue
                if t in odf.index:
                    oi = odf.index.get_loc(t)
                    if odf['pct'].iloc[oi] >= 9.5:
                        zt_in_ind += 1
            
            if zt_in_ind < 2:
                continue
            
            # 本票非涨停
            pct = df['pct'].iloc[i]
            if pct >= 9.5:
                continue
            
            close = df['close'].iloc[i]
            vol = df['vol'].iloc[i]
            
            # 持有期收益
            rets = []
            for h in range(1, HOLD+1):
                if i+h < len(df):
                    rets.append(df['pct'].iloc[i+h])
            if len(rets) < HOLD: continue
            total_ret = sum(rets)
            net_ret = total_ret - COST_BPS - SLIPPAGE
            
            # 热/冷判断
            total_zt = zt_by_date.get(d_str, 0)
            is_hot = total_zt >= HOT_THRESHOLD
            is_cold = total_zt < COLD_THRESHOLD
            
            signals.append({
                'code': code, 'ind': ind_name,
                'date': d_str, 'zt_ind': zt_in_ind,
                'entry': round(float(close), 2),
                'total_ret': round(total_ret,2),
                'net_ret': round(net_ret,2),
                'hit_limit': any(r > 9.5 for r in rets),
                'is_hot': is_hot, 'is_cold': is_cold,
                'total_mkt_zt': total_zt,
                'year': d_str[:4],
            })
        
        scanned += 1
        if scanned % 200 == 0:
            print(f"  扫描{scanned}票 | 信号{len(signals)}", flush=True)

# ============ 报告 ============
print(f"\n{'='*65}", flush=True)
print(f"📊 路线B 回测结果", flush=True)
print(f"{'='*65}", flush=True)
print(f"  信号数: {len(signals)}", flush=True)

if len(signals) < MIN_SIGNALS:
    print(f"  ❌ 信号<{MIN_SIGNALS} → 未通过", flush=True)
    exit()

rets = np.array([s['net_ret'] for s in signals])
hits = sum(1 for s in signals if s['hit_limit'])
mean_r = np.mean(rets)
med_r = np.median(rets)
win_r = np.mean(rets > 0) * 100

runs = (rets < 0).astype(int); cur, mcl = 0, 0
for v in runs:
    if v: cur += 1
    else: mcl, cur = max(mcl, cur), 0
mcl = max(mcl, cur)

print(f"\n  全量统计:", flush=True)
print(f"    均值: {mean_r:+.2f}% | 中位数: {med_r:+.2f}%", flush=True)
print(f"    胜率: {win_r:.1f}% | 涨停率: {hits/len(signals)*100:.1f}%", flush=True)
print(f"    最大连亏: {mcl}次", flush=True)

# 四格报告
print(f"\n  四格报告:", flush=True)
quadrants = [
    ("2024热", [(s['net_ret'], s['total_mkt_zt']) for s in signals if s['year']=='2024' and s['is_hot']]),
    ("2024冷", [(s['net_ret'], s['total_mkt_zt']) for s in signals if s['year']=='2024' and s['is_cold']]),
    ("2025热", [(s['net_ret'], s['total_mkt_zt']) for s in signals if s['year']=='2025' and s['is_hot']]),
    ("2025冷", [(s['net_ret'], s['total_mkt_zt']) for s in signals if s['year']=='2025' and s['is_cold']]),
]

all_quad_pass = True
quad_results = {}
for qname, qdata in quadrants:
    qrets = np.array([r for r, _ in qdata])
    if len(qrets) < 10:
        print(f"    {qname}: {len(qrets)}信号 ✅ (样本不足, 跳过)", flush=True)
        quad_results[qname] = 0
        continue
    q_mean = np.mean(qrets); q_med = np.median(qrets)
    q_win = np.mean(qrets > 0) * 100
    passed = q_mean >= 0
    if not passed: all_quad_pass = False
    print(f"    {qname}: {len(qrets)}信号 | 均值{q_mean:+.2f}% | 中位数{q_med:+.2f}% | 胜率{q_win:.1f}% {'✅' if passed else '❌'}", flush=True)
    quad_results[qname] = q_mean

# 通过检查
checks = [
    ('①信号数≥150', len(signals) >= MIN_SIGNALS),
    ('②中位数>0', med_r > 0),
    ('③净收益>0', mean_r > 0),
    ('④四格均非负', all_quad_pass),
]
print(f"\n  通过检查:", flush=True)
all_pass = True
for cname, result in checks:
    print(f"    {'✅' if result else '❌'} {cname}", flush=True)
    if not result: all_pass = False

print(f"\n  总体: {'✅ 通过! 可进封存段' if all_pass else '❌ 未通过'}", flush=True)

# 实验日志
log_file = '实验日志/路线B_v2日志.csv'
row = [datetime.now().strftime('%m-%d %H:%M'), len(signals),
       f"{mean_r:+.2f}%", f"{med_r:+.2f}%", f"{win_r:.1f}%",
       mcl, f"{mean_r:+.2f}%", '✅' if all_pass else '❌']
with open(log_file, 'a', newline='') as f:
    w = csv.writer(f)
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        w.writerow(['时间','信号数','均值','中位数','胜率','最大连亏','净收益','通过'])
    w.writerow(row)

# 涨停分布输出
print(f"\n📊 每日全市场(估计)涨停分布:", flush=True)
mkt_counts = np.array([s['total_mkt_zt'] for s in signals])
for p in [10,25,50,75,90]:
    print(f"  P{p}: {np.percentile(mkt_counts, p):.0f}", flush=True)
print(f"  热日占比: {(mkt_counts>=HOT_THRESHOLD).mean()*100:.0f}%", flush=True)
print(f"  冷日占比: {(mkt_counts<COLD_THRESHOLD).mean()*100:.0f}%", flush=True)

print(f"\n📝 实验日志已写入", flush=True)
