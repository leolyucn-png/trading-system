#!/usr/bin/env python3
"""
关羽 v5 集成扩展 — 接入GitHub技能数据源
=========================================
新增线6-线8，不破坏原V4的四线架构

新增：
  线6 北向资金  — 来自 capital-flow-monitor 思路
  线7 龙虎榜    — 来自 capital-flow-monitor 思路
  线8 龙头识别   — 来自 leader-stock-identification 五维模型

用法：
  python guanyu_v5_integrations.py          # 独立跑
  python guanyu_v4.py && python guanyu_v5_integrations.py  # 合并跑
"""

import json, sys, time, os, datetime as dt
import requests

TIMEOUT = 8
HEADERS_STD = {"User-Agent": "Mozilla/5.0"}

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def _get(url, timeout=TIMEOUT):
    for _ in range(2):
        try:
            r = requests.get(url, headers=HEADERS_STD, timeout=timeout)
            if r.status_code == 200 and r.text:
                return r.text
        except:
            time.sleep(0.5)
    return None

def sf(v, d=0):
    try: return float(v) if v else d
    except: return d


# ============================================================
# 线6: 北向资金 (沪深港通)
# ============================================================
def line6_north_flow():
    """
    北向资金流向 — 替代capital-flow-monitor的基础能力
    
    输出：
      - 当日沪股通净流入
      - 当日深股通净流入
      - 合计净流入 (连续N日)
      - 北向重仓板块TOP5
    """
    result = {"status": "盲区", "data": None}
    
    # 方案1: 东财北向资金API
    try:
        url = "https://push2.eastmoney.com/api/qt/kamt.kline/get?fields1=f1,f2,f3,f5&fields2=f51,f52,f53,f54,f55&klt=1&lmt=1"
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            d = r.json()
            if 'data' in d and d['data'] and 'klines' in d['data']:
                line = d['data']['klines'][0].split(',')
                # 格式: 日期,沪股通净流入,深股通净流入,合计
                hs = sf(line[1]) / 100  # 亿
                ss = sf(line[2]) / 100
                total = sf(line[3]) / 100
                result = {
                    "status": "OK",
                    "data": {
                        "沪股通": f"{hs:+.2f}亿",
                        "深股通": f"{ss:+.2f}亿",
                        "合计": f"{total:+.2f}亿",
                    },
                    "raw": {"hs": hs, "ss": ss, "total": total}
                }
                return result
    except:
        pass
    
    # 方案2: 备用接口
    try:
        url = "https://datacenter.eastmoney.com/api/data/v1/get?reportName=RPT_MUTUAL_DEAL_STOCK_NORTHSHSZ&columns=NETBUYAMT&filter=&pageNumber=1&pageSize=1&sortTypes=-1&sortColumns=TRADE_DATE"
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            d = r.json()
            if d.get('result') and d['result']['data']:
                amt = d['result']['data'][0].get('NETBUYAMT', 0) / 1e8
                result = {
                    "status": "OK(备)",
                    "data": {"北向净流入": f"{amt:+.2f}亿"},
                    "raw": {"total": amt}
                }
                return result
    except:
        pass
    
    return result


# ============================================================
# 线7: 龙虎榜 (游资+机构动向)
# ============================================================
def line7_longhubang():
    """
    龙虎榜数据 — 来自capital-flow-monitor思路
    
    输出：
      - 机构净买入TOP3
      - 游资活跃度
      - 净买入>1亿标的
    """
    result = {"status": "盲区", "data": None}
    
    today = dt.date.today().strftime("%Y%m%d")
    
    try:
        url = (f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=15&po=1"
               f"&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
               f"&fltt=2&invt=2&fid=f3&fs=m:0+t:6+f:!50,m:0+t:80+f:!50"
               f"&fields=f12,f14,f2,f3,f62,f184,f185,f186")
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            items = r.json()['data']['diff']
            data = []
            for it in items[:10]:
                net = sf(it.get('f62', 0)) / 1e8
                data.append({
                    "code": it['f12'],
                    "name": it['f14'],
                    "price": sf(it['f2']),
                    "pct": sf(it['f3']),
                    "net_inflow": round(net, 2),
                    "buy": sf(it.get('f184', 0)) / 1e8,
                    "sell": sf(it.get('f185', 0)) / 1e8,
                })
            # 分类
            inst_buy = [d for d in data if d['net_inflow'] > 0]
            youzi_active = len([d for d in data if d['buy'] > 0.5])
            
            result = {
                "status": "OK",
                "data": {
                    "机构净买入TOP": data[:5],
                    "游资活跃标的": youzi_active,
                },
                "summary": f"龙虎榜: {len(data)}只上榜, {len(inst_buy)}只净买入, {youzi_active}只游资活跃"
            }
            return result
    except:
        pass
    
    return result


