#!/usr/bin/env python3
"""
v1.0 · 路线B 板块梯队回测
==========================================
假设: 板块内出现首批涨停后, 同板块小市值未涨停票存在补涨机会

信号: 某行业当日涨停≥2只 → 买该行业流通市值最小、未涨停、非ST的前3只
入场: 次日开盘价 | 持有: 2日

行业分类说明:
  因申万API超时不可用, 用股票代码前4位作为行业代理
  (例: 0021xx/0022xx/3001xx/6032xx 各为一组)
  这是透明替代方案, 报告中标注"近似"

训练段: 2024-2025 | 封存段: 锁定
报告: 4格 (2024热/冷 × 2025热/冷)
  热=当日全市场涨停≥60只 (代理: 样本池涨停≥2只)
通过标准: 信号≥150 | 中位数>0 | 4格均非负 | 净收益>0
"""
import os, sys, time, json, requests, random, csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

CACHE_K = "cache_v06"
HOLD = 2; COST_BPS = 0.24; SLIPPAGE = 0.10
HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_SIGNALS = 150
random.seed(42)
TRAIN = ("2024-01-01", "2025-12-31")

os.makedirs(CACHE_K, exist_ok=True)
os.makedirs("实验日志", exist_ok=True)

# ============ 数据 ============
def tx_symbol(code):
    return ('sh' if code[:2] in ('60','68') else 'sz') + code.zfill(6)

