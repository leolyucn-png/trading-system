#!/usr/bin/env python3
"""
刘彻 V2.0 — 短线T+1尾盘执行引擎
=====================================
定位：今日尾盘买，次日出。最多持有2天。

从张飞（量价风险判定）+ 关羽（资金流向）+ 刘备（舆情排雷）获取数据，
通过秦始皇GATE门控，输出最终可执行候选。

禁止持仓过周末（周五不推荐）。
禁止单日开仓>2只。
-5%硬止损。

成功案例：天风证券+6.6%、晶澳科技+10.5%、融捷股份+3.39%、京东方+11.1%

用法：
  python3 liuche_v2.py              # 正常扫描
  python3 liuche_v2.py --gate-only  # 只看GATE，不出候选
  python3 liuche_v2.py --candidates # 只看候选
"""

import os, sys, json, datetime as dt, time
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "liuche_output")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(SCRIPT_DIR, "..", "memory", "刘彻扫描"), exist_ok=True)

# ═══════════════════════════════════════════════
# 配置区
# ═══════════════════════════════════════════════
MAX_DAILY = 2           # 每日最多开仓
MAX_FRIDAY = 1          # 周五最多开仓
MAX_HOLD_DAYS = 2       # 最长持有天数
STOP_LOSS = -5.0        # 硬止损(%)
BUY_WINDOW_START = 1430 # 尾盘买入窗口开始
BUY_WINDOW_END = 1455   # 尾盘买入窗口结束

# ETF候选池（短线只做强势/活跃板块）
WATCH_ETF = {
    "sh512480":"半导体","sh512760":"芯片","sh512010":"医药",
    "sh512690":"酒","sh512660":"军工","sh512400":"有色",
    "sh516160":"新能源","sh515790":"光伏","sh562500":"机器人",
    "sh512880":"证券","sh512800":"银行","sh159928":"消费",
    "sh515230":"软件","sh159865":"养殖","sh159819":"AI",
    "sh515880":"通信","sh588000":"科创50",
    "sz159766":"旅游","sz159992":"创新药","sz159883":"医疗器械",
    "sz159745":"建材","sh515220":"煤炭","sh516020":"化工",
    "sh516970":"基建","sh512200":"地产",
}

TIMEOUT = 6


def fetch_etf_quotes():
    """获取ETF实时行情"""
    etf_codes = list(WATCH_ETF.keys())
    result = {}
    
    for i in range(0, len(etf_codes), 20):
        batch = etf_codes[i:i+20]
        url = f'http://qt.gtimg.cn/q={",".join(batch)}'
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip():
                    continue
                f = line.split('~')
                if len(f) < 40:
                    continue
                code = f[0].split('_')[-1]
                sector = WATCH_ETF.get(code, f[1])
                px = float(f[3]) if f[3] else 0
                prev = float(f[4]) if f[4] else 0
                vol = float(f[6]) if f[6] else 0  # 手
                amount = float(f[37]) if f[37] else 0  # 成交额
                high = float(f[33]) if f[33] else 0
                low = float(f[34]) if f[34] else 0
                
                chg = (px - prev) / prev * 100 if prev else 0
                amp = (high - low) / prev * 100 if prev else 0
                
                # 量比（腾讯档位有量比字段）
                vol_ratio = float(f[18]) if f[18] else 0
                
                result[code] = {
                    "sector": sector, "price": px, "prev": prev,
                    "chg": round(chg, 2), "vol": vol,
                    "amount": amount, "high": high, "low": low,
                    "amplitude": round(amp, 2), "vol_ratio": round(vol_ratio, 2),
                }
        except:
            continue
    
    return result


def load_gate_status():
    """读取秦始皇GATE状态"""
    gate_path = os.path.join(SCRIPT_DIR, "..", "memory", "秦始皇_output", "gate_status.json")
    if os.path.exists(gate_path):
        try:
            with open(gate_path) as f:
                return json.load(f)
        except:
            pass
    return {"gate_level": "🟡", "score": 50, "max_position": 60}


def load_zhangfei_risk():
    """读取张飞风险判定（高位预警板块）"""
    zf_path = os.path.join(SCRIPT_DIR, "..", "memory", "zhangfei_output", "zhangfei_watch_result.json")
    blocked = []
    if os.path.exists(zf_path):
        try:
            with open(zf_path) as f:
                data = json.load(f)
            for r in data.get('high_risk', []):
                blocked.append(r.get('name', ''))
        except:
            pass
    return blocked


def check_weekend_risk():
    """周五风险：今天周五？"""
    today = dt.datetime.now().strftime('%A')
    return today == 'Friday'


def identify_candidates(etfs, gate, blocked, is_friday):
    """从ETF中筛选短线候选"""
    candidates = []
    max_picks = MAX_FRIDAY if is_friday else MAX_DAILY
    
    # GATE拦截
    if gate.get('gate_level') in ("🔴", "💀"):
        return [], f"GATE {gate['gate_level']}，禁止开仓"
    
    for code, info in etfs.items():
        sector = info['sector']
        chg = info['chg']
        vol_ratio = info['vol_ratio']
        amount = info['amount']
        
        # 张飞拦截
        if sector in blocked:
            continue
        
        # 条件1：板块不能太冷（成交额>5000万）
        if amount < 5e6:
            continue
        
        # 条件2：板块不能太热（涨幅>3%不追）
        if chg > 3.0:
            continue
        
        # 条件3：板块不能暴跌（跌幅>-3%不接飞刀）
        if chg < -3.0:
            continue
        
        # 条件4：量比>1.0（有资金动）
        if vol_ratio < 1.0:
            continue
        
        candidates.append({
            "code": code,
            "sector": sector,
            "chg": chg,
            "vol_ratio": vol_ratio,
            "price": info['price'],
            "amount": info['amount'],
            "amplitude": info['amplitude'],
            "score": _calc_score(chg, vol_ratio, info['amplitude']),
        })
    
    # 按评分排序
    candidates.sort(key=lambda x: -x['score'])
    
    return candidates[:max_picks], f"GATE {gate['gate_level']}, 上限{max_picks}只"


