#!/usr/bin/env python3
"""
刘彻 V2.1 — 板块→个股T+1尾盘引擎
========================================
定位：关羽(板块资金)→刘彻(板块内筛个股)→尾盘T+1买入→次日出

输入：从关羽/刘备拿到目标板块（如半导体 有色 新能源）
输出：个股候选（含代码/价格/量比/评分）

用法：
  python3 liuche_v2.1.py --sectors 半导体 有色
  python3 liuche_v2.1.py --sectors 半导体       # 单板块
"""

import os, sys, json, datetime as dt, time
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "liuche_output")
os.makedirs(OUT_DIR, exist_ok=True)

MAX_DAILY = 2
MAX_FRIDAY = 1
MAX_CANDIDATES = 5

# 板块→核心成分股（只放流动性好的活跃票，短线关注这些就够了）
SECTOR_STOCKS = {
    "半导体": ["002371","603986","600703","688981","688012",
               "300661","600584","002049","603005","300223",
               "688126","002409","300456","300604","600171",
               "603690","688041","688008"],
    "有色": ["000831","600362","000630","002460","002466",
             "600111","601899","000975","600547","002155",
             "600489","603799","600010"],
    "银行": ["601398","601939","601288","601328","600036",
             "600016","000001","002142","601166","600000",
             "601988","601658","600919","601229","600015"],
    "新能源": ["300750","002594","300274","300763","601012",
               "600438","002129","300450","002709","300014",
               "002074","300124","688390","300568"],
    "光伏": ["601012","600438","002129","300274","300763",
             "688599","688223","605117","601615","603806"],
    "军工": ["600760","600893","002179","600862","600118",
             "600879","000768","002013","600685","300034",
             "600416","600765"],
    "证券": ["600030","300059","601688","601211","600837",
             "000776","002736","601236","601066","600061",
             "601878","601377"],
    "AI": ["300308","688041","688256","603019","002230",
           "000938","688111","300624","002415","688568"],
    "医药": ["600276","300760","300015","600196","002007",
             "300122","603259","300759","000661","300347",
             "300529","600085"],
    "消费": ["600519","000858","600887","002304","000568",
             "603288","002714","000333","002415","300750"],
    "机器人": ["300124","002747","300024","688160","688017",
               "603666","002527","300276","002896"],
    "酒": ["600519","000858","000568","600809","000596",
           "603369","600559","002304"],
}


def fetch_quotes(codes):
    """用腾讯行情批量查询"""
    result = {}
    for i in range(0, len(codes), 20):
        batch = codes[i:i+20]
        sh_codes = [c if c.startswith('sh') or c.startswith('sz') else
                    ('sh' + c if c.startswith('6') else 'sz' + c) for c in batch]
        url = f'http://qt.gtimg.cn/q={",".join(sh_codes)}'
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip():
                    continue
                f = line.split('~')
                if len(f) < 40:
                    continue
                raw_code = f[0].split('_')[-1].split('=')[0]
                code = raw_code[2:] if raw_code.startswith(('sh','sz')) else raw_code
                result[code] = {
                    "name": f[1],
                    "price": float(f[3]) if f[3] else 0,
                    "prev": float(f[4]) if f[4] else 0,
                    "high": float(f[33]) if f[33] else 0,
                    "low": float(f[34]) if f[34] else 0,
                    "vol_ratio": float(f[18]) if f[18] else 0,
                    "amount": float(f[37]) if f[37] else 0,
                }
        except:
            continue
    return result


def filter_candidates(quotes, sector_name, codes):
    """从板块内筛选短线T+1候选"""
    candidates = []

    for code in codes:
        q = quotes.get(code)
        if not q or q['price'] == 0:
            continue

        pct = (q['price'] - q['prev']) / q['prev'] * 100 if q['prev'] else 0
        amplitude = (q['high'] - q['low']) / q['prev'] * 100 if q['prev'] else 0
        vol_ratio = q['vol_ratio']
        amount = q['amount']

        # 条件1：涨幅0~3%（温和启动，不追高）
        if pct < 0 or pct > 3.0:
            continue
        # 条件2：量比>0.8（有资金动）
        if vol_ratio < 0.8:
            continue
        # 条件3：有成交（>2000万）
        if amount < 2e6:
            continue
        # 条件4：振幅>1%（有波动）
        if amplitude < 1.0:
            continue

        score = 50
        if 0 < pct <= 1.5: score += 25
        elif 1.5 < pct <= 3.0: score += 15
        if vol_ratio >= 1.5: score += 20
        elif vol_ratio >= 1.2: score += 10
        if amplitude >= 3: score += 10
        elif amplitude >= 2: score += 5
        if amount >= 1e8: score += 10

        candidates.append({
            "code": code,
            "name": q['name'],
            "price": round(q['price'], 2),
            "pct": round(pct, 2),
            "vol_ratio": round(vol_ratio, 2),
            "amount": amount,
            "amplitude": round(amplitude, 2),
            "score": score,
        })

    candidates.sort(key=lambda x: -x['score'])
    return candidates[:MAX_CANDIDATES]


