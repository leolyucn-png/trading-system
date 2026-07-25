#!/usr/bin/env python3
"""
刘彻 V1.0 — 全板块轮动埋伏扫描引擎 (ETF数据源版)
===================================================
数据源: qt.gtimg.cn (稳如狗) — 40个行业/主题ETF

功能:
  ✅ 40+行业ETF全量扫描
  ✅ 放量不涨检测（量>均量+价微动）
  ✅ 连续蓄力检测（历史日对比）
  ✅ 轮动方向输出（最强/最弱/转向）
  ✅ 暗流板块发现（价微涨+量暴增）

输出: stdout + memory/刘彻扫描/YYYY-MM-DD.md
"""
import requests, json, time, os, sys
from datetime import datetime, timedelta

TIMEOUT = 8

# 40个行业/主题ETF → 板块映射
ETF_MAP = {
    'sh512480':'半导体','sh512760':'芯片','sh588200':'科创芯片',
    'sh512010':'医药','sh159883':'医疗器械','sz159992':'创新药',
    'sh512690':'酒','sh159928':'消费','sz159766':'旅游','sz159825':'农业',
    'sh512660':'军工','sh512670':'国防','sh512710':'军工龙头',
    'sh512400':'有色','sz159980':'有色期货','sh518880':'黄金',
    'sh159930':'能源','sz159945':'石油','sh159840':'碳中和',
    'sh516160':'新能源','sh159857':'光伏','sz159840':'储能',
    'sz159838':'新能车','sh515700':'新能源车','sh515790':'光伏产业',
    'sh512720':'计算机','sh159869':'软件','sh515230':'通信','sh515880':'通信设备',
    'sh159994':'5G','sh515050':'5GETF',
    'sh562500':'机器人','sz159770':'机器人AI','sh516360':'机器人ETF',
    'sh512200':'地产','sh159707':'基建','sh515250':'建材',
    'sh159865':'养殖','sh159867':'畜牧','sh516670':'畜牧养殖',
    'sh512880':'证券','sh512800':'银行',
    'sz159766':'旅游','sz159825':'农业','sz159829':'游戏','sh516620':'影视',
    'sh512890':'红利','sh510050':'上证50','sh588000':'科创50','sz159915':'创业板',
}


def fetch_etf_data():
    """从qt.gtimg.cn获取全部ETF数据"""
    etf_codes = list(ETF_MAP.keys())
    result = {}
    
    for i in range(0, len(etf_codes), 20):
        batch = etf_codes[i:i+20]
        url = f'http://qt.gtimg.cn/q={",".join(batch)}'
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                fields = line.split('~')
                if len(fields) < 40: continue
                code = fields[0].split('_')[-1]
                name = fields[1]
                px = float(fields[3]) if fields[3] else 0
                prev = float(fields[4]) if fields[4] else 0
                vol = float(fields[6]) if fields[6] else 0
                high = float(fields[33]) if fields[33] else 0
                low = float(fields[34]) if fields[34] else 0
                
                chg_pct = (px - prev) / prev * 100 if prev else 0
                sector = ETF_MAP.get(code, name)
                
                result[code] = {
                    'sector': sector, 'name': name,
                    'price': px, 'prev': prev, 'chg_pct': chg_pct,
                    'vol': vol, 'high': high, 'low': low,
                    'amplitude': (high - low) / prev * 100 if prev else 0
                }
        except Exception as e:
            continue
    
    return result


def load_history(history_dir, etfs, days=3):
    """加载历史成交量 - 优先读本地，没有则从Sina日K线补"""
    hist = {}
    for d in range(1, days+1):
        date_str = (datetime.now() - timedelta(days=d)).strftime('%Y-%m-%d')
        path = os.path.join(history_dir, f"etf_{date_str}.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for code, info in data.items():
                    if code not in hist: hist[code] = []
                    hist[code].append(info.get('vol', 0))
            except: pass
    
    if not hist:
        try:
            for code in list(etfs.keys())[:10]:
                mkt = 'sh' if code.startswith('sh') else 'sz'
                sym = code[2:]
                url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={mkt}{sym}&scale=240&ma=no&datalen=2'
                r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=3)
                data = r.json()
                if data and len(data) >= 2:
                    hist[code] = [float(data[-2].get('volume', 0))]
                time.sleep(0.05)
        except: pass
    return hist


def detect_signals(etfs, history):
    """检测三大信号"""
    vol_up = []      # 放量不涨
    accum = []       # 连续蓄力
    rotation = []    # 轮动方向
    
    for code, info in etfs.items():
        chg = info['chg_pct']
        vol = info['vol']
        sector = info['sector']
        
        # 计算量比
        hist_vols = history.get(code, [])
        avg_vol = sum(hist_vols) / len(hist_vols) if hist_vols else vol
        vol_ratio = vol / avg_vol if avg_vol > 0 else 1.0
        
        # 1. 放量不涨: 量比>1.3, 涨跌在(-0.5, 1.5)
        if vol_ratio > 1.3 and -0.5 < chg < 1.5:
            vol_up.append({
                'sector': sector, 'chg_pct': chg, 'vol_ratio': vol_ratio,
                'vol': vol, 'avg_vol': avg_vol,
                'level': '🟢' if vol_ratio > 1.8 else '🟡'
            })
        
        # 2. 连续蓄力: 量比>1.0且连续2天
        if len(hist_vols) >= 2:
            prev_vols = hist_vols[:2]
            if vol_ratio > 1.0 and -1 < chg < 2:
                days_up = sum(1 for v in prev_vols if v > avg_vol * 0.8)
                if days_up >= 1:
                    accum.append({
                        'sector': sector, 'chg_pct': chg,
                        'vol_ratio': vol_ratio, 'days_accum': days_up+1
                    })
        
        # 3. 轮动启动: 涨幅>2% + 量比>1.2
        if chg > 2 and vol_ratio > 1.2:
            rotation.append({
                'sector': sector, 'chg_pct': chg,
                'vol_ratio': vol_ratio, 'amplitude': info['amplitude']
            })
    
    return sorted(vol_up, key=lambda x: -x['vol_ratio']), \
           sorted(accum, key=lambda x: -x['vol_ratio']), \
           sorted(rotation, key=lambda x: -x['chg_pct'])