def _calc_score(chg, vol_ratio, amplitude):
    """
    短线评分（越高越好）
    - 涨幅在0~2%之间加分（温和启动，不是高潮）
    - 量比>1.5加分（资金活跃）
    - 振幅>2%加分（有波动空间）
    - 跌幅>-1%不扣分
    """
    score = 50
    
    # 涨幅评分
    if 0 < chg <= 1.5:
        score += 20  # 温和启动最佳
    elif 1.5 < chg <= 3.0:
        score += 10  # 还行
    elif -1 <= chg <= 0:
        score += 5   # 微跌，可能建仓
    
    # 量比评分
    if vol_ratio >= 2.0:
        score += 20
    elif vol_ratio >= 1.5:
        score += 15
    elif vol_ratio >= 1.2:
        score += 5
    
    # 振幅评分
    if amplitude >= 3:
        score += 10
    elif amplitude >= 2:
        score += 5
    
    return score


def run():
    now = dt.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    hour_min = now.hour * 100 + now.minute
    is_friday = check_weekend_risk()
    
    print("=" * 60)
    print(f"🐉 刘彻 V2.0 · 短线T+1尾盘引擎 | {date_str}")
    print("=" * 60)
    
    # 时间检查
    if hour_min < BUY_WINDOW_START or hour_min > BUY_WINDOW_END:
        if not (hour_min < 930):  # 盘后也可以跑（复盘模式）
            print(f"  ⏰ 非尾盘窗口(14:30-14:55)，当前{hour_min//100}:{hour_min%100:02d}")
            if hour_min > 1500:
                print(f"  盘后模式：仅做复盘，不出候选")
    
    # 尾盘窗口提示
    if BUY_WINDOW_START <= hour_min <= BUY_WINDOW_END:
        print(f"  🎯 尾盘窗口打开中 (14:30-14:55)")
    if is_friday:
        print(f"  ⚠️ 周五：最多推荐1只，建议空仓过周末")
    
    # 1. 采集
    print(f"\n📡 采集ETF数据...")
    etfs = fetch_etf_quotes()
    if not etfs:
        print("  ❌ 无ETF数据")
        return
    print(f"  ✅ {len(etfs)}个ETF")
    
    # 2. 读取GATE
    gate = load_gate_status()
    print(f"\n🚪 GATE: {gate.get('gate_level','🟡')} 评分{gate.get('score','?')} 仓位上限{gate.get('max_position','?')}%")
    
    # 3. 读取张飞风险
    blocked = load_zhangfei_risk()
    if blocked:
        print(f"  🗡️ 张飞拦截: {blocked}")
    
    # 4. 挑候选
    print(f"\n🔍 筛选短线候选...")
    candidates, note = identify_candidates(etfs, gate, blocked, is_friday)
    
    if candidates:
        print(f"\n🏆 今日短线候选 ({len(candidates)}只):")
        print(f"  {'板块':<10} {'涨跌':<8} {'量比':<8} {'评分':<6} {'建议'}")
        print(f"  {'-'*40}")
        for c in candidates:
            action = "尾盘关注" if 0 <= c['chg'] <= 2.0 else "观察"
            emoji = "✅" if c['score'] >= 70 else ("🟡" if c['score'] >= 55 else "👀")
            print(f"  {emoji} {c['sector']:<10} {c['chg']:+.2f}%  {c['vol_ratio']:.1f}x  {c['score']:<4}  {action}")
        
        # 第一条建议
        best = candidates[0]
        print(f"\n🦁 第一候选: {best['sector']} (评分{best['score']})")
        print(f"   尾盘14:30-14:55确认买入")
        if is_friday:
            print(f"   ⚠️ 周五，仅此1只，且建议谨慎")
    else:
        print(f"  ❌ 今日无候选")
        print(f"  原因: {note}")
    
    # 5. 保存
    output = {
        "time": now.strftime("%Y-%m-%d %H:%M"),
        "is_friday": is_friday,
        "gate": gate,
        "candidates": candidates,
        "summary": f"{len(candidates)}只候选 | {note}",
    }
    out_path = os.path.join(OUT_DIR, f"{date_str}_liuche.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # 也写入刘彻扫描目录
    scan_path = os.path.join(SCRIPT_DIR, "..", "memory", "刘彻扫描", f"{date_str}.md")
    with open(scan_path, "w") as f:
        f.write(f"# 🐉 刘彻 V2.0 短线扫描 | {date_str}\n\n")
        f.write(f"GATE: {gate.get('gate_level','?')} | 候选: {len(candidates)}只\n\n")
        if candidates:
            f.write("| 候选 | 涨幅 | 量比 | 评分 |\n")
            f.write("|:----|:---:|:---:|:---:|\n")
            for c in candidates:
                f.write(f"| {c['sector']} | {c['chg']:+.2f}% | {c['vol_ratio']:.1f}x | {c['score']} |\n")
    
    print(f"\n💾 已保存: liuche_output/{date_str}_liuche.json")


def run_candidates_only():
    """只输出候选（供其他模型消费）"""
    etfs = fetch_etf_quotes()
    gate = load_gate_status()
    blocked = load_zhangfei_risk()
    candidates, _ = identify_candidates(etfs, gate, blocked, check_weekend_risk())
    print(json.dumps(candidates, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if "--candidates" in sys.argv:
        run_candidates_only()
    else:
        run()
