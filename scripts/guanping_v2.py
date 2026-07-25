#!/usr/bin/env python3
"""
关平 V2.0 — 科技板块扫描 + 全市场涨停追踪 + 异动捕获
===================================================
升级：V1.0(科技36子板块) → V2.0(+涨停票扫描+当日异常涨幅+归档输出)

盲区修复：
  云赛智联 7/8涨停+7/16涨停 — V1.0个股池未收录 → 漏判
  修复：每日收盘扫全市场涨停票，不管在不在池里

输出：stdout + memory/关平扫描/YYYY-MM-DD.md
"""
import requests, json, time, re, os
from datetime import datetime

TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn"}

# ============= V1.0 保留：科技子板块 =============
TMT = {
    '芯片设计-AI算力': ['sz002049','sh603501','sz300661'],
    '芯片设计-存储': ['sh603986','sz300672'],
    '芯片设计-FPGA': ['sz002049','sh688385'],
    '封测': ['sz002185','sz002156','sh600584'],
    '设备': ['sz002371','sh688012'],
    '光通信': ['sz300308','sz300502','sz300394'],
    '算力-IDC': ['sh600941','sz300442'],
    '计算机-AI': ['sz000977','sh603019','sz002230'],
    '计算机-信创': ['sh600588','sz300454'],
    '传媒-游戏': ['sz002624','sh603444'],
    '机器人': ['sz002747','sz300124','sh601689'],
    '人形机器人': ['sz002050','sz002747','sh601689','sz300124','sh688017','sz002472','sh601100'],
    '光伏': ['sh601012','sz002459'],
    '储能': ['sz300274','sz300750'],
    '军工电子': ['sh600879','sh600118'],
    '军机': ['sh600760','sh600893','sz000768'],
}

STOCK_NAMES = {
    'sz002049':'紫光国微','sh603501':'韦尔股份','sz300661':'圣邦股份',
    'sh603986':'兆易创新','sz300672':'国科微','sh688385':'复旦微电',
    'sz002185':'华天科技','sz002156':'通富微电','sh600584':'长电科技',
    'sz002371':'北方华创','sh688012':'中微公司',
    'sz300308':'中际旭创','sz300502':'新易盛','sz300394':'天孚通信',
    'sh600941':'中国移动','sz300442':'润泽科技',
    'sz000977':'浪潮信息','sh603019':'中科曙光','sz002230':'科大讯飞',
    'sh600588':'用友网络','sz300454':'深信服',
    'sz002624':'完美世界','sh603444':'吉比特',
    'sz002747':'埃斯顿','sz300124':'汇川技术','sh601689':'拓普集团',
    'sh601012':'隆基绿能','sz002459':'晶澳科技',
    'sz300274':'阳光电源','sz300750':'宁德时代',
    'sh600879':'航天电子','sh600118':'中国卫星',
    'sh600760':'中航沈飞','sh600893':'航发动力','sz000768':'中航西飞',
}


def fetch_sina_batch(codes):
    """批量获取Sina实时行情，返回 {code: (price, prev_close, change%, vol, turnover)}"""
    result = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        try:
            r = requests.get(f'http://hq.sinajs.cn/list={",".join(batch)}',
                           headers=HEADERS, timeout=TIMEOUT)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                parts = line.split('"')
                if len(parts) < 2: continue
                fields = parts[1].split(',')
                if len(fields) < 6: continue
                code_raw = line.split('=')[0].split('_')[-1]
                px = float(fields[3]) if fields[3] else 0
                prev = float(fields[2]) if fields[2] else 0
                chg = (px - prev) / prev * 100 if prev else 0
                vol = int(fields[8]) if len(fields) > 8 and fields[8] else 0
                result[code_raw] = (px, prev, chg, vol)
        except Exception as e:
            continue
    return result