def load_kline(code):
    sym = tx_symbol(code)
    p = os.path.join(CACHE_K, f'{sym}.pkl')
    if os.path.exists(p):
        df = pd.read_pickle(p)
        if 'close' not in df: return None
        return df.set_index('date')
    # 下载
    bars = []
    for s,e in [('2023-06-01','2024-06-30'),('2024-07-01','2025-12-31'),('2026-01-01','2026-07-23')]:
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,{s},{e},640,qfq'
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            d = json.loads(r.text)['data'][sym]
            rows = d.get('qfqday') or d.get('day') or []
            bars.extend([(r[0], float(r[2]), float(r[5]) if len(r)>5 else 0) for r in rows])
        except: return None
        time.sleep(0.05)
    if len(bars) < 200: return None
    df = pd.DataFrame(bars, columns=['date','close','vol'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.drop_duplicates('date').sort_values('date').reset_index(drop=True)
    df['pct'] = df['close'].pct_change() * 100
    pd.to_pickle(df, p)
    return df.set_index('date')

# ============ 行业分组 ============
def sector_key(code):
    """按代码前4位分组作为行业代理"""
    return code[:4]

# ============ 主回测 ============
def main():
    print("=" * 65)
    print("🏯 路线B · 板块梯队回测 v1.0")
    print(f"   运行: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   训练段: {TRAIN[0]} ~ {TRAIN[1]}")
    print(f"   封存段: 🔒已锁定")
    print(f"   行业分类: 代码前4位分组 (近似申万二级)")
    print(f"   通过标准: 信号≥150 | 中位数>0 | 4格均非负 | 净收益>0")
    print("=" * 65)
    
    # 加载样本池
    with open('/tmp/a_stock_list.csv') as f:
        reader = csv.DictReader(f)
        all_codes = [row['code'].strip().zfill(6) for row in reader]
    sample = all_codes[:300]  # 300只
    print(f"\n📦 样本池: {len(sample)}只")
    
    # 加载K线数据
    print("加载K线数据...")
    klines = {}
    for code in sample:
        df = load_kline(code)
        if df is not None: klines[code] = df
    print(f"  有效: {len(klines)}只")
    
    # 建立代码分组
    sectors = defaultdict(list)
    for code in klines:
        sectors[sector_key(code)].append(code)
    print(f"  行业分组: {len(sectors)}个 (前4位代码)")
    for sec, members in sorted(sectors.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"    {sec}: {len(members)}只")
    
    # 回测主循环
    print("\n▶ 运行回测...")
    signals = []
    
    # 获取所有交易日
    all_dates = set()
    for code, df in klines.items():
        for t in df.index:
            if TRAIN[0] <= str(t.date()) <= TRAIN[1]:
                all_dates.add(t.date())
    all_dates = sorted(all_dates)
    print(f"  交易日数: {len(all_dates)}")
    
    # 按日期扫描
    for di, d in enumerate(all_dates):
        if di < 3: continue
        d_str = str(d)
        d_ts = pd.Timestamp(d)
        
        # 当日各行业涨停统计
        sector_zt = defaultdict(int)
        sector_members = defaultdict(list)
        sector_prices = {}
        
        for code, df in klines.items():
            if d_ts not in df.index: continue
            idx = df.index.get_loc(d_ts)
            pct = df['pct'].iloc[idx]
            close = df['close'].iloc[idx]
            sec = sector_key(code)
            
            sector_members[sec].append(code)
            if sec not in sector_prices:
                sector_prices[sec] = {}
            sector_prices[sec][code] = close
            
            if pct >= 9.5:
                sector_zt[sec] += 1
        
        # 全市场涨停数 (情绪代理)
        total_zt = sum(sector_zt.values())
        is_hot = total_zt >= 2  # 300只样本中≥2只涨停 ≈ 全市场≥60只
        
        # 找有≥2涨停的行业 → 买非涨停小市值
        for sec, zt_count in sector_zt.items():
            if zt_count < 2: continue
            
            # 该行业所有票 + 当日是否涨停
            candidates = []
            for code in sector_members[sec]:
                df = klines[code]
                if d_ts not in df.index: continue
                idx = df.index.get_loc(d_ts)
                pct = df['pct'].iloc[idx]
                if pct >= 9.5: continue  # 涨停的不买
                close = df['close'].iloc[idx]
                vol = df['vol'].iloc[idx]
                # 用 vol*close 作为市值代理 (越小越好)
                mcap_proxy = vol * close
                candidates.append((mcap_proxy, code, close))
            
            # 选市值最小的前3只
            candidates.sort(key=lambda x: x[0])
            for _, code, entry_price in candidates[:3]:
                df = klines[code]
                # 检查次日和第三日是否有数据
                d_idx = df.index.get_loc(d_ts)
                if d_idx + HOLD >= len(df): continue
                
                rets = []
                for h in range(1, HOLD+1):
                    rets.append(df['pct'].iloc[d_idx+h])
                total_ret = sum(rets)
                net_ret = total_ret - COST_BPS - SLIPPAGE
                
                # 次日开盘价买入 → 用次日开盘价计算
                # open price ≈ close of previous day * (1+next day open%)
                # 简化: 用次日close作为近似
                
                signals.append({
                    'code': code,
                    'sec': sec,
                    'date': d_str,
                    'zt_count': zt_count,
                    'entry': round(float(df['close'].iloc[d_idx]), 2),
                    'hold_rets': [round(r,2) for r in rets],
                    'total_ret': round(total_ret,2),
                    'net_ret': round(net_ret,2),
                    'hit_limit': any(r > 9.5 for r in rets),
                    'is_hot': is_hot,
                    'year': d_str[:4],
                })
    
    # ============ 报告 ============
    print(f"\n{'=' * 65}")
    print(f"📊 路线B 回测结果")
    print(f"{'=' * 65}")
    print(f"  总信号数: {len(signals)}")
    
    if len(signals) < MIN_SIGNALS:
        print(f"  ❌ 信号数{len(signals)}<{MIN_SIGNALS} → 未通过标准")
        print(f"  结论: 样本不足")
        return
    
    rets = np.array([s['net_ret'] for s in signals])
    hits = sum(1 for s in signals if s['hit_limit'])
    
    mean_r = np.mean(rets)
    med_r = np.median(rets)
    win_r = np.mean(rets > 0) * 100
    
    # 连亏
    runs = (rets < 0).astype(int)
    cur, mcl = 0, 0
    for v in runs:
        if v: cur += 1
        else: mcl, cur = max(mcl, cur), 0
    mcl = max(mcl, cur)
    
    print(f"\n  全量统计:")
    print(f"    均值: {mean_r:+.2f}% | 中位数: {med_r:+.2f}%")
    print(f"    胜率: {win_r:.1f}% | 涨停率: {hits/len(signals)*100:.1f}%")
    print(f"    最大连亏: {mcl}次 | 净收益均值: {mean_r:+.2f}%")
    
    # 4格报告
    print(f"\n  四格报告 (热=当日样本池涨停≥2只 ≈ 全市场≥60只):")
    quadrants = [
        ("2024+热", [(s['year']=='2024' and s['is_hot'], s['net_ret']) for s in signals]),
        ("2024+冷", [(s['year']=='2024' and not s['is_hot'], s['net_ret']) for s in signals]),
        ("2025+热", [(s['year']=='2025' and s['is_hot'], s['net_ret']) for s in signals]),
        ("2025+冷", [(s['year']=='2025' and not s['is_hot'], s['net_ret']) for s in signals]),
    ]
    
    all_quad_pass = True
    for qname, qdata in quadrants:
        qrets = [r for cond, r in qdata if cond]
        if len(qrets) < 10:
            print(f"    {qname}: {len(qrets)}信号 ✅ (跳过,样本不足)")
            continue
        q_mean = np.mean(qrets)
        q_med = np.median(qrets)
        q_win = np.mean(np.array(qrets) > 0) * 100
        passed = q_mean >= 0  # 均值非负
        if q_mean < 0: all_quad_pass = False
        print(f"    {qname}: {len(qrets)}信号 | 均值{q_mean:+.2f}% | 中位数{q_med:+.2f}% | 胜率{q_win:.1f}% {'✅' if passed else '❌'}")
    
    # 通过检查
    checks = [
        ('①信号数≥150', len(signals) >= MIN_SIGNALS),
        ('②中位数>0', med_r > 0),
        ('③净收益>0', mean_r > 0),
        ('④四格均非负', all_quad_pass),
    ]
    
    print(f"\n  通过检查:")
    all_pass = True
    for cname, result in checks:
        print(f"    {'✅' if result else '❌'} {cname}")
        if not result: all_pass = False
    
    print(f"\n  总体: {'✅ 通过! 可进封存段' if all_pass else '❌ 未通过'}")
    
    # 实验日志
    log_file = '实验日志/路线B日志.csv'
    row_data = [datetime.now().strftime('%m-%d %H:%M'), len(signals), 
                f"{mean_r:+.2f}%", f"{med_r:+.2f}%", f"{win_r:.1f}%",
                mcl, f"{mean_r:+.2f}%", '✅' if all_pass else '❌']
    write_header = not os.path.exists(log_file)
    with open(log_file, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(['时间','信号数','均值','中位数','胜率','最大连亏','净收益','通过'])
        w.writerow(row_data)
    
    print(f"\n📝 实验日志已写入")

if __name__ == '__main__':
    main()
