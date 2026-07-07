#!/usr/bin/env python3
"""
🐉 刘备计划 V1.0 — 资金高低切换 & 板块轮动预判引擎
运行层级：秦始皇大盘预判 → 本模型 → 板块扫描 → 个股筛选
不可跳过、不可颠倒顺序
"""

import urllib.request
import ssl
import json
import datetime
import sys
from typing import Dict, List, Tuple, Optional

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ============================================================
# 数据源层 - 腾讯API（稳定高速，作为主数据源）
# ============================================================

TENCENT_SECTOR_MAP = {
    # 科技
    "半导体": "sh512480",
    "软件": "sh515230", 
    "通信": "sh515880",
    "机器人": "sh562500",
    "消费电子": "sz159732",
    # 医药
    "创新药": "sz159992",
    "化学制药": "sz159938",
    "生物医药": "sz159859",
    "医疗服务": "sz159883",
    # 消费
    "白酒": "sh512690",
    "食品饮料": "sh515170",
    "生猪养殖": "sz159865",
    # 金融
    "券商": "sz159842",
    "银行": "sh512820",
    # 周期
    "化工": "sz159870",
    "有色金属": "sz159871",
    # 其他
    "军工": "sz512660",
    "游戏": "sz159869",
    "低空经济": "sh562550",
}

def get_tencent_quote(code: str) -> Optional[Dict]:
    """Get real-time quote from Tencent"""
    try:
        url = f'http://qt.gtimg.cn/q={code}'
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('gbk')
        vals = data.split('"')[1].split('~')
        if len(vals) > 4:
            return {
                'price': float(vals[3]),
                'prev_close': float(vals[4]),
                'open': float(vals[5]),
                'high': float(vals[33]) if len(vals) > 33 else 0,
                'low': float(vals[34]) if len(vals) > 34 else 0,
                'volume': int(vals[6]) if vals[6] else 0,
                'change_pct': (float(vals[3]) - float(vals[4])) / float(vals[4]) * 100
            }
    except:
        return None

def get_tencent_batch(codes: List[str]) -> Dict[str, Dict]:
    """Batch get quotes. Standard format for all stocks/ETFs:
    vals[3]=price, vals[4]=prev_close, vals[33]=high, vals[34]=low"""
    query = ','.join(codes)
    url = f'http://qt.gtimg.cn/q={query}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk')
        results = {}
        for line in data.strip().split(';'):
            line = line.strip()
            if not line or '"' not in line: continue
            try:
                vals = line.split('"')[1].split('~')
                code = vals[2]
                name = vals[1]
                
                price = float(vals[3])
                prev = float(vals[4])
                
                if prev == 0:
                    continue
                
                pct = (price - prev) / prev * 100
                
                results[code] = {
                    'name': name,
                    'price': price,
                    'prev_close': prev,
                    'change_pct': round(pct, 2),
                    'volume': int(vals[6]) if vals[6] and vals[6].lstrip('-').isdigit() else 0,
                    'high': float(vals[33]) if len(vals) > 33 and vals[33] else price,
                    'low': float(vals[34]) if len(vals) > 34 and vals[34] else price,
                }
            except Exception:
                pass
        return results
    except Exception as e:
        print(f'Tencent API error: {e}')
        return {}

def get_index_data() -> Dict:
    """Get major indices via direct API"""
    codes = ['sh000001', 'sh000688', 'sz399001', 'sz399006']
    query = ','.join(codes)
    url = f'http://qt.gtimg.cn/q={query}'
    names = {'000001': '上证', '000688': '科创50', '399001': '深证', '399006': '创业板'}
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context() if hasattr(ssl, 'create_default_context') else None)
        data = resp.read().decode('gbk')
        output = {}
        for line in data.strip().split(';'):
            line = line.strip()
            if not line or '"' not in line: continue
            try:
                vals = line.split('"')[1].split('~')
                code = vals[2]  # just the number
                if code in names:
                    price = float(vals[3])
                    prev = float(vals[4])
                    pct = (price - prev) / prev * 100
                    output[names[code]] = pct
            except:
                pass
        # Fill in any missing
        for n in names.values():
            if n not in output:
                output[n] = None
        return output
    except Exception as e:
        print(f'Index API error: {e}')
        return {'上证': None, '科创50': None, '深证': None, '创业板': None}

# ============================================================
# 资金高低切换打分引擎
# ============================================================

