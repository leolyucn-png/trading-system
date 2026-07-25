#!/usr/bin/env python3
"""
双模式选股 · 每日盘后扫描 v1.0
================================
模式1: 底部反转埋伏池（事件驱动）
模式2: 趋势回踩优质池（基本面打底）

数据源: Sina K线（历史） + qt.gtimg.cn（实时）
运行: 每天15:30盘后自动
输出: memory/双模式选股/YYYY-MM-DD.md
"""
import requests, json, time, os, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

TIMEOUT = 8
OUT_DIR = os.path.expanduser("~/memory/双模式选股")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── 数据采集 ───

def fetch_sina_kline(code, days=250):
    """获取Sina日K线"""
    mkt = 'sh' if code.startswith('sh') or code.startswith('6') else 'sz'
    sym = code.replace('sh','').replace('sz','')
    url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={mkt}{sym}&scale=240&ma=no&datalen={days}'
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=TIMEOUT)
        data = r.json()
        if not data: return None
        return [{
            'date': d['day'],
            'open': float(d['open']),
            'close': float(d['close']),
            'high': float(d['high']),
            'low': float(d['low']),
            'vol': float(d['volume']),
        } for d in data]
    except:
        return None


def get_realtime(codes):
    """批量获取实时行情"""
    result = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        url = f'http://qt.gtimg.cn/q={",".join(batch)}'
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                f = line.split('~')
                if len(f) < 45: continue
                code = line.split('=')[0].split('_')[-1]
                name = f[1]
                px = float(f[3]) if f[3] else 0
                prev = float(f[4]) if f[4] else 0
                vol = int(f[6]) if f[6] else 0
                cap = float(f[44]) if len(f) > 44 and f[44] else 0
                chg = (px-prev)/prev*100 if prev else 0
                result[code] = {'name':name,'px':px,'chg':chg,'vol':vol,'cap':cap}
        except: continue
    return result


def get_stock_list_market():
    """获取全A股列表（从Sina）"""
    codes = []
    # 深市中小板+创业板+主板
    prefixes = [
        ('sz', '000001', '003000'),  # 深主板
        ('sz', '000001', '003000'),  # dupe, skip
    ]
    
    # 简化: 用固定的大盘股列表作为初筛基础
    # 实际生产中应该从全市场采集
    sample_codes = set()
    
    # 预加载我们已有的诸葛候选池股票
    from zhugeliang_daily_scan import CANDIDATES
    for codes_str in CANDIDATES.values():
        for c in codes_str.split(','):
            c = c.strip()
            if c: sample_codes.add(c)
    
    # 加上我们已知的其他方向
    extra = [
        'sh600602','sz300709','sz300684','sh603160',  # 屏下摄像
        'sz002456','sz002036','sz002273',               # 光学/镜头
        'sz300691','sz300433','sz300115','sz300136',    # 电子
        'sz002681','sz300322','sz300088',
        'sh600745','sz002241',
        'sh600316','sh600760','sh600893','sz000768',    # 军工
        'sz002049','sh603501','sh603986',               # 芯片
        'sz002156','sh600584',                          # 封测
        'sh600171','sh600460',                          # 半导体
        'sz002230','sh603019','sz000977',               # AI
        'sz300308','sz300502',
        'sh600276','sz300760',                          # 医药
        'sh601899','sh600362',
        'sz002624','sh603444',
        'sz002747','sz300124',
    ]
    sample_codes.update(extra)
    
    return sorted(sample_codes)


# ─── 模式1: 底部反转 ───

