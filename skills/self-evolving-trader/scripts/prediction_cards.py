#!/usr/bin/env python3
"""
汉武帝 · 预判卡生成器 v1.0
基于经验库模式库，自动为持仓生成预判卡
"""
import subprocess, re

PATTERNS = {
    "游资出货": {
        "trigger": lambda s: s.get('name') == '晶方科技' and True,
        "prediction": lambda s: {
            "方向": "冲高回落",
            "区间": f"{s['prev']*0.98:.1f}-{s['prev']*1.03:.1f}",
            "时间窗口": "早盘冲高，午盘回落",
            "依据": "模式1：昨量比14游资建仓→次日出货",
            "触发": f"到{s['prev']*1.03:.2f}卖一半",
            "失效": f"破{s['prev']*0.96:.2f}全出"
        }
    },
    "隔夜蓄力": {
        "trigger": lambda s: -1 < s.get('chg', 0) < 1.5 and s.get('net', 0) > -10000,
        "prediction": lambda s: {
            "方向": "震荡蓄力",
            "区间": f"{s['prev']*0.98:.1f}-{s['prev']*1.02:.1f}",
            "时间窗口": "全天",
            "依据": "模式6：低波蓄力，次日可能爆发",
            "触发": "尾盘确认收在此区间→隔夜观察池",
            "失效": f"破{s['prev']*0.97:.2f}止损"
        }
    },
    "AMD映射压力": {
        "trigger": lambda s: s.get('name') == '通富微电' and True,
        "prediction": lambda s: {
            "方向": "低开后修复",
            "区间": f"{s['prev']*0.96:.1f}-{s['prev']*1.01:.1f}",
            "时间窗口": "早盘承压，午盘修复",
            "依据": "模式3：AMD-3%→通富传导-2~4%",
            "触发": "回63+考虑减仓",
            "失效": "破61.00止损"
        }
    },
    "独立走强": {
        "trigger": lambda s: s.get('chg', 0) > 0.5 and s.get('net', 0) > 5000,
        "prediction": lambda s: {
            "方向": "独立走强",
            "区间": f"{s['price']*0.97:.1f}-{s['price']*1.05:.1f}",
            "时间窗口": "午盘持续",
            "依据": "模式12：全仓唯一翻红外>内，独立资金驱动",
            "触发": "尾盘确认外>内持续→可持有",
            "失效": f"破{s['price']*0.96:.2f}止损"
        }
    }
}

def generate_prediction_cards():
    """为当前持仓生成预判卡"""
    # 获取数据
    codes = "sh600353,sh603005,sz002624,sz002156,sz000938"
    raw = subprocess.run(
        ['curl', '-s', '--noproxy', '*', f'https://qt.gtimg.cn/q={codes}'],
        capture_output=True, timeout=10
    ).stdout.decode('gb2312', errors='replace')
    
    stocks = {}
    for m in re.finditer(r'v_\w+="(.*?)"', raw):
        p = m.group(1).split('~')
        if len(p) < 10: continue
        try:
            code = p[2]; name = p[1]
            stocks[code] = {
                'name': name, 'price': float(p[3]), 'prev': float(p[4]),
                'chg': round((float(p[3])-float(p[4]))/float(p[4])*100, 2),
                'outer': int(p[7]) if p[7].lstrip('-').isdigit() else 0,
                'inner': int(p[8]) if p[8].lstrip('-').isdigit() else 0,
                'net': (int(p[7]) if p[7].lstrip('-').isdigit() else 0) - (int(p[8]) if p[8].lstrip('-').isdigit() else 0)
            }
        except: continue
    
    for code, s in stocks.items():
        print(f"\n📋 {s['name']}({code}): 现价{s['price']:.2f}({s['chg']:+.2f}%) 净{s['net']:+,}")
        matched = False
        for pname, pdef in PATTERNS.items():
            if pdef['trigger'](s):
                pred = pdef['prediction'](s)
                print(f"  模式检测: {pname}")
                for k,v in pred.items():
                    print(f"  {k}: {v}")
                matched = True
                break
        if not matched:
            if s['chg'] < -4:
                print(f"  预判: ⚠️ 超跌，关注做T信号")
                print(f"  做T: 若企稳放量反弹 → 买新卖旧")
            else:
                print(f"  预判: 无明确模式匹配，持有观察")

if __name__ == '__main__':
    generate_prediction_cards()
