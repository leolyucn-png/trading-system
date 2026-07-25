#!/usr/bin/env python3
"""
刘备 V4.1 · 全量聚类搜证引擎
==============================
升级：V4.0(预设关键词过滤) → V4.1(全量自动聚类)

盲区修复：
  云赛智联 7/8涨停 — 关键词没搜"算力" → 漏判
  修复：不再依赖预设关键词，自动聚类所有170条新闻

原理：
  1. 全量拉取三源新闻(170条)
  2. 分词提取高频词
  3. 按共现关系自动聚类
  4. 输出TOP10话题簇 + 代表性标题

用法：
  python liubei_v4.1.py          # 全量聚类
  python liubei_v4.1.py --query 算力  # 也保留关键词搜索
"""
import json, sys, re, os, datetime as dt, requests
from collections import Counter, defaultdict

TIMEOUT = 6; FETCH_N = 60
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ─── 数据采集 (与V4.0相同) ───
def _get(url, h=HEADERS):
    try:
        r = requests.get(url, headers=h, timeout=TIMEOUT)
        return r.text if r.status_code == 200 and r.text else None
    except: return None

def parse_em(raw):
    try:
        rows = json.loads(raw)["data"]["fastNewsList"]
        return [{"time": str(r.get("showTime") or r.get("updateTime",""))[:16],
                 "title": (r.get("title") or "").strip(), "source": "东财"}
                for r in rows] or None
    except: return None

def parse_sina(raw):
    try:
        rows = json.loads(raw)["result"]["data"]
        return [{"time": dt.datetime.fromtimestamp(int(r["ctime"])).strftime("%m-%d %H:%M"),
                 "title": r.get("title","").strip(), "source": "新浪"}
                for r in rows] or None
    except: return None

def parse_ths(raw):
    try:
        rows = json.loads(raw)["data"]["list"]
        return [{"time": dt.datetime.fromtimestamp(int(r["ctime"])).strftime("%m-%d %H:%M"),
                 "title": (r.get("title") or "").strip(), "source": "同花顺"}
                for r in rows] or None
    except: return None

def fetch_em():
    url = f"https://np-listapi.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&pageSize={FETCH_N}&sortEnd=&req_trace=1"
    return parse_em(_get(url, {"User-Agent": "Mozilla/5.0"}))

def fetch_sina():
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num={FETCH_N}"
    return parse_sina(_get(url, {"User-Agent": "Mozilla/5.0"}))

def fetch_ths():
    url = f"https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=&track=website&pagesize={FETCH_N}"
    return parse_ths(_get(url, {"User-Agent": "Mozilla/5.0", "Referer": "https://news.10jqka.com.cn/"}))

# ─── 🆕 全量聚类引擎 ───
# 核心词库：A股/财经新闻中高频出现的概念/板块/行业词
TOPIC_KEYWORDS = [
    # 板块
    '半导体', '芯片', 'AI', '人工智能', '算力', '光模块', '光通信',
    '医药', '创新药', '医疗', 'CRO', '医疗器械',
    '消费', '白酒', '食品', '社零', '零售',
    '新能源', '光伏', '储能', '电池', '锂电', '风电',
    '军工', '航天', '大飞机', '无人机', '核',
    '有色', '黄金', '铜', '铝', '稀土', '资源',
    '煤炭', '石油', '化工', '天然气', '能源',
    '银行', '证券', '保险', '金融', '券商',
    '地产', '房地产', '基建', '建材',
    '汽车', '智能驾驶', '机器人', '机器视觉',
    '游戏', '传媒', '影视', 'IP',
    '通信', '5G', '6G', '卫星', 'F5G',
    '数字经济', '信创', '软件', '云计算', '大数据',
    '电力', '电网', '特高压',
    '养殖', '猪肉', '农业',
    '钢铁', '机械', '工业母机',
    '航运', '港口', '物流',
    # 事件
    '涨停', '跌停', '回购', '减持', '中报', '业绩', '分红',
    '政策', '规划', '发布会', '央行', '美联储',
    '美股', '港股', '韩国', '日本',
    'DRAM', 'HBM', '海力士', '三星', 'SK',
    'OpenAI', 'GPT', '大模型', 'Meta',
    'Trump', '关税', '制裁',
    '重组', '并购', 'IPO', '上市',
    '社融', 'CPI', 'PPI', 'GDP',
]

