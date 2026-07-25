#!/usr/bin/env python3
"""诸葛亮 · 20+板块长期票扫描"""
import requests

# 20+板块全覆盖
sectors = {
    '半导体': 'sz002049,sh600171,sh600460,sh600584,sz002185,sz002156,sz300661',
    '芯片设计': 'sh603501,sh688385,sh688981,sz300782,sz300672',
    '消费电子': 'sz000725,sz002475,sh603005,sz002241,sz300433,sh601138',
    '医药': 'sh600276,sz300760,sh600196,sz000538,sz300015,sz300347',
    '创新药': 'sh600216,sh600267,sz300122,sh688180,sh600079',
    '医疗器械': 'sz300760,sh688016,sz300003,sh600529,sz300633',
    'AI/算力': 'sz000977,sz002410,sz002230,sh603019,sz300624,sh603236',
    '通信': 'sh600941,sz000063,sz300394,sz300308,sh600498',
    '云计算': 'sz300454,sh688111,sz300442,sh600588,sh688568',
    '软件': 'sz002230,sz300033,sz300496,sh603171,sh688318',
    '储能': 'sz300750,sz300274,sz002074,sh600438,sz300763',
    '光伏': 'sh601012,sz002459,sz300274,sh600438,sz300724',
    '新能源车': 'sz002594,sz300750,sz002460,sh600104,sz002466',
    '机器人': 'sz002747,sz002527,sh601689,sz300124,sh688165,sz300660',
    '人形机器人': 'sz002050,sz002747,sh601689,sz300124,sh688017,sz002472,sh601100',
    '军工': 'sh600760,sh600893,sz000768,sh600038,sz002013,sh600185',
    '航天': 'sh600879,sh600118,sz002025,sh600391,sh603698',
    '化工': 'sh600309,sz002709,sh600352,sh600141,sz300409',
    '有色': 'sh601899,sh600362,sh600547,sz000630,sh600489',
    '钢铁': 'sh600019,sh600010,sh600808,sz000708,sh600022',
    '基建': 'sh601668,sh601800,sh600039,sh601186,sh601390',
    '地产': 'sz000002,sh600048,sh600383,sh600606,sz001979',
    '银行': 'sh601398,sh601939,sh601288,sh600036,sh601166',
    '证券': 'sh600030,sh601211,sh600837,sh601995,sz002736',
    '游戏': 'sz002624,sh603444,sz300315,sz300459,sz002555,sh603258',
    '传媒': 'sz300058,sz002400,sh601858,sz300251,sz300413',
    '食品饮料': 'sh600519,sh000858,sh600887,sz002304,sh603288',
    '家电': 'sz000333,sh600690,sh600839,sz002242,sh603486',
    '旅游': 'sz300144,sh600258,sh601888,sz000888,sh600706',
    '农业': 'sz002714,sh600598,sz000998,sh600737,sz300189',
    '煤炭': 'sh601088,sh600188,sh600546,sz000983,sh600348',
    '电力': 'sh600900,sh601985,sh600886,sz003816,sh600023',
}

# Fetch all
all_codes = []
for codes_str in sectors.values():
    for c in codes_str.split(','):
        c = c.strip()
        if c and len(c) > 5 and c not in all_codes:
            all_codes.append(c)

print(f'Total unique codes: {len(all_codes)}')
print()

def sina_query(codes):
    all_results = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        code_str = ','.join(batch)
        try:
            r = requests.get(
                f'http://hq.sinajs.cn/list={code_str}',
                headers={'Referer': 'http://finance.sina.com.cn'},
                timeout=8
            )
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    fields = line.split('"')[1].split(',')
                    if len(fields) < 6:
                        continue
                    code_raw = line.split('=')[0].split('_')[-1]
                    name = fields[0]
                    if 'ST' in name or '*ST' in name:
                        continue
                    px = float(fields[3])
                    prev = float(fields[2])
                    high = float(fields[4])
                    low = float(fields[5])
                    vol = int(float(fields[8]))
                    chg = (px - prev) / prev * 100
                    amp = (high - low) / prev * 100
                    amount = float(fields[9]) if len(fields) > 9 else 0
                    all_results[code_raw] = {
                        'name': name, 'px': px, 'chg': chg,
                        'vol': vol, 'amp': amp, 'amount': amount,
                    }
                except:
                    continue
        except:
            continue
    return all_results

import requests
all_data = sina_query(all_codes)

# Print by sector
total = 0
for sector_name, codes_str in sectors.items():
    items = []
    for c in codes_str.split(','):
        c = c.strip()
        if not c or len(c) < 5:
            continue
        code_key = c.split('.')[-1]
        info = all_data.get(code_key)
        if info:
            items.append(info)
    if items:
        total += 1
        # Show best 1-2 in each sector
        sorted_items = sorted(items, key=lambda x: abs(x['chg']))
        best = sorted_items[0]
        chg = best['chg']
        bar = 'RM' if chg > 5 else ('GR' if chg > 0 else ('RD' if chg > -2 else 'SK'))
        marker = 'RM' if chg > 5 else ('GR' if chg > 0 else ('RD' if chg > -2 else 'SK'))
        if marker == 'RM':
            m = 'RM'
        elif marker == 'GR':
            m = 'GR'
        elif marker == 'RD':
            m = 'RD'
        else:
            m = 'SK'
        # Show 1st and 2nd candidates
        first = sorted_items[0]
        second = sorted_items[1] if len(sorted_items) > 1 else None
        fwd = 'GR' if first['chg'] > 0 else ('YW' if first['chg'] < 0 else 'GR')
        print(f'{fwd} {sector_name:8s} | {first["name"]:10s} {first["px"]:.2f} {first["chg"]:+.2f}%', end='')
        if second:
            swd = 'GR' if second['chg'] > 0 else 'YW'
            print(f' | {second["name"]:10s} {second["px"]:.2f} {second["chg"]:+.2f}%')
        else:
            print()

print(f'\n总板块数: {total}')

# 诸葛亮DNA精选：横盘+方向对+市值合理
print()
print('=' * 65)
print('  诸葛亮DNA精选：今日<3% + 温和放量')
print('=' * 65)
print()

# 筛选今日不热不冷的
candidates = []
for code_key, info in all_data.items():
    if abs(info['chg']) < 3 and info['amp'] < 5 and info['vol'] > 10000:
        # 量太小的不要
        candidates.append(info)

# 按|涨跌幅|排序，最平的优先
candidates.sort(key=lambda x: abs(x['chg']))

for info in candidates[:25]:
    chg = info['chg']
    marker = 'GR' if chg > 0 else 'YW'
    print(f'{marker} {info["name"]:12s} {info["px"]:>8.2f}  {chg:>+6.2f}%  振幅{info["amp"]:.1f}%  量{info["vol"]//100:>6}手')