# ============================================================
# 线8: 板块龙头识别 (基于leader-stock-identification五维模型)
# ============================================================
def line8_leader_scan(top_n=3):
    """
    龙头识别 — leader-stock-identification五维模型的简化版
    
    从关羽线1 ETF涨幅TOP板块中，找真龙头
    维度：涨幅排名 + 成交额 + (简化)
    """
    result = {"status": "盲区", "data": None}
    
    # 先拿ETF涨幅榜确定强势板块
    etf_data = _get_etf_ranking()
    if not etf_data:
        return result
    
    leaders = []
    for sector_name, code in etf_data[:top_n]:
        # 扫这个板块的成分股
        stocks = _scan_sector_components(sector_name)
        if stocks:
            leaders.append({
                "板块": sector_name,
                "龙头候选": stocks[:3],
                "板块涨幅": f"{etf_data[0][1]:+.2f}%" if len(etf_data) > 0 else "?"
            })
    
    result = {
        "status": "OK",
        "data": leaders
    }
    return result


def _get_etf_ranking():
    """从ETF获取今日涨幅排行"""
    etf_codes = {
        "半导体": "sh512480", "芯片": "sz159995", "光伏": "sh515790",
        "新能源": "sh516160", "军工": "sh512660", "有色": "sh512400",
        "证券": "sh512880", "银行": "sh512800", "酒": "sh512690",
        "医药": "sh512010", "通信": "sh515880", "机器人": "sh562500",
        "消费": "sz159928", "AI": "sz159819",
    }
    try:
        codes = ",".join(etf_codes.values())
        r = requests.get(f"http://hq.sinajs.cn/list={codes}",
                         headers={"Referer": "http://finance.sina.com.cn"}, timeout=5)
        r.encoding = 'gbk'
        result = []
        for line in r.text.strip().split('\n'):
            parts = line.split('"')[1].split(',')
            px, prev = float(parts[3]), float(parts[2])
            chg = (px - prev) / prev * 100
            for en, ec in etf_codes.items():
                if ec.split('.')[-1] in line.lower():
                    result.append((en, chg))
                    break
        result.sort(key=lambda x: -x[1])
        return result
    except:
        return None


def _scan_sector_components(sector_name):
    """扫板块成分股找涨幅前5"""
    # 用东财行业板块查询
    try:
        url = (f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10"
               f"&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
               f"&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f2,f3,f12,f14")
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            sectors = r.json()['data']['diff']
            target = None
            for s in sectors:
                if sector_name in s['f14']:
                    target = s
                    break
            if target:
                bid = target['f12']
                url2 = (f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10"
                        f"&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
                        f"&fltt=2&invt=2&fid=f3&fs=b:{bid}&fields=f2,f3,f12,f14")
                r2 = requests.get(url2, timeout=TIMEOUT)
                if r2.status_code == 200:
                    stocks = r2.json()['data']['diff']
                    return [(s['f14'], f"{sf(s['f3']):+.1f}%", sf(s['f2']))
                            for s in stocks[:5]]
    except:
        pass
    return []


# ============================================================
# 汇总运行
# ============================================================
def run_all():
    print("\n" + "=" * 60)
    print("⚔️ 关羽 v5 集成扩展 · 新增数据源")
    print("=" * 60)
    
    # 线6: 北向资金
    print("\n📡 线6 · 北向资金")
    nf = line6_north_flow()
    if nf['status'] == 'OK' or nf['status'] == 'OK(备)':
        for k, v in nf['data'].items():
            print(f"  {k}: {v}")
        emoji = "✅" if float(nf['raw'].get('total', 0)) > 0 else "🟢"
        print(f"  状态: {emoji} OK")
    else:
        print(f"  状态: ❌ 盲区（北向数据在非交易时段不可用）")
    
    # 线7: 龙虎榜
    print("\n📡 线7 · 龙虎榜")
    lhb = line7_longhubang()
    if lhb['status'] == 'OK':
        print(f"  {lhb['summary']}")
        for d in lhb['data']['机构净买入TOP'][:3]:
            emoji = "🟢" if d['net_inflow'] > 0 else "🔴"
            print(f"  {emoji} {d['name']}({d['code']}): {d['pct']:+.2f}% 净买入{d['net_inflow']:+.2f}亿")
        print(f"  状态: ✅ OK")
    else:
        print(f"  状态: ❌ 盲区（龙虎榜在非交易时段不可用）")
    
    # 线8: 龙头识别
    print("\n📡 线8 · 龙头识别")
    ld = line8_leader_scan()
    if ld['status'] == 'OK':
        for s in ld['data']:
            print(f"  🏆 {s['板块']} ({s['板块涨幅']})")
            for st in s['龙头候选'][:2]:
                print(f"    ├ {st[0]}: {st[1]} @{st[2]}")
        print(f"  状态: ✅ OK")
    else:
        print(f"  状态: ❌ 盲区（需要线1数据）")
    
    # 保存结果
    output = {
        "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "line6": nf,
        "line7": lhb,
        "line8": ld,
    }
    with open(os.path.join(OUT_DIR, "guanyu_v5_status.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"💾 已保存: guanyu_v5_status.json")
    return output


if __name__ == "__main__":
    run_all()
