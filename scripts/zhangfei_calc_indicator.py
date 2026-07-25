#!/usr/bin/env python3
"""
张飞 v2.0 — calc_indicator 核心计算层
========================================
输入：data_fetch拉取的原始数据
计算流程：【20日分位】→【量价四象限分类】→【情绪指标打分】
输出：结构化的判定结果供risk_watch消费

用法：python3 zhangfei_calc_indicator.py
"""

import os, sys, json, datetime as dt
import pandas as pd
import numpy as np

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "zhangfei_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "zhangfei_output")
os.makedirs(OUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════
# 配置区（可调参数）
# ═══════════════════════════════════════════════
POSITION_LOW = 30           # 低位上限(%)
POSITION_HIGH = 70          # 高位下限(%)
PERIOD_DAY = 20             # 分位计算周期
VOLUME_HIGH = 1.5           # 放量倍数
VOLUME_LOW = 0.7            # 缩量倍数
VOLUME_PERIOD = 20          # 均量计算周期
PRICE_FLAT_MAX = 1.0        # 滞涨判定上限(%)
PRICE_FLAT_MIN = -1.0       # 滞涨判定下限(%)
PRICE_PANIC = -2.0          # 放量大跌阈值(%)
LIMIT_UP_DAYS = 3           # 连板检测窗口
LIMIT_UP_COUNT = 2          # 涨停次数阈值
LIMIT_UP_THRESHOLD = 9.8    # 涨停判定涨幅(%)
EMOTION_OVERHEAT = -3       # 情绪过热阈值
EMOTION_PANIC = 3           # 情绪恐慌阈值


class NumpyEncoder(json.JSONEncoder):
    """支持NumPy类型的JSON序列化"""
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (np.bool_, np.integer)):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def calc_position_pct(series_close, period=PERIOD_DAY):
    """计算20日价格分位"""
    if len(series_close) < period:
        return None, None
    recent = series_close.tail(period)
    low = recent.min()
    high = recent.max()
    if high == low:
        return 50.0, "中段"
    current = recent.iloc[-1]
    pct = (current - low) / (high - low) * 100
    if pct <= POSITION_LOW:
        zone = "低位"
    elif pct >= POSITION_HIGH:
        zone = "高位"
    else:
        zone = "中段"
    return round(pct, 1), zone


def calc_volume_ma(series_volume, period=VOLUME_PERIOD):
    """计算均量"""
    if len(series_volume) < period:
        return None, None, None
    ma = series_volume.tail(period).mean()
    current = series_volume.iloc[-1]
    if ma == 0:
        return None, None, None
    ratio = current / ma
    if ratio >= VOLUME_HIGH:
        vol_zone = "放量"
    elif ratio <= VOLUME_LOW:
        vol_zone = "缩量"
    else:
        vol_zone = "平量"
    return round(ratio, 2), vol_zone, ma


def classify_quadrant(pct_change, vol_zone):
    """量价四象限分类"""
    if vol_zone == "放量":
        if pct_change >= 2.0:
            return "Ⅴ放量大跌", "🔴"  # 独立条目
        elif pct_change > 0:
            return "Ⅰ放量上涨", "🟢"
        elif pct_change >= PRICE_FLAT_MIN:
            return "Ⅱ放量滞涨", "🟡"
        else:
            return "Ⅴ放量大跌", "🔴"
    elif vol_zone == "缩量":
        if pct_change > 0:
            return "Ⅲ缩量上涨", "🟢"
        else:
            return "Ⅳ缩量下跌", "🔴"
    else:
        if pct_change > 0:
            return "平量上涨", "🟢"
        else:
            return "平量下跌", "🔴"


def check_limit_up(stock_df, days=LIMIT_UP_DAYS, threshold=LIMIT_UP_THRESHOLD):
    """检测近期是否有多连板"""
    recent = stock_df.tail(days)
    pct_col = _get_col(recent, ['pct_chg', '涨跌幅', '涨跌额'])
    if isinstance(pct_col, pd.Series):
        limit_count = (pct_col >= threshold).sum()
    else:
        limit_count = 0
    return limit_count >= LIMIT_UP_COUNT