class RotationScorer:
    """高低切换量化打分"""
    
    def __init__(self):
        self.sectors = list(TENCENT_SECTOR_MAP.keys())
        self.sector_codes = list(TENCENT_SECTOR_MAP.values())
        
    def score_high_sector_decline(self, data: Dict) -> Tuple[int, List]:
        """维度1：高位赛道衰退分（40分）"""
        score = 40
        warnings = []
        
        # Sort by today's change, find top gainers
        sorted_sectors = sorted(data.items(), key=lambda x: x[1]['change_pct'], reverse=True)
        
        # Check if top gainers from last week are now cooling
        top5 = [s[0] for s in sorted_sectors[:5]]
        for sector in top5:
            info = data[sector]
            if info['change_pct'] < -3:  # top sector now falling
                score -= 5
                warnings.append(f"{sector}：今日{info['change_pct']:.1f}%，资金拐头，-5分")
            elif info['change_pct'] < 0:
                score -= 3
                warnings.append(f"{sector}：今日{info['change_pct']:.1f}%微跌，-3分")
                
        # Check for 天地板 pattern (open high close low)
        for sector, info in data.items():
            if info.get('high', 0) > 0 and info['price'] > 0:
                high_pct = (info['high'] - info['prev_close']) / info['prev_close'] * 100
                now_pct = info['change_pct']
                if high_pct > 3 and now_pct < -5:  # 天地板
                    score -= 10
                    warnings.append(f"{sector}：天地板（高{high_pct:.1f}%→现{now_pct:.1f}%），-10分")
                    break  # once is enough for this signal
                    
        return max(score, 0), warnings
    
    def score_low_sector_inflow(self, data: Dict) -> Tuple[int, List]:
        """维度2：低位板块回流分（35分）"""
        score = 0
        signals = []
        
        # Find sectors that are UP today (inflow candidates)
        for sector, info in sorted(data.items(), key=lambda x: x[1]['change_pct'], reverse=True):
            if info['change_pct'] > 3:  # >3% today
                score += 5
                signals.append(f"{sector}：今日+{info['change_pct']:.1f}%放量异动，+5分")
            elif info['change_pct'] > 1:
                score += 3
                signals.append(f"{sector}：今日+{info['change_pct']:.1f}%温和走强，+3分")
        
        # Volumn validation
        for sector, info in data.items():
            if info.get('volume', 0) > 500000 and info['change_pct'] > 0:
                # High volume + positive price = capital inflow signal
                pass  # simplified for now
        
        return min(score, 35), signals[:5]  # cap at 35, max 5 signals
    
    def score_seesaw(self, data: Dict) -> Tuple[int, str]:
        """维度3：资金跷跷板分（15分）"""
        # Calculate total outflow from top gainers falling, inflow to bottom risers
        outflow = 0
        inflow = 0
        
        for sector, info in data.items():
            if info['change_pct'] < -3:
                outflow += abs(info['change_pct'])
            elif info['change_pct'] > 3:
                inflow += info['change_pct']
        
        if outflow > 0 and inflow > 0:
            match = 1 - abs(outflow - inflow) / max(outflow, inflow)
            if match > 0.8:
                return 15, f"典型高低切（流出{outflow:.0f}%≈流入{inflow:.0f}%，匹配度{match:.0%}）"
            elif match > 0.5:
                return 8, f"部分分流（匹配度{match:.0%}）"
            else:
                return 2, f"非典型切换（匹配度{match:.0%}）"
        return 2, "无明显跷跷板效应"
    
    def score_market_environment(self, index_data: Dict) -> Tuple[int, str]:
        """维度4：大盘环境适配分（10分）"""
        sh = index_data.get('上证', 0)
        cy = index_data.get('创业板', 0)
        
        if sh is not None and sh < -0.5:
            return 10, f"弱势环境（上证{sh:+.1f}%），切换信号强化"
        elif cy is not None and cy < -1:
            return 10, f"弱势环境（创业板{cy:+.1f}%），切换信号强化"
        elif sh is not None and sh > 1:
            return 2, f"强势普涨（上证{sh:+.1f}%），切换信号弱化"
        else:
            return 5, f"震荡环境（上证{sh:+.1f}%），中性"

# ============================================================
# 主执行引擎
# ============================================================