def get_limit_up_stocks():
    """抓取全市场涨停票 - 使用东方财富涨停板接口"""
    try:
        url = "https://push2ex.eastmoney.com/getTopicZTPool"
        params = {
            "ut": "7eea3edcaed734bea9cbfce24459edfa",
            "cb": "",
            "pageindex": 0,
            "pagesize": 200,
            "sort": "fbt%3Aasc",
            "date": "",
            "_": int(time.time()*1000)
        }
        # 尝试另一种接口
        url2 = "https://push2.eastmoney.com/api/qt/clist/get"
        params2 = {
            "pn": "1", "pz": "200", "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2",
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f20",
            "_": int(time.time()*1000)
        }
        r = requests.get(url2, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json()
        items = data.get("data", {}).get("diff", [])
        limit_ups = []
        for item in items:
            chg_pct = item.get("f3", 0)
            if chg_pct and float(chg_pct) >= 9.9:
                limit_ups.append({
                    "code": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "price": item.get("f2", 0),
                    "chg_pct": float(chg_pct),
                    "vol_ratio": item.get("f10", item.get("f20", 0)),
                    "turnover": item.get("f15", 0),
                    "cap": item.get("f20", 0),
                })
        return limit_ups
    except Exception as e:
        return []


def get_concept_boards():
    """获取概念板块行情 - 用于发现被忽略的板块"""
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "60", "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2",
            "fid": "f3", "fs": "m:90+t:3",
            "fields": "f2,f3,f4,f12,f14,f104,f105,f128,f140,f136",
            "_": int(time.time()*1000)
        }
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        data = r.json()
        items = data.get("data", {}).get("diff", [])
        boards = []
        for item in items:
            boards.append({
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "chg_pct": float(item.get("f3", 0)) if item.get("f3") else 0,
                "amount": item.get("f105", 0),
                "rise_count": item.get("f104", 0),
                "lead_stock": item.get("f128", ""),
            })
        return boards
    except:
        return []


def detect_anomalies(boards, limit_ups):
    """检测异常：领涨概念vs关注度不对称"""
    anomalies = []
    
    # 1. 涨停票最多的概念 ≠ 我们每天盯的概念
    board_zt = {}
    for b in boards:
        if b['rise_count'] and float(b['rise_count']) > 0:
            board_zt[b['name']] = float(b['rise_count'])
    
    # 2. 涨停票中市值50-200亿、非科技板块的
    for stock in limit_ups:
        cap_val = stock.get('cap', 0) or 0
        cap = float(cap_val) / 1e8 if cap_val else 0
        if 20 < cap < 300:
            anomalies.append(stock)
    
    return sorted(board_zt.items(), key=lambda x: -x[1]), anomalies


def run_tech_scan(all_prices):
    """运行科技子板块扫描"""
    lines = []
    lines.append("\n## 📟 科技子板块扫描\n")
    
    results = []
    for sector_name, codes in TMT.items():
        chgs = []
        for c in codes:
            code_key = c.split('.')[-1]
            if code_key in all_prices:
                px, prev, chg, vol = all_prices[code_key]
                chgs.append(chg)
        
        if chgs:
            avg = sum(chgs) / len(chgs)
            bar = '🚀' if avg > 6 else ('🟢' if avg > 2 else ('🟡' if avg > 0 else ('🔴' if avg > -2 else '💀')))
            results.append((avg, sector_name, bar))
    
    results.sort(key=lambda x: -x[0])
    
    lines.append("| 子板块 | 均涨跌 | 信号 |")
    lines.append("|:----|:---:|:---:|")
    for avg, name, bar in results:
        lines.append(f"| {name} | {avg:+.1f}% | {bar} |")
    
    # 最强/最弱
    if results:
        lines.append(f"\n> 🥇 最强: {results[0][1]} {results[0][0]:+.1f}%")
        lines.append(f"> 💀 最弱: {results[-1][1]} {results[-1][0]:+.1f}%")
    
    return "\n".join(lines)