def check_mode1(kline, rt_info):
    """检查是否满足底部反转条件"""
    if not kline or len(kline) < 200:
        return None
    
    closes = [k['close'] for k in kline]
    volumes = [k['vol'] for k in kline]
    highs = [k['high'] for k in kline]
    lows = [k['low'] for k in kline]
    
    # ① 较近1年高点跌幅≥30%
    y1_high = max(highs[-200:])
    current = closes[-1]
    drawdown = (current - y1_high) / y1_high * 100
    if drawdown > -30:
        return None  # 跌幅不够
    
    # ② 连续10个交易日不创新低
    recent_10_low = min(lows[-10:])
    prior_10_low = min(lows[-20:-10]) if len(lows) >= 20 else recent_10_low - 1
    if recent_10_low < prior_10_low:
        return None
    
    # ③ 收盘价站稳20日均线
    if len(closes) < 21:
        return None
    ma20 = sum(closes[-20:]) / 20
    if current < ma20:
        return None
    
    # ④ 流动性: 近20日日均成交额
    avg_vol_20 = sum(volumes[-20:]) / 20
    cap = rt_info.get('cap', 0) * 1e8  # 总市值(元)
    avg_amount = avg_vol_20 * current
    
    # 用成交量×价格估算成交额（简化）
    # 实际成交额需要从API获取，这里用股数×均价近似
    est_amount = avg_vol_20 * sum(closes[-20:]) / 20
    
    # ⑤ 市值: 50-500亿
    if cap and (cap < 50e8 or cap > 500e8):
        return None
    
    # ⑥ 成交量温和放大 (30-80%)
    recent_5_vol = sum(volumes[-5:]) / 5
    if not (1.3 < recent_5_vol / avg_vol_20 < 1.8):
        return None
    
    score = abs(drawdown) + 5  # 跌幅越大分数越高
    if current / ma20 > 1.02:
        score += 5  # 站稳均线加分
    
    return {
        'drawdown': round(drawdown, 1),
        'score': round(score, 1),
        'ma20_above': round(current / ma20 * 100 - 100, 1),
        'vol_ratio': round(recent_5_vol / avg_vol_20, 2),
        'est_amount': round(est_amount / 1e8, 1),
    }


# ─── 模式2: 趋势回踩 ───

