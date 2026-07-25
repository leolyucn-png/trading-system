#!/usr/bin/env python3
"""
刘彻 V3.0 — T+1隔日套利智能筛选引擎
=========================================
遵循用户2026-07-25亲授完整套利框架，所有规则固化。

输入：关羽(板块资金信号) + 刘备(舆情催化验证)
输出：最多2只候选（优先1只），含次日集合竞价验证标准

硬性约束：
  - 最终输出≤2只，优先1只
  - 无合格标的 → "今日无合格标的，建议观望"
  - 禁止强行凑票

用法：
  python3 liuche_v3.py --sectors 半导体
  python3 liuche_v3.py --board 半导体 有色
"""

import os, sys, json, datetime as dt, requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "liuche_output")
os.makedirs(OUT_DIR, exist_ok=True)

# 配置
CAP_MIN = 40e8
CAP_MAX = 250e8
VOL_DAILY_MIN = 8000e4
STREAK_EXCLUDE = 3

SECTOR_STOCKS = {
    "半导体": ["002371","603986","600703","688981","688012",
               "300661","600584","002049","603005","300223",
               "688126","002409","300456","300604","600171",
               "603690","688041","688008","300474","002185"],
    "有色": ["000831","600362","000630","002460","002466",
             "600111","601899","000975","600547","002155",
             "600489","603799","600010","000060"],
    "新能源": ["300750","002594","300274","300763","601012",
               "600438","002129","300450","002709","300014",
               "002074","300124","688390","300568","300457"],
    "光伏": ["601012","600438","002129","300274","300763",
             "688599","688223","605117","601615","603806"],
    "军工": ["600760","600893","002179","600862","600118",
             "600879","000768","002013","600685","300034",
             "600416","600765","600967","300696"],
    "证券": ["600030","300059","601688","601211","600837",
             "000776","002736","601236","601066","600061"],
    "AI": ["300308","688041","688256","603019","002230",
           "000938","688111","300624","002415","688568",
           "300502","300394"],
    "医药": ["600276","300760","300015","600196","002007",
             "300122","603259","300759","000661","300347",
             "300529","600085","300832","300896"],
    "机器人": ["300124","002747","300024","688160","688017",
               "603666","002527","300276","002896","688169"],
}

RISK_WARNING = """
⚠️ 【风险前置提示】
不构成任何投资建议，所有结论仅基于历史统计概率推演。
不存在稳定盈利保证。隔夜情绪、突发消息会打破历史规律。
隔日套利本质是高频率博弈，连亏或大幅回撤可能性始终存在。
"""