def main():
    t0 = time.time()
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    
    print(f"🏹 关平 V2.0 启动 | {date_str} {time_str}")
    
    output_lines = [f"# 关平 V2.0 扫描 | {date_str} {time_str}\n"]
    
    # ───── 1. 涨停票扫描 ─────
    print("  ┣ 抓涨停票...")
    limit_ups = get_limit_up_stocks()
    output_lines.append(f"## 🔥 涨停票 ({len(limit_ups)}只)\n")
    
    if limit_ups:
        output_lines.append("| 代码 | 名称 | 涨幅 | 量比 | 换手 |")
        output_lines.append("|:----|:----|:---:|:---:|:---:|")
        
        for s in limit_ups[:40]:
            name = s['name']
            code = s['code']
            chg = s['chg_pct']
            vol_ratio = s.get('vol_ratio', '')
            turnover = s.get('turnover', '')
            v_str = f"{vol_ratio}" if vol_ratio else "-"
            t_str = f"{turnover}%" if turnover else "-"
            
            # 标记：不在关平个股池内 = 可能漏判
            code_key = f"sh{code}" if code.startswith('6') else f"sz{code}"
            known = code_key in STOCK_NAMES
            flag = "" if known else " ⚠️新"
            
            output_lines.append(f"| {code} | {name}{flag} | **+{chg:.1f}%** | {v_str} | {t_str} |")
        
        output_lines.append("")
        new_count = 0
        for s in limit_ups[:40]:
            c = s['code']
            code_key = f"sh{c}" if c.startswith('6') else f"sz{c}"
            if code_key not in STOCK_NAMES:
                new_count += 1
        output_lines.append(f"> ⚠️ 新面孔(不在V1.0池内): {new_count}只 — 这些涨停票我们的旧系统全漏")
    
    # ───── 2. 概念板块发现 ─────
    print("  ┣ 扫概念板块...")
    boards = get_concept_boards()
    output_lines.append(f"\n## 📊 概念板块 TOP 10\n")
    
    if boards:
        sorted_boards = sorted(boards, key=lambda x: -x['chg_pct'])
        output_lines.append("| 概念 | 涨幅 | 成分上涨数 | 领涨股 |")
        output_lines.append("|:----|:---:|:--------:|:------|")
        
        our_focus = {'半导体','芯片','军工','医药','消费','白酒','新能源','光伏','有色','通信','算力','Ai'}
        
        for b in sorted_boards[:15]:
            name = b['name']
            chg = b['chg_pct']
            rise = b.get('rise_count', '-')
            lead = b.get('lead_stock', '-')
            is_ours = "✅" if name in our_focus else "⚠️盲区"
            output_lines.append(f"| {name} {is_ours} | {chg:+.1f}% | {rise} | {lead} |")
        
        # 找出我们没盯的概念
        blind_spots = [b for b in sorted_boards[:15] 
                      if b['name'] not in our_focus and b['chg_pct'] > 2]
        if blind_spots:
            output_lines.append(f"\n> 🚨 盲区概念(涨>2%但不在关注池): {', '.join(b['name'] for b in blind_spots)}")
    
    # ───── 3. 保留V1.0科技扫描 ─────
    print("  ┣ 科技子板块扫描...")
    all_codes = []
    for codes in TMT.values():
        all_codes.extend(codes)
    all_codes = list(dict.fromkeys(all_codes))
    all_prices = fetch_sina_batch(all_codes)
    tech_report = run_tech_scan(all_prices)
    output_lines.append(tech_report)
    
    # ───── 4. 写入文件 ─────
    out_dir = os.path.expanduser("~/memory/关平扫描")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{date_str}.md")
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    elapsed = time.time() - t0
    print(f"  ┗ ✅ 完成 | {elapsed:.1f}s → {out_path}")
    
    # 输出摘要
    print(f"\n📋 摘要: 涨停{len(limit_ups)}只 | 概念板块{len(boards)}个 | 科技子板块{len(TMT)}个")


if __name__ == '__main__':
    main()