def main():
    t0 = time.time()
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    
    print(f"🐉 刘彻 V1.0 ETF扫描启动 | {date_str} {now.strftime('%H:%M')}")
    
    out_dir = os.path.expanduser("~/memory/刘彻扫描")
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. 采集
    print("  ┣ 采集ETF数据...")
    etfs = fetch_etf_data()
    if not etfs:
        print("  ❌ 无ETF数据")
        return
    
    # 保存原始数据作为历史
    etf_save = {code: {k: v for k, v in info.items() if k != 'amplitude'} 
                for code, info in etfs.items()}
    with open(os.path.join(out_dir, f"etf_{date_str}.json"), 'w') as f:
        json.dump(etf_save, f, ensure_ascii=False)
    
    print(f"  ┃ 采集 {len(etfs)} 个ETF")
    
    # 2. 加载历史
    history = load_history(out_dir, etfs)
    
    # 3. 检测信号
    print("  ┣ 信号检测...")
    vol_up, accum, rotation = detect_signals(etfs, history)
    
    # 4. 生成报告
    report = [f"# 刘彻 V1.0 全板块扫描 | {date_str}\n"]
    
    # 最强/最弱 ETF
    sorted_etfs = sorted(etfs.items(), key=lambda x: -x[1]['chg_pct'])
    report.append(f"## 📊 ETF 方向 (TOP/BOTTOM 各5)\n")
    report.append("| 🟢 最强 | 涨跌 | 🔴 最弱 | 涨跌 |")
    report.append("|:--------|:---:|:--------|:---:|")
    for i in range(5):
        top_name = sorted_etfs[i][1]['sector']
        top_chg = sorted_etfs[i][1]['chg_pct']
        bot_name = sorted_etfs[-i-1][1]['sector']
        bot_chg = sorted_etfs[-i-1][1]['chg_pct']
        report.append(f"| {top_name} | **{top_chg:+.1f}%** | {bot_name} | **{bot_chg:+.1f}%** |")
    report.append("")
    
    # 放量不涨
    report.append(f"## 🕵️ 放量不涨 ({len(vol_up)}个)\n")
    if vol_up:
        report.append("| 板块 | 涨跌 | 量比 | 信号 |")
        report.append("|:----|:---:|:---:|:---:|")
        for s in vol_up[:10]:
            report.append(f"| {s['sector']} | {s['chg_pct']:+.1f}% | {s['vol_ratio']:.1f}x | {s['level']} |")
        report.append(f"\n> 放量不涨=主力暗中建仓。跟踪1-3日后爆发。")
    else:
        report.append("无放量不涨信号。\n")
    
    # 连续蓄力
    report.append(f"\n## 📈 连续蓄力 ({len(accum)}个)\n")
    if accum:
        report.append("| 板块 | 涨跌 | 量比 | 蓄力天数 |")
        report.append("|:----|:---:|:---:|:------:|")
        for s in accum[:8]:
            report.append(f"| {s['sector']} | {s['chg_pct']:+.1f}% | {s['vol_ratio']:.1f}x | {s['days_accum']}天 |")
    else:
        report.append("无连续蓄力信号。\n")
    
    # 轮动启动
    report.append(f"\n## 🚀 轮动启动 ({len(rotation)}个)\n")
    if rotation:
        report.append("| 板块 | 涨幅 | 量比 | 振幅 |")
        report.append("|:----|:---:|:---:|:---:|")
        for s in rotation[:10]:
            amp = f"{s['amplitude']:.1f}%" if s.get('amplitude') else '-'
            report.append(f"| {s['sector']} | **{s['chg_pct']:+.1f}%** | {s['vol_ratio']:.1f}x | {amp} |")
    else:
        report.append("无板块轮动启动信号。\n")
    
    # 写入
    out_path = os.path.join(out_dir, f"{date_str}.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    elapsed = time.time() - t0
    print(f"  ┗ ✅ 完成 | {elapsed:.1f}s → {out_path}")
    print(f"\n📋 刘彻摘要:")
    print(f"  放量不涨: {len(vol_up)}个")
    print(f"  连续蓄力: {len(accum)}个")
    print(f"  轮动启动: {len(rotation)}个")
    
    if vol_up:
        top = vol_up[0]
        print(f"\n🦁 最高优先级: {top['sector']} 量比{top['vol_ratio']:.1f}x 涨{top['chg_pct']:+.1f}%")


if __name__ == '__main__':
    main()
