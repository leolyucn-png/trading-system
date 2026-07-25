#!/usr/bin/env python3
"""
v0.9.3 · 孙权模式回测 · 终审轮
==========================================
协议: 2026-07-23 用户终审版

测试范围:
  单测: 条件1(市值), 条件4(板块), 条件5(情绪门控×3档)
  组合: 基线+条件1, 基线+条件4, 基线+条件5(×3档)
  最多再加一轮两两组合(如果前面有通过的)

通过标准(全部同时满足):
  ① 信号数 ≥ 150
  ② 中位数 > 0
  ③ 2024分年均值 > 0 且 2025分年均值 > 0
  ④ 扣成本(双边0.24%+滑点0.1%)后净收益 > 0

无一达标 → 结论"放量不涨信号证伪",项目归档
"""
import os, sys, time, json, requests, random, csv
import pandas as pd
import numpy as np
from datetime import datetime

CACHE_K = "cache_v06"
HOLD = 3; COST_BPS = 0.24; SLIPPAGE = 0.10
HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_SIGNALS = 150
random.seed(42)

TRAIN = ("2024-01-01", "2025-12-31")

# 基线参数
BASE_VOL_MIN, BASE_VOL_MAX = 1.5, 3.0
BASE_PCT_MIN, BASE_PCT_MAX = 2.0, 7.0

os.makedirs(CACHE_K, exist_ok=True)
os.makedirs("实验日志", exist_ok=True)

# ============ 票池 ============
def load_pool():
    import csv
    with open('/tmp/a_stock_list.csv', 'r') as f:
        reader = csv.DictReader(f)
        return [row['code'].strip().zfill(6) for row in reader]

ALL_CODES = load_pool()
print(f"📦 全A非ST池: {len(ALL_CODES)}只")

# ============ 数据 ============
def tx_symbol(code):
    return ('sh' if code[:2] in ('60','68') else 'sz') + code.zfill(6)

def stock_hist(code):
    """加载K线, 含20/60日均量"""
    sym = tx_symbol(code)
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
    df['ma20_vol'] = df['vol'].rolling(20).mean().shift(1)
    df['ma60_vol'] = df['vol'].rolling(60).mean().shift(1)
    pd.to_pickle(df, p)
    return df.set_index('date')

# ============ 条件函数 ============
def cond_base(df, i):
    vr = df['vol'].iloc[i] / df['ma20_vol'].iloc[i] if df['ma20_vol'].iloc[i] > 0 else 0
    p = df['pct'].iloc[i]
    return BASE_VOL_MIN <= vr <= BASE_VOL_MAX and BASE_PCT_MIN <= p <= BASE_PCT_MAX

# 条件1: 市值<30亿 (用当日gtimg, 近似)
_mcap_cache = {}
def cond_mcap(code, df, i):
    """流通市值 < 30亿 (近似: 当前市值, 非精确历史值)"""
    if code in _mcap_cache:
        cap = _mcap_cache[code]
    else:
        try:
            sym = tx_symbol(code)
            r = requests.get(f'http://qt.gtimg.cn/q={sym}', headers=HEADERS, timeout=5)
            f = r.text.split('~')
            cap = float(f[44]) if len(f) > 44 and f[44] else 999
            _mcap_cache[code] = cap
        except:
            cap = 999
    return cap < 30  # 30亿以下

# 条件4: 板块效应 — 所属行业近3日有涨停股
# 简化: 信号日当天, 样本池中同市值段(按前两位代码)涨停>=2只
_industry_zt = {}  # date+sector -> count
def cond_sector(code, df, i, all_stocks_data):
    """
    板块效应: 当日同行业有涨停
    简化定义: 信号日, 同一交易所板块(sz/sh)中至少3只涨停
    """
    t = str(df.index[i].date())
    exchange = 'sz' if code[:2] in ('00','30','02','01','03') else 'sh'
    key = f"{t}_{exchange}"
    
    if key not in _industry_zt:
        # 数当日该交易所涨停数(从已有的全量数据)
        zt_count = 0
        t_ts = pd.Timestamp(t)
        for c, d in all_stocks_data.items():
            if d is None or len(d) < 60: continue
            ex = 'sz' if c[:2] in ('00','30','02','01','03') else 'sh'
            if ex != exchange: continue
            if t_ts in d.index:
                idx = d.index.get_loc(t_ts)
                if d['pct'].iloc[idx] >= 9.5:
                    zt_count += 1
        _industry_zt[key] = zt_count
    return _industry_zt[key] >= 3