def _get_col(df, names, default=0):
    """兼容不同数据源的列名（支持DataFrame和Series）"""
    if hasattr(df, 'columns'):
        # DataFrame
        for n in names:
            if n in df.columns:
                return df[n]
    elif hasattr(df, 'index'):
        # Series (单行)
        for n in names:
            if n in df.index:
                return df[n]
    return default

def calc_one_etf(etf_df):
    """计算单只ETF的所有指标"""
    if len(etf_df) < max(PERIOD_DAY, VOLUME_PERIOD):
        return None

    close = _get_col(etf_df, ['close', '收盘', 'CLOSE'])
    volume = _get_col(etf_df, ['amount', '成交额', 'volume', '成交量'])
    if isinstance(volume, pd.Series):
        volume = volume.fillna(0) if volume.dtype.kind in 'if' else volume

    # 1. 分位
    pct, zone = calc_position_pct(close)

    # 2. 量
    vol_ratio, vol_zone, vol_ma = calc_volume_ma(volume)

    # 3. 当日涨跌
    latest = etf_df.iloc[-1]
    chg = float(_get_col(latest, ['pct_chg', '涨跌幅', '涨跌额', 'pct_change'], 0))

    # 4. 量价象限
    quad, quad_color = classify_quadrant(chg, vol_zone)

    # 5. 连板检测
    pct_col = _get_col(etf_df, ['pct_chg', '涨跌幅', '涨跌额', 'pct_change'])
    if isinstance(pct_col, pd.Series):
        pct_df = etf_df.copy()
        pct_df['涨跌幅'] = pct_col
        is_limit_up = check_limit_up(pct_df)
    else:
        is_limit_up = False

    close_val = float(_get_col(latest, ['close', '收盘', 0]))
    vol_val = float(_get_col(latest, ['amount', '成交额', 'volume', '成交量'], 0))

    date_val = latest.get('date') or latest.get('日期', '')
    if hasattr(date_val, 'strftime'):
        date_str = date_val.strftime('%Y-%m-%d')
    else:
        date_str = str(date_val)[:10]

    return {
        "position_pct": pct,
        "zone": zone,
        "vol_ratio": vol_ratio,
        "vol_zone": vol_zone,
        "pct_change": round(chg, 2),
        "quadrant": quad,
        "quadrant_color": quad_color,
        "close": round(close_val, 3) if close_val != 0 else 0,
        "volume": float(vol_val),
        "is_limit_up": is_limit_up,
        "date": date_str,
    }


# ═══════════════════════════════════════════════
# 情绪指标计算（简化版，无需实时数据也能跑）
# ═══════════════════════════════════════════════
EMOTION_TAGS = {
    "散户热度": {"score": 0, "weight": 2, "tag": "normal"},
    "龙虎榜散户": {"score": 0, "weight": 2, "tag": "normal"},
    "融资余额": {"score": 0, "weight": 1, "tag": "normal"},
    "涨停密度": {"score": 0, "weight": 1, "tag": "normal"},
    "量比异常": {"score": 0, "weight": 1, "tag": "normal"},
}


def calc_emotion_score(sector_df=None, stock_df=None):
    """
    计算情绪总分（实时数据可选，无数据时返回0）
    """
    score = 0
    details = {}

    # 涨停密度（板块内涨停占比）
    if sector_df is not None and len(sector_df) > 0:
        try:
            zt_count = (sector_df['涨跌幅'] >= LIMIT_UP_THRESHOLD).sum()
            zt_density = zt_count / len(sector_df) * 100
            if zt_density > 10:
                score -= 1
                details["涨停密度"] = -1
            else:
                details["涨停密度"] = 0
        except:
            details["涨停密度"] = 0

    return score, details


