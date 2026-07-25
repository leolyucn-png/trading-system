#!/usr/bin/env python3
"""
汉武帝计划 - 早盘扫描 (v2.1 去akshare版)
用Sina+EastMoney直接API，零akshare依赖
"""
import requests
import json
import re
from datetime import datetime

TIMEOUT = 8
HEADERS_SINA = {'Referer': 'http://finance.sina.com.cn'}

now = datetime.now()
print("=" * 60)
print(f"🦁 汉武帝早盘扫描 | {now.strftime('%Y-%m-%d %H:%M')}")
print("=" * 60)

# ============================================================
# 1. 大盘实时行情 (Sina)
# ============================================================
print("\n【1】📊 大盘指数行情")
INDEX_CODES = {
    '上证指数': 's_sh000001',
    '深证成指': 's_sz399001',
    '创业板指': 's_sz399006',
    '科创50': 's_sh000688',
    '沪深300': 's_sh000300',
}
try:
    r = requests.get(f'http://hq.sinajs.cn/list={",".join(INDEX_CODES.values())}',
                     headers=HEADERS_SINA, timeout=TIMEOUT)
    r.encoding = 'gbk'
    for line in r.text.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('"')
        if len(parts) < 2:
            continue
        fields = parts[1].split(',')
        if len(fields) < 5:
            continue
        # Find which index
        for name, code in INDEX_CODES.items():
            if code in line:
                # 指数格式: [0]=名称 [1]=当前价 [2]=涨跌额 [3]=涨跌幅%
                price = float(fields[1]) if fields[1] else 0
                pct = float(fields[3]) if fields[3] else 0
                amount = fields[5] if len(fields) > 5 else '?'
                emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
                print(f"  {emoji} {name}: {price:.2f}  ({pct:+.2f}%)  成交额: {amount}")
                break
except Exception as e:
    print(f"  ⚠️ Sina指数获取失败: {e}")

# ============================================================
# 2. 市场情绪 - 涨跌停 (EastMoney)
# ============================================================
print("\n【2】🌡️ 市场情绪")
try:
    # 涨停池
    today_str = now.strftime('%Y%m%d')
    em_url = f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3&fs=b:DLMJ0101&fields=f2,f3,f4,f12,f14,f15,f16,f17,f20&_={int(now.timestamp()*1000)}'
    r = requests.get(em_url, timeout=TIMEOUT)
    data = r.json()
    if data.get('data') and data['data'].get('diff'):
        zt_list = data['data']['diff']
        print(f"  今日涨停: {len(zt_list)} 家")
        for item in zt_list[:10]:
            print(f"    ✅ {item.get('f14','?')}({item.get('f12','?')}) "
                  f"最新:{item.get('f2','?')} 涨幅:{item.get('f3','?')}%")
    else:
        print(f"  涨停数据: 暂无")
except Exception as e:
    print(f"  涨停数据获取失败: {e}")

# 跌停
try:
    em_dt_url = f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3&fs=b:DLMJ0102&fields=f2,f3,f4,f12,f14&_={int(now.timestamp()*1000)}'
    r = requests.get(em_dt_url, timeout=TIMEOUT)
    data = r.json()
    if data.get('data') and data['data'].get('diff'):
        print(f"  今日跌停: {len(data['data']['diff'])} 家")
        for item in data['data']['diff'][:5]:
            print(f"    💀 {item.get('f14','?')}({item.get('f12','?')}) 跌幅:{item.get('f3','?')}%")
    else:
        print(f"  今日跌停: 0 家")
except Exception as e:
    print(f"  跌停数据获取失败: {e}")

# ============================================================
# 3. 核心持仓监测 - 上海贝岭(600171)
# ============================================================
print("\n【3】🎯 核心持仓监测")
holdings = ['sh600171', 'sh600316', 'sh600487', 'sh600288']
# 600171=贝岭, 600316=洪都, 600487=亨通, 600288=大恒
try:
    r = requests.get(f'http://hq.sinajs.cn/list={",".join(holdings)}',
                     headers=HEADERS_SINA, timeout=TIMEOUT)
    r.encoding = 'gbk'
    for line in r.text.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('"')
        if len(parts) < 2:
            continue
        fields = parts[1].split(',')
        if len(fields) < 10:
            continue
        name = fields[0]
        code = line.split('=')[0].split('_')[-1] if '=' in line else '?'
        open_p = float(fields[1]) if fields[1] else 0
        prev = float(fields[2]) if fields[2] else 0
        price = float(fields[3]) if fields[3] else 0
        high = float(fields[4]) if fields[4] else 0
        low = float(fields[5]) if fields[5] else 0
        amount = float(fields[8]) if len(fields) > 8 and fields[8] else 0
        pct = (price - prev) / prev * 100 if prev > 0 else 0
        
        emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
        print(f"  {emoji} {name}({code}) 开:{open_p:.2f} 现:{price:.2f} ({pct:+.2f}%)")
        print(f"    昨收:{prev:.2f} 高:{high:.2f} 低:{low:.2f} 成交额:{amount/1e8:.2f}亿")