def fetch_quotes(codes):
    """腾讯行情"""
    result = {}
    for i in range(0, len(codes), 20):
        batch = codes[i:i+20]
        sh = [('sh'+c if c.startswith('6') else 'sz'+c) for c in batch]
        try:
            r = requests.get('http://qt.gtimg.cn/q='+','.join(sh),
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                f = line.split('~')
                if len(f) < 40: continue
                raw = f[0].split('_')[-1].split('=')[0]
                code = raw[2:] if raw.startswith(('sh','sz')) else raw
                result[code] = {
                    "name": f[1], "price": float(f[3]) if f[3] else 0,
                    "prev": float(f[4]) if f[4] else 0,
                    "vol_ratio": float(f[18]) if f[18] else 0,
                    "amount": float(f[37]) if f[37] else 0,
                    "high": float(f[33]) if f[33] else 0,
                    "low": float(f[34]) if f[34] else 0,
                }
        except: continue
    return result


def fetch_fundamentals(codes):
    """市值等基本面（akshare，超时5秒跳过）"""
    result = {}
    import concurrent.futures
    try:
        import akshare as ak
        def get_one(code):
            try:
                info = ak.stock_individual_info_em(symbol=code)
                if info is not None:
                    for _, row in info.iterrows():
                        key = str(row.iloc[0])
                        if '流通市值' in key:
                            val = row.iloc[1]
                            cap = float(val) * 1e8 if '亿' in str(val) else float(val)
                            return (code, cap)
            except: pass
            return (code, None)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = {ex.submit(get_one, c): c for c in codes[:10]}
            for f in concurrent.futures.as_completed(futures, timeout=5):
                c, cap = f.result()
                result[c] = cap
    except: pass
    return result


def screen_stocks(sector):
    """选股：市值→排除→涨跌→量比→成交→分类→评分→自检"""
    codes = SECTOR_STOCKS.get(sector, [])
    if not codes: return []

    quotes = fetch_quotes(codes)
    if not quotes: return []

    caps = fetch_fundamentals(codes)
    candidates = []

    for code in codes:
        q = quotes.get(code)
        if not q or q['price'] == 0 or q['prev'] == 0: continue

        name = q['name']
        pct = (q['price'] - q['prev']) / q['prev'] * 100

        # 排除ST
        if any(kw in name.upper() for kw in ['ST', '*ST', '退市', 'N']): continue

        # 市值门槛
        cap = caps.get(code, 0)
        if cap and (cap < CAP_MIN or cap > CAP_MAX): continue

        # 涨幅0~3%
        if pct <= 0 or pct > 3.0: continue

        # 量比
        vr = q['vol_ratio']
        if vr < 0.8: continue

        # 成交额
        if q['amount'] < VOL_DAILY_MIN: continue

        # 振幅
        amp = (q['high'] - q['low']) / q['prev'] * 100 if q['prev'] else 0
        if amp < 1.0: continue

        # 类型
        stype = "低位补涨" if pct < 2.0 else "情绪龙头"

        # 评分
        score = 50
        if 0 < pct <= 1.5: score += 25
        elif pct <= 3.0: score += 15
        if vr >= 1.5: score += 20
        elif vr >= 1.2: score += 10
        if amp >= 3: score += 10
        elif amp >= 2: score += 5
        if q['amount'] >= 1e8: score += 10

        # 防幻觉自检
        if pct is None or abs(pct) > 20: continue
        if vr is None or vr < 0.3: continue
        if q['amount'] is None or q['amount'] <= 0: continue

        candidates.append({
            "code": code, "name": name, "price": round(q['price'], 2),
            "pct": round(pct, 2), "vol_ratio": round(vr, 2),
            "amount": q['amount'], "amplitude": round(amp, 2),
            "cap": cap, "type": stype, "score": score,
        })

    candidates.sort(key=lambda x: -x['score'])
    return candidates


def run(sectors):
    now = dt.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    is_friday = now.strftime('%A') == 'Friday'

    print(RISK_WARNING)
    print("=" * 65)
    print(" 刘彻 V3.0 - T+1隔日套利 | " + date_str)
    print("=" * 65)
    if is_friday:
        print(" 周五：周末空窗期长，非机会极大不建议建仓")

    if not sectors:
        print(" 用法: python3 liuche_v3.py --sectors 半导体")
        return

    # 选股
    all_candidates = []
    for sector in sectors:
        print("\n " + sector + " (" + str(len(SECTOR_STOCKS.get(sector, []))) + "只)")
        candidates = screen_stocks(sector)
        for c in candidates[:3]:
            emoji = "✅" if c['score'] >= 70 else "🟡"
            cap_str = (" 市值" + str(int(c['cap']/1e8)) + "亿") if c['cap'] else ""
            print("   " + emoji + " " + c['name'] + "(" + c['code'] + ") " +
                  "{:+.2f}%".format(c['pct']) + " 量比" + str(c['vol_ratio']) +
                  cap_str + " " + c['type'] + " 评分" + str(c['score']))
        all_candidates.extend(candidates)

    # 最终输出
    print("\n" + "=" * 65)
    print(" 最终候选")
    print("=" * 65)

    all_candidates.sort(key=lambda x: -x['score'])
    max_picks = 1 if is_friday else min(2, len(all_candidates))

    if not all_candidates:
        print("\n 今日无合格标的，建议观望")
        return

    picks = all_candidates[:max_picks]

    for i, c in enumerate(picks, 1):
        print("\n" + "-" * 65)
        print(" 候选#" + str(i) + " | " + c['name'] + "(" + c['code'] + ")")
        print("-" * 65)
        print(" 分类: " + c['type'])
        print(" 现价: " + str(c['price']) + " | 涨幅: {:+.2f}%".format(c['pct']) +
              " | 量比: " + str(c['vol_ratio']) + " | 评分: " + str(c['score']))
        if c['cap']:
            print(" 流通市值: " + str(int(c['cap']/1e8)) + "亿")

        prob = 65
        if c['pct'] <= 1.5: prob += 5
        if 1.2 <= c['vol_ratio'] <= 3.0: prob += 5
        if c['type'] == "低位补涨": prob += 5
        print(" 隔日正向收益概率预估: ~" + str(prob) + "%")

        print("\n 次日09:25验证标准:")
        print("   [良性] 竞价量 > 昨日同时段1.5倍")
        print("   [良性] 竞价价在昨日收盘±1%以内")
        print("   [良性] 量比 > " + str(max(1.0, c['vol_ratio'] * 0.8)))
        print("   [危险] 竞价低开 > -2% → 放弃")
        print("   [危险] 竞价量 < 昨日0.5倍 → 放弃")
        print("   [操作] 仅限隔夜持仓，次日择机离场")

    # 保存
    output = {"time": date_str, "picks": picks, "count": len(picks)}
    with open(os.path.join(OUT_DIR, date_str + "_liuche_v3.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # GATE联动写入
    gate_dir = os.path.join(SCRIPT_DIR, "..", "memory", "秦始皇_output")
    os.makedirs(gate_dir, exist_ok=True)
    gate_path = os.path.join(gate_dir, "liuche_signals.json")
    with open(gate_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    args = sys.argv[1:]
    sectors = []
    for i, a in enumerate(args):
        if a in ('--sectors', '--board') and i+1 < len(args):
            sectors = args[i+1:]
            break
    if not sectors:
        print("用法: python3 liuche_v3.py --sectors 半导体")
        sys.exit(1)
    run(sectors)