def run(etf_data=None):
    """主计算入口"""
    if etf_data is None:
        cache = os.path.join(CACHE_DIR, "etf_data.pkl")
        if not os.path.exists(cache):
            print("❌ 无数据，请先运行 zhangfei_data_fetch.py")
            return
        etf_data = pd.read_pickle(cache)

    print("=" * 60)
    print("🗡️ 张飞 calc_indicator · 核心计算")
    print("=" * 60)

    results = []
    for code in etf_data['code'].unique():
        one = etf_data[etf_data['code'] == code].sort_values('date').reset_index(drop=True)
        name = one['name'].iloc[0]
        r = calc_one_etf(one)
        if r is None:
            continue

        # 连板豁免 (ETF没有涨停一说，但个股数据进来说明机制)
        if r['is_limit_up']:
            r['zone'] = "中段"

        # 情绪计算（无板块明细时跳过）
        emo_score, emo_detail = calc_emotion_score()
        r['emotion_score'] = emo_score
        r['emotion_detail'] = emo_detail

        # 风险等级判定
        r['risk_level'], r['risk_note'] = judge_risk(r)

        results.append({"code": code, "name": name, **r})

    # 按风险排序
    risk_order = {"🔴": 0, "🟡": 1, "🟢": 2}
    results.sort(key=lambda x: (risk_order.get(x['risk_level'], 9), -x['position_pct']))

    for r in results:
        emoji = r['quadrant_color']
        print(f"  {r['risk_level']} {r['name']:<10} 分位{r['position_pct']:>5.1f}% "
              f"[{r['zone']}]  {emoji} {r['quadrant']:<8}  "
              f"{r['pct_change']:+.2f}% 量{r['vol_ratio']}")

    # 输出分类汇总
    high_risk = [r for r in results if r['risk_level'] == "🔴"]
    low_opp = [r for r in results if r['risk_level'] == "🟢" and r['zone'] == "低位"]
    mid = [r for r in results if r['zone'] == "中段"]

    summary = {
        "高位预警": [r['name'] for r in high_risk],
        "低位机会": [r['name'] for r in low_opp],
        "中段观察": [r['name'] for r in mid],
        "禁止新开仓": len(high_risk) > 0,
        "减仓提示": len([r for r in results if r.get('quadrant') in ("Ⅱ放量滞涨", "Ⅳ缩量下跌", "Ⅴ放量大跌")
                           and r['zone'] == "高位"]) > 0,
    }

    print(f"\n📋 汇总:")
    print(f"  高位预警: {summary['高位预警']}")
    print(f"  低位机会: {summary['低位机会']}")
    print(f"  中段观察: {len(summary['中段观察'])}只")
    print(f"  禁止新开仓: {'是' if summary['禁止新开仓'] else '否'}")

    output = {
        "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "results": results,
        "summary": summary,
    }
    with open(os.path.join(OUT_DIR, "zhangfei_calc_result.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    print(f"\n💾 已保存: zhangfei_calc_result.json")

    return results, summary


def judge_risk(r):
    """
    分层风险判定
    返回 (risk_level, note)
    """
    zone = r['zone']
    quad = r['quadrant']
    emo = r['emotion_score']

    # === 高位区 ===
    if zone == "高位":
        if r['is_limit_up']:
            return "🟡", "连板豁免-走中段规则"

        if quad == "Ⅱ放量滞涨":
            if emo <= EMOTION_OVERHEAT:
                return "🔴", "高位放量滞涨+情绪过热→出货预警"
            return "🔴", "高位放量滞涨→出货预警"

        if quad == "Ⅰ放量上涨":
            if emo <= EMOTION_OVERHEAT:
                return "🔴", "高位放量上涨+情绪过热→加速赶顶"
            return "🟡", "高位放量上涨→观察"

        if quad == "Ⅳ缩量下跌":
            return "🔴", "高位缩量下跌→趋势转弱"

        if quad == "Ⅴ放量大跌":
            return "🔴", "高位放量大跌→踩踏出逃"

        return "🟡", "高位正常波动→观察"

    # === 低位区 ===
    if zone == "低位":
        if quad in ("Ⅰ放量上涨", "Ⅲ缩量上涨"):
            if emo >= EMOTION_PANIC:
                return "🟢", "低位放量启动+情绪恐慌→买入机会"
            return "🟢", "低位放量启动→关注候选池"

        if quad == "Ⅴ放量大跌":
            return "🔴", "低位放量大跌→回避,等缩量企稳"

        if quad == "Ⅳ缩量下跌":
            return "🟡", "低位缩量阴跌→观望"

        return "🟡", "低位观察"

    # === 中段区 ===
    return "🟢", "中段正常→不拦截"


if __name__ == "__main__":
    run()
