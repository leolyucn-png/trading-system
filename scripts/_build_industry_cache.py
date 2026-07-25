#!/usr/bin/env python3
"""
构建行业映射缓存 + 涨停分布
直接URL字符串方式(已验证可用)
"""
import requests, json, time, os, csv
from collections import Counter

HEADERS = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = "scripts"
os.makedirs(OUT_DIR, exist_ok=True)

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json()
    except: return None

# ============ Step 1: 获取行业列表(全量) ============
print("Step 1: 获取行业列表...")
url = "http://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=120&po=1&np=1&fields=f12,f14&fs=m:90+t:2"
data = fetch(url)
if data and data.get('data','').get('diff'):
    industries = data['data']['diff']
    print(f"  共{len(industries)}个行业")
    ind_list = [(i['f12'], i['f14']) for i in industries]
else:
    print("  获取行业列表失败"); exit(1)

# ============ Step 2: 获取成分股 ============
print("Step 2: 下载成分股...")
cache_file = os.path.join(OUT_DIR, "industry_map_v2.json")

if os.path.exists(cache_file):
    print("  缓存已存在, 跳过")
    with open(cache_file) as f: stock_to_industry = json.load(f)
else:
    stock_to_industry = {}
    for i, (ind_code, ind_name) in enumerate(ind_list):
        url = f"http://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=500&po=1&np=1&fields=f12,f14&fs=b:{ind_code}"
        data = fetch(url)
        if data and data.get('data','').get('diff'):
            for stock in data['data']['diff']:
                code = stock['f12'].zfill(6)
                stock_to_industry[code] = ind_name
        if (i+1) % 20 == 0:
            print(f"  进度{i+1}/{len(industries)} | {len(stock_to_industry)}只")
        time.sleep(0.15)
    
    with open(cache_file, 'w') as f:
        json.dump(stock_to_industry, f)
    print(f"  缓存保存: {len(stock_to_industry)}只")

ind_counts = Counter(stock_to_industry.values())
print(f"行业数: {len(ind_counts)} | 前10:")
for n, c in ind_counts.most_common(10):
    print(f"  {n}: {c}只")

# ============ Step 3: 涨停分布(全市场采样) ============
print("\nStep 3: 涨停分布采样...")
zt_file = os.path.join(OUT_DIR, "zt_distribution.csv")

if os.path.exists(zt_file):
    print("  ZT分布缓存存在")
else:
    daily_zt = []
    # 每月取5天采样(5,10,15,20,25日), 约120个样本
    for year in [2024, 2025]:
        for month in range(1, 13):
            for day in [5, 10, 15, 20, 25]:
                date_str = f"{year}{month:02d}{day:02d}"
                url = f"http://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=500&po=1&np=1&fields=f12,f14,f3&fs=m:90+t:3"
                data = fetch(url)
                if data and data.get('data','').get('diff'):
                    zt_count = len(data['data']['diff'])
                    daily_zt.append({"date": f"{year}-{month:02d}-{day:02d}", "zt_count": zt_count})
                time.sleep(0.2)
                if (month*5 + day) % 30 == 0:
                    print(f"  进度: {year}-{month:02d}")
    
    with open(zt_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['date','zt_count'])
        w.writeheader(); w.writerows(daily_zt)

import pandas as pd
zt_df = pd.read_csv(zt_file)
c = zt_df['zt_count']
print(f"\n涨停分布 ({len(zt_df)}个采样日):")
print(f"  中位数: {c.median():.0f}")
print(f"  均值: {c.mean():.0f}")
print(f"  P25: {c.quantile(0.25):.0f} | P75: {c.quantile(0.75):.0f}")
print(f"  P90: {c.quantile(0.90):.0f}")
print(f"  涨停≥60: {(c>=60).mean()*100:.0f}%")
print(f"  涨停≥100: {(c>=100).mean()*100:.0f}%")
print(f"  涨停≥30: {(c>=30).mean()*100:.0f}%")

print("\n✅ 缓存构建完成")