# 条件5: 情绪门控 — 全市场当日涨停家数 ≥ N
# 用样本池涨停率作为全市场情绪代理
_emotion_cache = {}
def cond_emotion(code, df, i, all_stocks_data, threshold_pct=0.05):
    """
    情绪门控: 当日样本池内涨停比例 ≥ threshold_pct
    threshold_pct: 涨停股数/总样本数
    N=30/50/80 → 在5000只里 = 0.6%/1%/1.6%
    对应200只样本: 1-3只涨停
    """
    t = str(df.index[i].date())
    if t in _emotion_cache:
        return _emotion_cache[t] >= threshold_pct
    
    t_ts = pd.Timestamp(t)
    zt_count = 0
    total = 0
    for c, d in all_stocks_data.items():
        if d is None: continue
        if t_ts in d.index:
            idx = d.index.get_loc(t_ts)
            if d['pct'].iloc[idx] >= 9.5:
                zt_count += 1
            total += 1
    
    ratio = zt_count / total if total > 0 else 0
    _emotion_cache[t] = ratio
    return ratio >= threshold_pct

# ============ 信号采集器 ============
def scan_signals(pool, conditions_fn):
    """
    高级信号采集器
    conditions_fn: func(code, df, i, all_data) -> bool
    """
    # 先加载所有股票数据
    all_data = {}
    n_loaded = 0
    for code in pool:
        df = stock_hist(code)
        if df is not None:
            all_data[code] = df
        n_loaded += 1
        if n_loaded % 50 == 0:
            print(f"  数据加载: {n_loaded}/{len(pool)}")
    
    sigs = []
    n_scanned = 0
    for code, df in all_data.items():
        for i in range(60, len(df)-HOLD):
            t = df.index[i]
            if t < pd.Timestamp(TRAIN[0]) or t > pd.Timestamp(TRAIN[1]):
                continue
            if not conditions_fn(code, df, i, all_data):
                continue
            rets = [df['pct'].iloc[i+h] for h in range(1, HOLD+1) if i+h < len(df)]
            if len(rets) < HOLD: continue
            total_ret = sum(rets); net_ret = total_ret - COST_BPS - SLIPPAGE
            sigs.append({
                'code': code, 'date': str(t.date()),
                'close': round(float(df['close'].iloc[i]), 2),
                'pct': round(float(df['pct'].iloc[i]), 2),
                'total_ret': round(total_ret,2), 'net_ret': round(net_ret,2),
                'hit_limit': any(r > 9.5 for r in rets),
            })
        n_scanned += 1
        if n_scanned % 30 == 0:
            print(f"  扫描: {n_scanned}/{len(all_data)} | 信号{len(sigs)}")
    
    return sigs, all_data

# ============ 条件工厂 ============
def make_cond_single(cond_name, cond_func):
    """生成单个条件的测试函数"""
    def fn(code, df, i, all_data):
        return cond_func(code, df, i, all_data)
    fn.__name__ = cond_name
    return fn

def make_cond_combo(cond_name, cond_func, base_check=cond_base):
    """生成基线+条件的测试函数"""
    def fn(code, df, i, all_data):
        return base_check(df, i) and cond_func(code, df, i, all_data)
    fn.__name__ = cond_name
    return fn