def check_mode2(kline, rt_info):
    """检查是否满足趋势回踩条件"""
    if not kline or len(kline) < 60:
        return None
    
    closes = [k['close'] for k in kline]
    volumes = [k['vol'] for k in kline]
    lows = [k['low'] for k in kline]
    
    current = closes[-1]
    
    # ① 近3个月低点逐步抬高
    month_ago_low = min(lows[-40:-20]) if len(lows) >= 40 else min(lows[-20:-10])
    recent_low_2 = min(lows[-20:-10])
    recent_low_1 = min(lows[-10:])
    
    if not (recent_low_1 > recent_low_2 > month_ago_low):
        return None
    
    # ② 累计涨幅≤60%
    period_low = min(lows[-60:])
    total_gain = (current - period_low) / period_low * 100
    if total_gain > 60:
        return None
    
    # ③ 流动性
    avg_vol_20 = sum(volumes[-20:]) / 20
    est_amount = avg_vol_20 * sum(closes[-20:]) / 20 / 1e8
    if est_amount < 1:
        return None
    
    cap = rt_info.get('cap', 0)
    if cap and (cap < 80 or cap > 800):
        return None
    
    # ④ 回踩确认: 缩量+小阳
    if len(volumes) < 6 or len(closes) < 31:
        return None
    avg_vol_5 = sum(volumes[-5:]) / 5
    daily_vol = volumes[-1]
    
    # 缩量至60%以下
    if daily_vol / avg_vol_5 > 0.6:
        return None
    
    # 小阳/十字星
    if len(kline) >= 2:
        today_chg = (closes[-1] - closes[-2]) / closes[-2] * 100
        if not (-2 < today_chg < 3):
            return None
    
    # ⑤ 回踩均线
    if len(closes) < 31:
        return None
    ma20 = sum(closes[-20:]) / 20
    ma30 = sum(closes[-30:]) / 30
    
    near_ma = abs(current - ma20) / ma20 < 0.03 or abs(current - ma30) / ma30 < 0.03
    if not near_ma:
        return None
    
    return {
        'total_gain': round(total_gain, 1),
        'near_ma': 'MA20' if abs(current-ma20)/ma20 < abs(current-ma30)/ma30 else 'MA30',
        'vol_shrink': round(daily_vol / avg_vol_5 * 100, 1),
        'est_amount': round(est_amount, 1),
    }


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"🔍 双模式选股扫描 | {today}")
    
    # 1. 获取标的列表
    codes = get_stock_list_market()
    print(f"  ┣ 标的池: {len(codes)}只")
    
    # 2. 获取实时行情
    rt = get_realtime(codes)
    print(f"  ┣ 实时行情: {len(rt)}只")
    
    # 3. 逐只扫描K线（并行）
    mode1_candidates = []
    mode2_candidates = []
    
    valid_codes = [c for c in codes if c in rt and rt[c]['px'] > 0]
    print(f"  ┣ 有效标的: {len(valid_codes)}只")
    
    done = 0
    for code in valid_codes:
        done += 1
        kline = fetch_sina_kline(code, 250)
        if not kline:
            continue
        
        info = rt[code]
        
        # 排雷: 无ST
        if 'ST' in info['name'] or '*ST' in info['name']:
            continue
        
        # 模式1
        m1 = check_mode1(kline, info)
        if m1:
            mode1_candidates.append({**info, 'code': code, 'mode1': m1})
        
        # 模式2
        m2 = check_mode2(kline, info)
        if m2:
            mode2_candidates.append({**info, 'code': code, 'mode2': m2})
        
        if done % 20 == 0:
            print(f"    ... {done}/{len(valid_codes)}")
    
    # 4. 排序输出
    mode1_candidates.sort(key=lambda x: -x['mode1']['score'])
    mode2_candidates.sort(key=lambda x: -x['mode2']['total_gain'])
    
    # ── 生成报告 ──
    report = [f"# 双模式选股 | {today}\n"]
    
    # 模式1
    report.append(f"## 📦 底部反转埋伏池 ({len(mode1_candidates)}只)\n")
    if mode1_candidates:
        report.append("| 代码 | 名称 | 现价 | 跌幅 | 20日均线上 | 量比 | 评分 |")
        report.append("|:---:|:----|:---:|:---:|:--------:|:---:|:---:|")
        for c in mode1_candidates[:10]:
            m = c['mode1']
            report.append(f"| {c['code']} | {c['name']} | {c['px']:.2f} | {m['drawdown']}% | +{m['ma20_above']}% | {m['vol_ratio']}x | {m['score']} |")
        report.append("")
        report.append("> 入场区间: 事件落地前20-30天分2批。止损: 近期最低点下方3%。")
        report.append("> ⚠️ 催化待人工确认（未来90天内的事件）。")
    else:
        report.append("无候选。\n")
    
    # 模式2
    report.append(f"\n## 📈 趋势回踩优质池 ({len(mode2_candidates)}只)\n")
    if mode2_candidates:
        report.append("| 代码 | 名称 | 现价 | 累计涨幅 | 回踩均线 | 缩量% |")
        report.append("|:---:|:----|:---:|:------:|:--------|:----:|")
        for c in mode2_candidates[:10]:
            m = c['mode2']
            report.append(f"| {c['code']} | {c['name']} | {c['px']:.2f} | {m['total_gain']}% | {m['near_ma']} | {m['vol_shrink']}% |")
        report.append("")
        report.append("> 建仓: 回踩确认后分批。止损: 放量破30日线3日不收回。")
    else:
        report.append("无候选。\n")
    
    # 5. 写入文件
    out_path = os.path.join(OUT_DIR, f"{today}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"  ┗ ✅ 完成 → {out_path}")
    print(f"\n📋 结果:")
    print(f"  底部反转: {len(mode1_candidates)}只")
    if mode1_candidates:
        top = mode1_candidates[0]
        print(f"    🥇 {top['name']} {top['px']:.2f} 跌幅{top['mode1']['drawdown']}% 评分{top['mode1']['score']}")
    print(f"  趋势回踩: {len(mode2_candidates)}只")
    if mode2_candidates:
        top = mode2_candidates[0]
        print(f"    🥇 {top['name']} {top['px']:.2f} 涨幅{top['mode2']['total_gain']}% 回踩{top['mode2']['near_ma']}")


if __name__ == '__main__':
    main()
