#!/usr/bin/env python3
"""关键词实时监控 - LEO盯盘系统"""
import requests, json, time

# 监控关键词组
WATCH_WORDS = {
    "稀土": ["稀土", "永磁", "磁材"],
    "制裁": ["制裁", "禁令", "出口管制", "限制出口"],
    "政策": ["降准", "降息", "印花税", "政治局"],
    "地缘": ["伊朗", "霍尔木兹", "美伊", "中东"],
    "科技": ["华为", "芯片", "半导体", "AI", "人工智能"],
    "游戏": ["版号", "游戏", "异环", "完美世界"],
    "异动": ["涨价", "断供", "囤货", "紧缺"],
}

def check_news():
    url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=20"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        items = data.get("result", {}).get("data", [])
        alerts = []
        for item in items:
            title = item.get("title", "")
            ctime = int(item.get("ctime", 0))
            for category, keywords in WATCH_WORDS.items():
                for kw in keywords:
                    if kw in title:
                        alerts.append({
                            "time": time.strftime("%H:%M", time.localtime(ctime)),
                            "category": category,
                            "title": title
                        })
                        break
        return alerts
    except:
        return []

if __name__ == "__main__":
    alerts = check_news()
    for a in alerts:
        print(f'[{a["time"]}] [{a["category"]}] {a["title"]}')
    if not alerts:
        print("暂无匹配的关键词新闻")