# ============ 报告 ============
def report(label, sigs, n_stocks):
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"📊 {label}")
    lines.append(f"{'='*60}")
    lines.append(f"  股票数: {n_stocks} | 信号数: {len(sigs)}")
    
    if len(sigs) < MIN_SIGNALS:
        lines.append(f"  ❌ 信号数{len(sigs)}<{MIN_SIGNALS} → 未通过")
        return '\n'.join(lines), False
    
    rets = np.array([s['net_ret'] for s in sigs])
    hits = sum(1 for s in sigs if s['hit_limit'])
    
    mean_r = np.mean(rets); med_r = np.median(rets)
    win_r = np.mean(rets>0)*100
    max_dd = np.min(np.minimum.accumulate(rets))
    # 连亏
    runs = (rets < 0).astype(int); cur, mcl = 0, 0
    for v in runs:
        if v: cur += 1
        else: mcl, cur = max(mcl, cur), 0
    mcl = max(mcl, cur)
    
    # 分年
    y24 = [s['net_ret'] for s in sigs if s['date'][:4]=='2024']
    y25 = [s['net_ret'] for s in sigs if s['date'][:4]=='2025']
    m24 = np.mean(y24) if y24 else 0
    m25 = np.mean(y25) if y25 else 0
    
    lines.append(f"\n  均值: {mean_r:+.2f}% | 中位数: {med_r:+.2f}%")
    lines.append(f"  胜率: {win_r:.1f}% | 涨停率: {hits/len(sigs)*100:.1f}%")
    lines.append(f"  最大回撤: {max_dd:.2f}% | 最大连亏: {mcl}次")
    lines.append(f"  2024年: {len(y24)}信号 | 均值{m24:+.2f}%")
    lines.append(f"  2025年: {len(y25)}信号 | 均值{m25:+.2f}%")
    lines.append(f"  净收益均值: {mean_r:+.2f}% (扣成本后)")
    
    # 通过检查
    checks = []
    checks.append(('①信号数≥150', len(sigs) >= 150))
    checks.append(('②中位数>0', med_r > 0))
    checks.append(('③2024均值>0', m24 > 0))
    checks.append(('③2025均值>0', m25 > 0))
    checks.append(('④净收益>0', mean_r > 0))
    
    all_pass = all(v for _, v in checks)
    lines.append(f"\n  通过检查:")
    for name, result in checks:
        lines.append(f"    {'✅' if result else '❌'} {name}")
    lines.append(f"  总体: {'✅ 通过! 可进封存段' if all_pass else '❌ 未通过'}")
    
    return '\n'.join(lines), all_pass

# ============ 实验日志 ============
def log_experiment(cond_name, sigs, n_stocks, passed):
    log_file = '实验日志/消融日志.csv'
    header = ['时间','条件','股票数','信号数','均值','中位数','胜率','涨停率',
              '最大连亏','净收益','2024均值','2025均值','通过']
    
    if not sigs:
        row = [datetime.now().strftime('%m-%d %H:%M'), cond_name, n_stocks, 0,
               '','','','','','','','','❌']
    else:
        rets = np.array([s['net_ret'] for s in sigs])
        hits = sum(1 for s in sigs if s['hit_limit'])
        y24 = np.mean([s['net_ret'] for s in sigs if s['date'][:4]=='2024']) or ''
        y25 = np.mean([s['net_ret'] for s in sigs if s['date'][:4]=='2025']) or ''
        runs = (rets < 0).astype(int); cur, mcl = 0, 0
        for v in runs:
            if v: cur += 1
            else: mcl, cur = max(mcl, cur), 0
        mcl = max(mcl, cur)
        
        row = [datetime.now().strftime('%m-%d %H:%M'), cond_name, n_stocks, len(sigs),
               f"{np.mean(rets):+.2f}%", f"{np.median(rets):+.2f}%",
               f"{np.mean(rets>0)*100:.1f}%", f"{hits/len(sigs)*100:.1f}%",
               mcl, f"{np.mean(rets):+.2f}%", 
               f"{y24:+.2f}%" if isinstance(y24, float) else y24,
               f"{y25:+.2f}%" if isinstance(y25, float) else y25,
               '✅' if passed else '❌']
    
    write_header = not os.path.exists(log_file)
    with open(log_file, 'a', newline='') as f:
        w = csv.writer(f)
        if write_header: w.writerow(header)
        w.writerow(row)