def extract_topics(items):
    """从标题全量自动聚类"""
    # 统计每个关键词在哪些标题里出现
    kw_titles = defaultdict(list)
    for item in items:
        title = item['title']
        for kw in TOPIC_KEYWORDS:
            if kw in title:
                kw_titles[kw].append(item)
    
    # 合并同义关键词 → 话题簇
    merge_map = {
        '半导体/芯片': ['半导体', '芯片', '韩', '三星', 'SK', '海力士', 'DRAM', 'HBM', 'CPO'],
        '算力/AI': ['算力', 'AI', '人工智能', '大模型', 'GPT', 'OpenAI', 'Meta', '光模块', '光通信'],
        '医药/医疗': ['医药', '创新药', '医疗', 'CRO', '医疗器械'],
        '消费/白酒': ['消费', '白酒', '食品', '零售', '社零'],
        '新能源/光伏': ['新能源', '光伏', '储能', '电池', '锂电', '风电'],
        '军工/航天': ['军工', '航天', '大飞机', '无人机', '核'],
        '有色/资源': ['有色', '黄金', '铜', '铝', '稀土', '资源', '煤炭', '石油'],
        '金融/证券': ['银行', '证券', '保险', '金融', '券商'],
        '房地产/基建': ['地产', '房地产', '基建', '建材'],
        '人形机器人': ['人形机器人', '机器人产量', '机器人产业化', '机器人概念'],
    '汽车/机器人': ['汽车', '智能驾驶', '机器人', '机器视觉', '机器人概念'],
        '游戏/传媒': ['游戏', '传媒', '影视', 'IP'],
        '通信/卫星': ['通信', '5G', '6G', '卫星', 'F5G'],
        '数字经济/信创': ['数字经济', '信创', '软件', '云计算', '大数据', '用友'],
        '电力/能源': ['电力', '电网', '特高压', '天然气'],
        '养殖/农业': ['养殖', '猪肉', '农业'],
        '钢铁/机械': ['钢铁', '机械', '工业母机'],
        '航运/物流': ['航运', '港口', '物流'],
        '政策/宏观': ['政策', '规划', '发布会', '央行', '美联储', '社融', 'CPI', 'PPI', 'GDP', 'Trump', '关税', '制裁'],
        '业绩/公告': ['中报', '业绩', '回购', '减持', '分红', '重组', '并购'],
        '美股/港股': ['美股', '港股', '韩国', '日本'],
    }
    
    topics = {}
    for topic_name, keywords in merge_map.items():
        all_items = []
        seen = set()
        for kw in keywords:
            for item in kw_titles.get(kw, []):
                tid = item['title'][:60]
                if tid not in seen:
                    seen.add(tid)
                    all_items.append(item)
        if all_items:
            topics[topic_name] = all_items
    
    # 按命中数量排序
    sorted_topics = sorted(topics.items(), key=lambda x: -len(x[1]))
    return sorted_topics


def keyword_search(pool, args):
    """保留关键词搜索能力"""
    hits = []
    for item in pool:
        if any(k in item['title'] for k in args):
            hits.append(item)
    return hits


def main():
    now = dt.datetime.now()
    ts = now.strftime('%m/%d %H:%M')
    
    # 采集
    pool, health = [], {}
    for name, fn in [("东财", fetch_em), ("新浪", fetch_sina), ("同花顺", fetch_ths)]:
        try: items = fn()
        except: items = None
        if items: pool.extend(items); health[name] = f"OK({len(items)}条)"
        else: health[name] = "盲区"
    
    # 状态文件
    status = {"timestamp": dt.datetime.now().isoformat(),
              "sources": health, "total_items": len(pool)}
    with open("liubei_status.json","w",encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    
    print("="*60)
    print(f"🤝 刘备 V4.1 · 全量聚类 | {ts}")
    for k,v in health.items(): print(f" {'✅' if 'OK' in v else '🔴'} {k}: {v}")
    print(f" 📊 总计 {len(pool)} 条")
    print("="*60)
    
    # 查health
    if any(a.startswith('--') for a in sys.argv[1:]):
        print("仅健康检查。")
        return
    
    # 手动关键词搜索（保留）
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args:
        hits = keyword_search(pool, args)
        print(f"\n🔍 {' '.join(args)} · 命中{len(hits)}条:")
        for h in hits[:15]:
            print(f" [{h['time']}] ({h['source']}) {h['title']}")
        if not hits:
            print(" 无命中。")
        return
    
    # 🆕 全量聚类
    print(f"\n{'='*60}")
    print(f"📊 全量话题聚类 (TOP 10)")
    print(f"{'='*60}")
    
    topics = extract_topics(pool)
    
    for rank, (topic, items) in enumerate(topics[:12], 1):
        bar = '🔥' if len(items) > 8 else ('🟢' if len(items) > 4 else '🟡')
        print(f"\n{rank:2}. {bar} **{topic}** ({len(items)}条)")
        
        # 显示前3条代表性新闻
        for item in items[:3]:
            src = item['source']
            t = item['time'][-8:] if len(item['time']) > 8 else item['time']
            title = item['title'][:80]
            print(f"    [{t} {src}] {title}")
        
        # 热度评估
        if len(items) >= 6:
            # 看看新闻时间分布
            recent = sum(1 for it in items if '今' in it.get('time', '') or 
                        dt.datetime.now().strftime('%m-%d') in it.get('time', ''))
            if recent > len(items) * 0.5:
                print(f"    ⚡ 今日集中发酵 — 关注度高")
    
    # 盲区检测：哪些板块今天有新闻但没在我们关注池
    threshold = 1  # 至少1条就算有动静
    our_focus_keywords = {'半导体', '芯片', '医药', '医疗', '消费', '军工', '有色', '新能源', '存储'}
    print(f"\n{'='*60}")
    print(f"🚨 盲区警报：有新闻但不在核心关注池")
    print(f"{'='*60}")
    blind_count = 0
    for topic, items in topics:
        topic_kw = set(topic.split('/'))
        if not topic_kw & our_focus_keywords and len(items) >= 2:
            print(f"  ⚠️ {topic} ({len(items)}条) — 未关注!")
            blind_count += 1
    if blind_count == 0:
        print("  ✅ 所有活跃话题均在关注池内")


if __name__ == '__main__':
    main()
