"""
data_loader.py — 数据获取层

从 akshare + system memory 中拉取：
- 指数日K线（上证/科创50/沪深300）
- ETF板块日K线（半导体/有色/新能源/银行等）
- 板块主力资金流（近3个月）

所有数据缓存在 outputs/ 目录，避免重复拉取
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(CACHE_DIR, exist_ok=True)

# 核心跟踪的板块ETF列表
SECTOR_ETFS = {
    "半导体ETF": "512480",
    "有色ETF": "512400",
    "新能源ETF": "516160",
    "光伏ETF": "515790",
    "军工ETF": "512660",
    "银行ETF": "512800",
    "证券ETF": "512880",
    "AI_ETF": "159819",
    "通信ETF": "515880",
    "机器人ETF": "562500",
    "医药ETF": "512010",
    "消费ETF": "159928",
    "酒ETF": "512690",
    "软件ETF": "515230",
    "养殖ETF": "159865",
    "医疗ETF": "512170",
}


def load_index_daily(symbol="sh000001", name="上证指数", force_refresh=False):
    """获取指数日K线"""
    cache_file = os.path.join(CACHE_DIR, f"idx_{symbol}.pkl")

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df['name'] = name
        # 计算日涨跌幅
        df['pct_change'] = df['close'].pct_change() * 100
        # 计算量比（相对5日均量）
        df['volume_ma5'] = df['volume'].rolling(5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']

        with open(cache_file, "wb") as f:
            pickle.dump(df, f)
        print(f"  ✅ 已获取 {name} ({symbol}): {len(df)} 个交易日")
        return df
    except Exception as e:
        print(f"  ❌ {name} 获取失败: {e}")
        return None


def load_etf_daily(etf_code="512480", name="半导体ETF", force_refresh=False):
    """获取ETF日K线"""
    cache_file = os.path.join(CACHE_DIR, f"etf_{etf_code}.pkl")

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    try:
        import akshare as ak
        # 深交所ETF用 sz, 上交所ETF用 sh
        market = "sz" if etf_code.startswith("15") else "sh"
        df = ak.fund_etf_hist_em(symbol=etf_code, period="daily",
                                  start_date="20260401", end_date="20260725",
                                  adjust="qfq")
        df['date'] = pd.to_datetime(df['日期'])
        df = df.sort_values('date').reset_index(drop=True)
        df['name'] = name
        df['pct_change'] = df['收盘'].pct_change() * 100
        df['volume_ma5'] = df['成交量'].rolling(5).mean()
        df['volume_ratio'] = df['成交量'] / df['volume_ma5']

        with open(cache_file, "wb") as f:
            pickle.dump(df, f)
        print(f"  ✅ 已获取 {name} ({etf_code}): {len(df)} 个交易日")
        return df
    except Exception as e:
        print(f"  ❌ {name} 获取失败: {e}")
        return None


def load_all_sectors(force_refresh=False):
    """加载所有板块ETF数据"""
    print("\n📡 加载板块ETF数据...")
    result = {}
    for name, code in SECTOR_ETFS.items():
        df = load_etf_daily(code, name, force_refresh)
        if df is not None:
            result[name] = df
    print(f"  ✅ 成功加载 {len(result)}/{len(SECTOR_ETFS)} 个板块")
    return result


def load_all_indices(force_refresh=False):
    """加载所有指数"""
    print("\n📡 加载指数数据...")
    indices = {
        "sh000001": "上证指数",
        "sh000688": "科创50",
        "sh000300": "沪深300",
        "sh000016": "上证50",
        "sh399001": "深证成指",
        "sh399006": "创业板指",
    }
    result = {}
    for code, name in indices.items():
        df = load_index_daily(code, name, force_refresh)
        if df is not None:
            result[name] = df
    print(f"  ✅ 成功加载 {len(result)}/{len(indices)} 个指数")
    return result


def load_sector_flows(force_refresh=False):
    """
    加载板块资金流数据（近1个月可用）
    东财行业板块资金流
    """
    cache_file = os.path.join(CACHE_DIR, "sector_flows.pkl")

    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    try:
        import akshare as ak
        # 获取最近一次的数据（盘中可用，但历史不可回溯）
        # 改用 stock_sector_fund_flow_rank
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
        if df is not None and len(df) > 0:
            print(f"  ✅ 已获取行业资金流: {len(df)} 个行业")
            with open(cache_file, "wb") as f:
                pickle.dump(df, f)
            return df
    except Exception as e:
        print(f"  ❌ 资金流获取失败: {e}")
        return None


def get_market_breadth(date_str):
    """
    获取某日涨跌家数（大盘宽度数据）
    从系统内存中查询
    """
    # TODO: 从 memory 中的每日复盘提取
    # 暂时返回 None，后续从每日日志中提取
    return None


def prepare_backtest_data(indices=None, sectors=None):
    """
    准备回测用的统一数据集
    返回一个以日期为索引的DataFrame
    """
    if indices is None:
        indices = load_all_indices()
    if sectors is None:
        sectors = load_all_sectors()

    # 以沪深300为基准日期轴
    base = indices.get("沪深300")
    if base is None:
        base = indices.get("上证指数")
    if base is None:
        print("❌ 无基准指数")
        return None

    dates = base[['date']].copy()
    dates.set_index('date', inplace=True)

    # 添加指数列
    for name, df in indices.items():
        cols = df[['date', 'close', 'pct_change', 'volume', 'volume_ratio']].copy()
        cols.columns = ['date'] + [f"{name}_{c}" for c in ['close', 'pct', 'vol', 'vol_ratio']]
        cols.set_index('date', inplace=True)
        dates = dates.join(cols, how='left')

    # 添加板块ETF列
    for name, df in sectors.items():
        cols = df[['date', '收盘', 'pct_change', '成交量', 'volume_ratio']].copy()
        cols.columns = ['date'] + [f"{name}_{c}" for c in ['close', 'pct', 'vol', 'vol_ratio']]
        cols.set_index('date', inplace=True)
        dates = dates.join(cols, how='left')

    return dates.reset_index()


if __name__ == "__main__":
    print("=" * 60)
    print("📡 数据加载测试")
    print("=" * 60)
    indices = load_all_indices()
    sectors = load_all_sectors()
    data = prepare_backtest_data(indices, sectors)
    if data is not None:
        print(f"\n✅ 数据集: {len(data)} 行 × {len(data.columns)} 列")
        print(f"   日期范围: {data['date'].min().date()} → {data['date'].max().date()}")
        print(f"\n   最后5行关键列:")
        print(data[['date', '上证指数_close', '科创50_close', '半导体ETF_close']].tail(5).to_string())