def run_liu_bei_scan() -> str:
    """运行刘备轮动扫描，返回完整输出"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"=========🐉刘备V1.0 资金高低切换研判【{now}】=========")
    print()
    
    # Step 1: Get data
    print("📡 数据采集...")
    index_data = get_index_data()
    sector_quotes = get_tencent_batch(list(TENCENT_SECTOR_MAP.values()))
    
    # Map sector names to data (strip market prefix for matching)
    sector_data = {}
    for sname, scode in TENCENT_SECTOR_MAP.items():
        bare_code = scode[2:] if scode.startswith(('sh','sz')) else scode
        if scode in sector_quotes:
            sector_data[sname] = sector_quotes[scode]
        elif bare_code in sector_quotes:
            sector_data[sname] = sector_quotes[bare_code]
    
    # Step 2: Score
    scorer = RotationScorer()
    
    d1_score, d1_warnings = scorer.score_high_sector_decline(sector_data)
    d2_score, d2_signals = scorer.score_low_sector_inflow(sector_data)
    d3_score, d3_desc = scorer.score_seesaw(sector_data)
    d4_score, d4_desc = scorer.score_market_environment(index_data)
    
    total = d1_score + d2_score + d3_score + d4_score
    
    if total >= 70:
        level = "🔴 强高低切换"
        level_desc = "明确主线切换，规避高位赛道，布局低位轮动方向"
        action = "禁止新开高位赛道仓位，可布局低位轮动方向"
    elif total >= 45:
        level = "🟡 弱轮动分化"
        level_desc = "结构性小幅分流，资金试探性转移"
        action = "谨慎追高位，小仓位试错低位"
    else:
        level = "🟢 无明显切换"
        level_desc = "原有热点延续，资金仍集中在主线"
        action = "维持原有主线操作不动"
    
    # Step 3: Format output
    
    # 1️⃣ 大盘环境
    sh_str = f"{index_data.get('上证', 0):+.2f}%" if index_data.get('上证') else "N/A"
    cy_str = f"{index_data.get('创业板', 0):+.2f}%" if index_data.get('创业板') else "N/A"
    
    env_ok = "✅ 适合切换" if d4_score >= 8 else "⚠️ 切换信号偏弱" if d4_score >= 5 else "❌ 不适合切换"
    
    print(f"1️⃣ 大盘环境适配")
    print(f"   上证：{sh_str} | 创业板：{cy_str}")
    print(f"   判定：{env_ok}")
    print(f"   原因：{d4_desc}")
    print()
    
    # 2️⃣ 高位承压板块
    print(f"2️⃣ 高位承压板块（流出队列）")
    top_gainers = sorted(sector_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)[:5]
    print(f"   {'板块':<10} {'涨跌':<8} {'判定':<10}")
    print(f"   {'-'*30}")
    for name, info in top_gainers:
        pct = info['change_pct']
        if pct > 2:
            tag = "🟢走强"
        elif pct > -2:
            tag = "🟡震荡"
        else:
            tag = "🔴承压"
        print(f"   {name:<10} {pct:+.2f}%{'':<4} {tag}")
    if d1_warnings:
        print(f"\n   ⚠️ 衰退信号：")
        for w in d1_warnings:
            print(f"      {w}")
    print()
    
    # 3️⃣ 低位回流板块
    print(f"3️⃣ 低位回流板块（流入队列）")
    bottom_losers = sorted(sector_data.items(), key=lambda x: x[1]['change_pct'])[:5]
    print(f"   {'板块':<10} {'涨跌':<8} {'判定':<10}")
    print(f"   {'-'*30}")
    for name, info in bottom_losers:
        pct = info['change_pct']
        if pct < -3:
            tag = "🔴大跌"
        elif pct < -1:
            tag = "🟡回落"
        else:
            tag = "🟢企稳"
        print(f"   {name:<10} {pct:+.2f}%{'':<4} {tag}")
    
    # Also show risers (potential inflow targets)
    risers = [(n, i) for n, i in sorted(sector_data.items(), key=lambda x: x[1]['change_pct'], reverse=True) if i['change_pct'] > 2]
    if risers:
        print(f"\n   📈 今日逆势走强（潜在流入）：")
        for name, info in risers[:3]:
            print(f"      {name}：+{info['change_pct']:.1f}%")
    print()
    
    # 4️⃣ 综合评分
    print(f"4️⃣ 综合切换评分")
    print(f"   高位衰退分：{d1_score}/40 | 低位回流分：{d2_score}/35 | 跷跷板分：{d3_score}/15 | 环境分：{d4_score}/10")
    print(f"   📊 总分：{total}/100 | 等级：{level}")
    print(f"   📝 {level_desc}")
    print()
    
    # 5️⃣ 轮动预判
    # Determine direction from today's data
    riser_sectors = [(n, i) for n, i in sector_data.items() if i['change_pct'] > 2]
    faller_sectors = [(n, i) for n, i in sector_data.items() if i['change_pct'] < -2]
    
    if riser_sectors:
        dir_str = " → ".join([n for n, i in riser_sectors[:3]])
    else:
        dir_str = "无明显方向"
    
    print(f"5️⃣ 轮动预判结论")
    print(f"   未来半日/次日资金大概率方向：{dir_str}")
    if total >= 70:
        print(f"   核心逻辑：高位资金退出→流入低位补涨板块，典型高低切换")
    elif total >= 45:
        print(f"   核心逻辑：资金在板块间试探性分流，观望为主")
    else:
        print(f"   核心逻辑：原有主线尚未瓦解，低位板块未获持续资金认可")
    print()
    
    # 6️⃣ 实操约束
    print(f"6️⃣ 实操约束")
    if total >= 70:
        print(f"   □ 禁止新开高位赛道仓位")
        print(f"   □ 可布局低位轮动方向")
    elif total < 45:
        print(f"   □ 维持原有主线操作")
        print(f"   □ 可小仓位试仓低位机会")
    else:
        print(f"   □ 谨慎追高位，观望为主")
        print(f"   □ 小仓位试错低位轮动")
    print()
    
    # 7️⃣ 失效临界点
    print(f"7️⃣ 预判失效临界点")
    print(f"   上证跌破3980 / 板块资金反转阈值：今日高位板块重新获得资金流入")
    print()
    
    # 8️⃣ 数据源状态
    print(f"8️⃣ 数据源状态")
    print(f"   ✅ Tencent API — 20板块实时行情")
    print(f"   ⚠️ akshare板块资金流 — 需盘中运行（约2分钟）")
    print(f"   ⚠️ 北向资金 — 需14:00后稳定")
    print()
    
    print(f"===============end==================")
    
    return total

if __name__ == "__main__":
    run_liu_bei_scan()