# ============ 主流程 ============
def main():
    print("=" * 60)
    print("🏯 秦始皇 v0.9.3 · 终审轮")
    print(f"   运行: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   训练段: {TRAIN[0]} ~ {TRAIN[1]}")
    print(f"   样本: 全A采样200只")
    print(f"   通过标准: 信号≥150 & 中位数>0 & 2024/2025均>0 & 净收益>0")
    print("=" * 60)
    
    pool = ALL_CODES[:200]
    
    # 先加载数据 (所有条件共享)
    print("\n📦 加载数据...")
    all_data = {}
    for code in pool:
        df = stock_hist(code)
        if df is not None: all_data[code] = df
    print(f"  有效股票: {len(all_data)}只")
    
    # 定义测试
    tests = []
    
    # 单测
    tests.append(("单测:条件1-市值<30亿", lambda c, d, i, a: cond_mcap(c, d, i)))
    tests.append(("单测:条件4-板块效应", lambda c, d, i, a: cond_sector(c, d, i, a)))
    for n_name, n_val in [("30涨停", 0.006), ("50涨停", 0.01), ("80涨停", 0.016)]:
        tests.append((f"单测:条件5-情绪{n_name}", 
                     lambda c, d, i, a, tv=n_val: cond_emotion(c, d, i, a, tv)))
    
    # 基线组合
    tests.append(("基线+条件1", lambda c, d, i, a: cond_base(d, i) and cond_mcap(c, d, i)))
    tests.append(("基线+条件4", lambda c, d, i, a: cond_base(d, i) and cond_sector(c, d, i, a)))
    for n_name, n_val in [("30涨停", 0.006), ("50涨停", 0.01), ("80涨停", 0.016)]:
        tests.append((f"基线+条件5-{n_name}",
                     lambda c, d, i, a, tv=n_val: cond_base(d, i) and cond_emotion(c, d, i, a, tv)))
    
    # 运行
    passed_any = False
    last_good_config = None
    for name, cond_fn in tests:
        print(f"\n▶ {name}")
        
        sigs = []
        for code, df in all_data.items():
            for i in range(60, len(df)-HOLD):
                t = df.index[i]
                if t < pd.Timestamp(TRAIN[0]) or t > pd.Timestamp(TRAIN[1]): continue
                if not cond_fn(code, df, i, all_data): continue
                rets = [df['pct'].iloc[i+h] for h in range(1, HOLD+1) if i+h < len(df)]
                if len(rets) < HOLD: continue
                total_ret = sum(rets); net_ret = total_ret - COST_BPS - SLIPPAGE
                sigs.append({
                    'code': code, 'date': str(t.date()),
                    'close': round(float(df['close'].iloc[i]), 2),
                    'pct': round(float(df['pct'].iloc[i]), 2),
                    'total_ret': round(total_ret,2), 'net_ret': round(net_ret,2),
                    'hit_limit': any(r > 9.5 for r in rets),
                })
        
        output, passed = report(name, sigs, len(all_data))
        print(output)
        log_experiment(name, sigs, len(all_data), passed)
        
        if passed:
            passed_any = True
            last_good_config = name
            print(f"\n  🏆 {name} 通过全部标准! 可进封存段")
    
    # 总结
    print(f"\n{'=' * 60}")
    if passed_any:
        print(f"🏆 有组合通过标准: {last_good_config}")
        print(f"   下一步: 定稿去封存段验证")
    else:
        print(f"❌ 无一组合通过全部4条标准")
        print(f"   结论: 放量不涨信号证伪")
        print(f"   项目归档 → 不再加新条件")
    print(f"{'=' * 60}")
    
    # 打印实验日志
    print(f"\n📝 实验日志: 实验日志/消融日志.csv")

if __name__ == '__main__':
    main()
