import requests
import json

# Full list of candidate bull stocks to check
stocks = [
    ('sz002931', '锋龙股份'),
    ('sz002716', '湖南白银'),
    ('sh603629', '利通电子'),
    ('sz002297', '博云新材'),
    ('sh603773', '沃格光电'),
    ('sh600353', '旭光电子'),
    ('sh600171', '上海贝岭'),
    ('sh600460', '士兰微'),
    ('sh600206', '有研新材'),
    ('sh603005', '晶方科技'),
    ('sz002156', '通富微电'),
    ('sz002747', '埃斯顿'),
    ('sh601162', '天风证券'),
    ('sh600428', '中远海特'),
    ('sh600884', '杉杉股份'),
    ('sh601137', '博威合金'),
    ('sz002409', '雅克科技'),
    ('sz000670', '盈方微'),
]

print("=== 历史6个月 K线数据验证 ===")
print()

for code, name in stocks:
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={},day,,,120,qfq".format(code)
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if 'data' in data and code in data['data']:
            days = data['data'][code].get('qfqday', [])
            if not days:
                days = data['data'][code].get('day', [])
            
            if len(days) >= 30:
                # Best 30-day window
                best_30d_change = 0
                best_start = ''
                best_end = ''
                
                for i in range(len(days) - 30):
                    window = days[i:i+30]
                    start_close = float(window[0][2])
                    end_close = float(window[-1][2])
                    change = (end_close - start_close) / start_close * 100
                    if change > best_30d_change:
                        best_30d_change = change
                        best_start = window[0][0]
                        best_end = window[-1][0]
                
                # Count limit-ups in last 60 days
                best_window = days[-60:] if len(days) >= 60 else days
                limit_ups = 0
                for d in best_window:
                    c = float(d[2])  # close
                    o = float(d[1])  # open
                    daily_change = (c - o) / o * 100
                    if daily_change >= 9.0:
                        limit_ups += 1
                
                last = days[-1]
                curr_price = float(last[2])
                
                status = "✅" if best_30d_change > 50 and limit_ups >= 3 else "❌"
                
                print("{} {}:".format(code, name))
                print("  最佳30日涨幅: {:.1f}% ({}~{})".format(best_30d_change, best_start, best_end))
                print("  近60日涨停次数: {}".format(limit_ups))
                print("  现价: {}".format(curr_price))
                print("  判定: {} 30日涨{:.0f}% | 涨停{}次".format(status, best_30d_change, limit_ups))
                
                # Recent 10 days trend
                recent = days[-10:]
                trend_parts = ["{}:{}".format(d[0][5:], d[2]) for d in recent]
                print("  近10日: {}".format(", ".join(trend_parts)))
                print()
            else:
                print("{} {}: 数据不足{}天".format(code, name, len(days)))
                print()
    except Exception as e:
        print("{} {}: 失败 - {}".format(code, name, str(e)[:60]))
        print()