except Exception as e:
    print(f"  ⚠️ 持仓数据获取失败: {e}")

# ============================================================
# 4. 行业资金流向 TOP5 (EastMoney)
# ============================================================
print("\n【4】💰 行业资金流向 (东财主力)")
try:
    # 东财行业资金流
    flow_url = f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2&fields=f2,f3,f4,f12,f14,f62,f66,f184&_={int(now.timestamp()*1000)}'
    r = requests.get(flow_url, timeout=TIMEOUT)
    data = r.json()
    if data.get('data') and data['data'].get('diff'):
        items = data['data']['diff']
        # Sort by main force net flow (f62)
        sorted_items = sorted(items, key=lambda x: x.get('f62', 0) or 0, reverse=True)
        print(f"  今日行业主力净流入 TOP5:")
        for item in sorted_items[:5]:
            net = (item.get('f62') or 0) / 1e8
            pct = item.get('f3') or 0
            print(f"    💵 {item.get('f14','?')}: +{net:.2f}亿 涨幅:{pct}%")
        print(f"  今日行业主力净流出 TOP3:")
        for item in sorted_items[-3:]:
            net = (item.get('f62') or 0) / 1e8
            pct = item.get('f3') or 0
            print(f"    📉 {item.get('f14','?')}: {net:.2f}亿 涨幅:{pct}%")
    else:
        print(f"  资金流数据: 暂未更新")
except Exception as e:
    print(f"  ⚠️ 资金流获取失败: {e}")

# ============================================================
# 5. 昨夜外盘信号 (Sina美股)
# ============================================================
print("\n【5】🔭 外盘参考")
US_INDICES = {
    '道琼斯': 'gb_dji',
    '纳斯达克': 'gb_ixic',
    '标普500': 'gb_inx',
}
try:
    r = requests.get(f'http://hq.sinajs.cn/list={",".join(US_INDICES.values())}',
                     headers=HEADERS_SINA, timeout=TIMEOUT)
    r.encoding = 'gbk'
    for line in r.text.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('"')
        if len(parts) < 2:
            continue
        fields = parts[1].split(',')
        if len(fields) < 5:
            continue
        for name, code in US_INDICES.items():
            if code in line:
                price = float(fields[1]) if fields[1] else 0
                pct_str = fields[2] if len(fields) > 2 else '0'
                pct = float(pct_str.replace('%', '')) if pct_str else 0
                emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
                print(f"  {emoji} {name}: {price:.2f}  ({pct:+.2f}%)  时间:{fields[3] if len(fields)>3 else '?'}")
                break
except Exception as e:
    print(f"  ⚠️ 外盘数据获取失败: {e}")

# ============================================================
# 6. A股主要板块涨幅排序
# ============================================================
print("\n【6】📈 主要板块涨跌幅 (东财)")
SECTOR_CODES = [
    ('BK0483', '半导体'), ('BK2087', 'AI智能'), ('BK0716', '通信设备'),
    ('BK0596', '军工'), ('BK0472', '证券'), ('BK0477', '白酒'),
    ('BK0574', '新能源车'), ('BK0493', '医药'), ('BK0478', '银行'),
    ('BK0473', '保险'), ('BK0545', '光伏'), ('BK0475', '有色'),
    ('BK0466', '软件'), ('BK0736', '机器人'), ('BK0456', '云计算'),
    ('BK0480', '消费电子'), ('BK0481', '芯片'),
]
try:
    codes_str = ','.join([f'{c}' for c, _ in SECTOR_CODES])
    sec_url = f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=30&po=0&np=1&fltt=2&invt=2&fid=f3&fs=b:{codes_str}&fields=f2,f3,f4,f12,f14,f104,f105&_={int(now.timestamp()*1000)}'
    r = requests.get(sec_url, timeout=TIMEOUT)
    data = r.json()
    if data.get('data') and data['data'].get('diff'):
        items = data['data']['diff']
        sorted_items = sorted(items, key=lambda x: x.get('f3', 0) or 0, reverse=True)
        for item in sorted_items:
            pct = item.get('f3') or 0
            emoji = "🔴" if pct and pct > 0 else "🟢"
            print(f"  {emoji} {item.get('f14','?')}: {pct:+.2f}%")
    else:
        print(f"  板块数据: 暂未获取")
except Exception as e:
    print(f"  ⚠️ 板块数据获取失败: {e}")

print("\n" + "=" * 60)
print("✅ 汉武帝早盘扫描完成 | v2.1 零akshare")
print("=" * 60)
