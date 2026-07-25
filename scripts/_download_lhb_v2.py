#!/usr/bin/env python3
"""下载机构龙虎榜全量数据"""
import requests, json, os, time, csv, sys
sys.stdout.reconfigure(line_buffering=True)
os.makedirs('lhb_data_v2', exist_ok=True)
H = {"User-Agent": "Mozilla/5.0"}

def dl(yr, mo, page=1):
    ed = 30 if mo in [4,6,9,11] else (28 if mo==2 else 31)
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    fil = "(TRADE_DATE>='" + str(yr) + "-" + str(mo).zfill(2) + "-01')"
    fil += "(TRADE_DATE<='" + str(yr) + "-" + str(mo).zfill(2) + "-" + str(ed) + "')"
    params = {"reportName":"RPT_ORGANIZATION_TRADE_DETAILS","columns":"ALL",
              "filter":fil,"pageSize":5000,"pageNumber":page,
              "sortColumns":"TRADE_DATE,SECURITY_CODE","sortTypes":"-1,1",
              "source":"WEB","client":"WEB"}
    r = requests.get(url, params=params, headers=H, timeout=15)
    return r.json()

t = 0
for yr in [2024,2025]:
    for mo in range(1,13):
        fn = "lhb_data_v2/jg_" + str(yr) + str(mo).zfill(2) + ".csv"
        if os.path.exists(fn) and os.path.getsize(fn) > 100:
            with open(fn) as fh: t += len(fh.readlines()) - 1
            continue
        d = dl(yr, mo)
        if d.get("result") and d["result"].get("data"):
            items = d["result"]["data"]
            if items:
                with open(fn, "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(items[0].keys()))
                    w.writeheader()
                    w.writerows(items)
                t += len(items)
                print("  " + str(yr) + "-" + str(mo).zfill(2) + ": " + str(len(items)) + "条")
            else:
                print("  " + str(yr) + "-" + str(mo).zfill(2) + ": 空")
        else:
            msg = str(d.get("message","?"))
            print("  " + str(yr) + "-" + str(mo).zfill(2) + ": " + msg[:30])
        time.sleep(1.5)

print("\n总计: " + str(t) + "条")
