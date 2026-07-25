#!/usr/bin/env python3
"""
张飞 v2.0 — data_fetch 数据采集层
====================================
从AkShare拉取张飞计算所需的原始数据：
  - ETF日K线（20日分位用）
  - 指数日K线（大盘位置判断）
  - 板块涨跌/成交额（量价象限用）
  - 个股涨跌/成交额（个股持仓监控）

输出：原始DataFrame缓存供calc层消费

用法：python3 zhangfei_data_fetch.py
"""

import os, sys, json, datetime as dt
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "zhangfei_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ═══════════════════════════════════════════════
# 配置区（可调参数）
# ═══════════════════════════════════════════════
PERIOD_DAY = 20         # 分位计算周期
VOLUME_PERIOD = 20      # 均量计算周期
YEAR_MONTHS = 6        # 历史数据拉取跨度(月)

# ETF观察列表
ETF_WATCH = {
    "512480": "半导体ETF", "512400": "有色ETF", "516160": "新能源ETF",
    "515790": "光伏ETF", "512660": "军工ETF", "512800": "银行ETF",
    "512880": "证券ETF", "159819": "AI_ETF", "562500": "机器人ETF",
    "512010": "医药ETF", "159928": "消费ETF", "512690": "酒ETF",
    "515230": "软件ETF", "159865": "养殖ETF", "512170": "医疗ETF",
    "515880": "通信ETF",
}

# 指数观察列表
INDEX_WATCH = {
    "sh000001": "上证指数", "sh000688": "科创50",
    "sh000300": "沪深300", "sh399006": "创业板指",
}


def fetch_etf_data(force_refresh=False):
    """获取ETF日K线，用于20日分位+量价计算
    
    源1：优先从概率系统缓存加载（unpush2his被proxy屏蔽时的备选，日常也更快）
    源2：akshare fund_etf_hist_em（东财，需push2his可通）
"""
    cache = os.path.join(CACHE_DIR, "etf_data.pkl")
    prob_cache = os.path.join(SCRIPT_DIR, '..', 'memory', 'probability_trading', 'outputs')
    
    # 如果本地缓存够新，直接用
    if not force_refresh and os.path.exists(cache):
        df = pd.read_pickle(cache)
        last_date = df['date'].max()
        if last_date >= pd.Timestamp.now() - pd.Timedelta(days=3):
            print(f"  ✅ ETF数据(本地缓存): {last_date.date()}")
            return df
    
    # 优先从概率系统缓存加载（已存了78个交易日数据）
    etf_cache_files = [f for f in os.listdir(prob_cache) if f.startswith('etf_') and f.endswith('.pkl')]
    if etf_cache_files and not force_refresh:
        all_data = []
        for fname in etf_cache_files:
            fpath = os.path.join(prob_cache, fname)
            df = pd.read_pickle(fpath)
            code = fname.replace('etf_', '').replace('.pkl', '')
            # 找对应的ETF名称
            name = ETF_WATCH.get(code, f"ETF_{code}")
            df['code'] = code
            df['name'] = name
            df['date'] = pd.to_datetime(df['date']) if 'date' in df.columns else df['日期']
            df = df.rename(columns={
                '收盘': 'close', '成交量': 'volume', '成交额': 'amount',
                '涨跌幅': 'pct_chg', '换手率': 'turnover'
            })
            if 'close' not in df.columns:
                df['close'] = df.get('收盘', 0)
            if 'amount' not in df.columns:
                df['amount'] = df.get('成交额', 0)
            if 'pct_chg' not in df.columns:
                df['pct_chg'] = df.get('涨跌幅', 0)
            all_data.append(df)
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result.to_pickle(cache)
            print(f"  ✅ ETF数据(概率系统缓存): {len(result)}行")
            return result
    
    # 兜底：akshare直拉
    try:
        import akshare as ak
    except ImportError:
        print("  ❌ akshare 未安装")
        return None

    all_data = []
    start = (dt.date.today() - dt.timedelta(days=PERIOD_DAY * 3 + 10)).strftime("%Y%m%d")
    end = dt.date.today().strftime("%Y%m%d")

    for code, name in ETF_WATCH.items():
        try:
            df = ak.fund_etf_hist_em(symbol=code, period="daily",
                                      start_date=start, end_date=end, adjust="qfq")
            if df is None or len(df) < 2:
                continue
            df['code'] = code
            df['name'] = name
            df['date'] = pd.to_datetime(df['日期'])
            all_data.append(df[['date', 'code', 'name', '开盘', '收盘', '最高', '最低',
                                '成交量', '成交额', '涨跌幅', '换手率']].rename(columns={
                '收盘': 'close', '成交量': 'volume', '成交额': 'amount',
                '涨跌幅': 'pct_chg', '换手率': 'turnover'
            }))
        except Exception as e:
            print(f"  ⚠️ {name}({code}) 拉取失败: {str(e)[:50]}")
            continue

    if not all_data:
        print("  ❌ 全部ETF拉取失败")
        return None

    result = pd.concat(all_data, ignore_index=True)
    result.to_pickle(cache)
    print(f"  ✅ ETF数据(新拉): {len(result)}行")
    return result


def fetch_index_data(force_refresh=False):
    """获取指数日K线"""
    cache = os.path.join(CACHE_DIR, "index_data.pkl")
    if not force_refresh and os.path.exists(cache):
        df = pd.read_pickle(cache)
        last_date = df['date'].max()
        if last_date >= pd.Timestamp.now().normalize():
            return df

    try:
        import akshare as ak
    except ImportError:
        return None

    all_data = []
    for code, name in INDEX_WATCH.items():
        try:
            df = ak.stock_zh_index_daily(symbol=code)
            df['date'] = pd.to_datetime(df['date'])
            df = df[df['date'] >= pd.Timestamp.now() - pd.DateOffset(months=YEAR_MONTHS)]
            df['code'] = code
            df['name'] = name
            all_data.append(df[['date', 'code', 'name', 'open', 'close', 'high', 'low',
                                'volume']])
        except:
            continue

    if not all_data:
        return None
    result = pd.concat(all_data, ignore_index=True)
    result.to_pickle(cache)
    return result


def fetch_sector_flows():
    """获取当日板块资金流（实时）"""
    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
        if df is not None and len(df) > 0:
            return df
    except:
        pass
    return None


def run():
    print("=" * 60)
    print("🗡️ 张飞 data_fetch · 数据采集")
    print("=" * 60)
    etf = fetch_etf_data()
    idx = fetch_index_data()
    flows = fetch_sector_flows()
    print(f"  ETF: {len(etf) if etf is not None else 0}行")
    print(f"  指数: {len(idx) if idx is not None else 0}行")
    print(f"  资金流: {len(flows) if flows is not None else 0}行")
    return {"etf": etf, "index": idx, "flows": flows}


if __name__ == "__main__":
    run()