def check_gate():
    gate_path = os.path.join(SCRIPT_DIR, "..", "memory", "秦始皇_output", "gate_status.json")
    if os.path.exists(gate_path):
        try:
            with open(gate_path) as f:
                g = json.load(f)
            return g.get('gate_level', '🟡'), g.get('score', 50)
        except:
            pass
    return '🟡', 50


def run(sectors):
    now = dt.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    is_friday = now.strftime('%A') == 'Friday'

    print("=" * 60)
    print(f"🐉 刘彻 V2.1 · 板块→个股T+1引擎 | {date_str}")
    print("=" * 60)

    if not sectors:
        print("❌ 未指定板块")
        print("用法: python3 liuche_v2.1.py --sectors 半导体 有色")
        return

    gate_level, gate_score = check_gate()
    print(f"  🚪 GATE: {gate_level} | 周五: {'⚠️' if is_friday else '否'}")

    if gate_level in ("🔴", "💀"):
        print("  ❌ GATE拦截，禁止开仓")
        return

    all_candidates = []

    for sector in sectors:
        codes = SECTOR_STOCKS.get(sector, [])
        if not codes:
            print(f"\n⚠️ 不支持板块 '{sector}'，可用: {list(SECTOR_STOCKS.keys())}")
            continue

        print(f"\n📡 {sector} ({len(codes)}只成分股)")
        print("-" * 40)

        quotes = fetch_quotes(codes)
        if not quotes:
            print("  ❌ 获取行情失败")
            continue

        # 板块内涨幅排名
        stocks_data = []
        for c in codes:
            q = quotes.get(c)
            if q and q['price'] > 0:
                pct = (q['price'] - q['prev']) / q['prev'] * 100 if q['prev'] else 0
                stocks_data.append((q['name'], c, pct, q['vol_ratio']))
        stocks_data.sort(key=lambda x: -x[2])

        print(f"  🏆 涨幅TOP3:")
        for n, c, p, v in stocks_data[:3]:
            emoji = "🔴" if p > 0 else "🟢"
            print(f"    {emoji} {n:>8}({c}) {p:+.2f}% 量比{v:.1f}")

        candidates = filter_candidates(quotes, sector, codes)
        print(f"  🎯 短线候选: {len(candidates)}只")
        for c in candidates:
            print(f"    {c['score']:3d}分 {c['name']:>8}({c['code']}) {c['pct']:+.2f}% 量比{c['vol_ratio']:.1f}")

        all_candidates.extend(candidates)

    print(f"\n{'='*60}")
    picks = all_candidates[: (MAX_FRIDAY if is_friday else MAX_DAILY)]

    if not picks:
        print("❌ 今日无候选")
        return

    print(f"🏆 最终候选 ({len(picks)}只):")
    print(f"  {'代码':<8} {'名称':<8} {'现价':<8} {'涨幅':<8} {'量比':<6} {'评分'}")
    print(f"  {'-'*44}")
    for c in picks:
        emoji = "✅" if c['score'] >= 70 else "🟡"
        print(f"  {emoji} {c['code']:<8} {c['name']:<8} {c['price']:<8.2f} {c['pct']:+.2f}%  {c['vol_ratio']:<6.1f} {c['score']}")

    # 存结果
    output = {
        "time": now.strftime("%Y-%m-%d %H:%M"),
        "sectors": sectors,
        "is_friday": is_friday,
        "gate": gate_level,
        "picks": picks,
    }
    with open(os.path.join(OUT_DIR, f"{date_str}_liuche_picks.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    args = sys.argv[1:]
    sectors = []
    for i, a in enumerate(args):
        if a == '--sectors' and i+1 < len(args):
            sectors = args[i+1:]
            break
    if not sectors:
        print("用法: python3 liuche_v2.1.py --sectors 半导体 有色 银行")
        sys.exit(1)
    run(sectors)
