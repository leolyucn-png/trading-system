#!/usr/bin/env python3
"""
关平 V1.0 — 大A科技板块专属扫描器
隶属关羽，专门扫描A股科技板块细分赛道
覆盖：狭义TMT(电子/通信/计算机/传媒) + 广义硬科技(机械/电力/军工/汽车)
数据源：Sina API（永远稳定）
"""
import requests, json, time
from datetime import datetime

# ============================================================
# 一、狭义TMT核心科技
# ============================================================

TMT = {
    # 1.1 半导体设计
    '芯片设计-AI算力': ['sz002049','sh603501','sz300661','sz300782','sz300672'],
    '芯片设计-存储': ['sh603986','sz300672','sz300661'],
    '芯片设计-功率': ['sz300373','sz300623','sh600171'],
    '芯片设计-FPGA': ['sz002049','sh688385'],
    # 1.2 晶圆制造
    '晶圆制造-代工': ['sh688981','sh688126'],
    # 1.3 封测
    '封测-先进封装': ['sz002185','sz002156','sh600584'],
    # 1.4 设备
    '半导体设备-刻蚀薄膜': ['sz002371','sh688012'],
    '半导体设备-清洗量测': ['sh688037','sz300604'],
    # 1.5 材料
    '半导体材料-硅片': ['sh688126','sz300054'],
    '半导体材料-光刻胶': ['sz300236','sh600309'],
    # 1.6 光学光电子
    '光学-OLED面板': ['sz000725','sz000050'],
    '光学-车载镜头': ['sz002475','sh603005'],
    # 1.7 电子元件
    '电子元件-PCB': ['sh603005','sz300476'],
    '电子元件-MLCC': ['sz000636','sh600563'],
    # 1.8 消费电子
    '消费电子-终端': ['sz002475','sz002241','sz300433'],
    # 2. 通信
    '光通信-光模块': ['sz300308','sz300502','sz300394'],
    '光通信-光器件': ['sz300308','sz300502'],
    '算力-IDC': ['sh600941','sz300442'],
    '卫星通信': ['sh600118','sz002025'],
    # 3. 计算机
    '计算机-AI服务器': ['sz000977','sh603019'],
    '计算机-AI软件': ['sz002230','sz300624','sh688111'],
    '计算机-信创': ['sh600588','sz300454','sz002410'],
    '计算机-金融IT': ['sz300033','sh600570'],
    # 4. 传媒
    '传媒-AI游戏': ['sz002624','sh603444','sz300315'],
    '传媒-数字IP': ['sz300058','sz300251','sz002400'],
}

# ============================================================
# 二、广义硬科技
# ============================================================

HARD_TECH = {
    # 5. 机械设备
    '机器人-减速器': ['sz002747','sz300124'],
    '机器人-伺服电机': ['sz300124','sz002527'],
    '机器人-整机': ['sh601689','sz002747','sz300660'],
    '工业母机': ['sz000988','sz300124'],
    # 6. 电力设备
    '光伏-组件': ['sh601012','sz002459'],
    '光伏-逆变器': ['sz300274','sz300763'],
    '储能-电池': ['sz300750','sz002074'],
    '储能-PCS': ['sz300274','sz300763'],
    '风电': ['sh600011','sz300443'],
    # 7. 国防军工
    '军工电子': ['sh600879','sh600118'],
    '军工-航天': ['sh600118','sz002025','sh600391'],
    '军工-军机': ['sh600760','sh600893','sz000768'],
    # 8. 汽车
    '汽车-智能驾驶': ['sz002405','sh601689'],
    '汽车-车载芯片': ['sh600171','sh603005'],
    '汽车-车规功率': ['sz300373','sh600171'],
}

# ============================================================
# 三、美股强联动
# ============================================================

US_LINK = {
    '美股联动-光模块': ['sz300308','sz300502','sz300394'],
    '美股联动-光伏储能': ['sz300274','sz300763','sz300750'],
    '美股联动-OLED': ['sz000725','sz000050'],
    '美股联动-AI芯片': ['sz002049','sh603501','sz300308'],
}

def fetch_sina(codes_list):
    """批量获取Sina实时行情"""
    all_codes = []
    for codes in codes_list:
        all_codes.extend(codes)
    all_codes = list(dict.fromkeys(all_codes))  # 去重保持顺序
    
    all_prices = {}
    for i in range(0, len(all_codes), 50):
        batch = all_codes[i:i+50]
        try:
            r = requests.get(f'http://hq.sinajs.cn/list={",".join(batch)}',
                            headers={'Referer':'http://finance.sina.com.cn'}, timeout=8)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                fields = line.split('"')[1].split(',')
                if len(fields) < 4: continue
                code_raw = line.split('=')[0].split('_')[-1]
                px = float(fields[3])
                prev = float(fields[2])
                chg = (px - prev) / prev * 100
                all_prices[code_raw] = (px, chg)
        except:
            continue
    return all_prices

# 股票名称映射
STOCK_NAMES = {
    'sz002049':'紫光国微','sh603501':'韦尔股份','sz300661':'圣邦股份','sz300782':'卓胜微','sz300672':'国科微',
    'sh603986':'兆易创新','sz300373':'扬杰科技','sz300623':'捷捷微电','sh600171':'上海贝岭','sh688385':'复旦微电',
    'sh688981':'中芯国际','sh688126':'沪硅产业',
    'sz002185':'华天科技','sz002156':'通富微电','sh600584':'长电科技',
    'sz002371':'北方华创','sh688012':'中微公司','sh688037':'芯源微','sz300604':'长川科技',
    'sz300054':'鼎龙股份','sz300236':'上海新阳','sh600309':'万华化学',
    'sz000725':'京东方A','sz000050':'深天马A',
    'sz002475':'立讯精密','sh603005':'晶丰明源',
    'sz300476':'胜宏科技','sz000636':'风华高科','sh600563':'法拉电子',
    'sz002241':'歌尔股份','sz300433':'蓝思科技',
    'sz300308':'中际旭创','sz300502':'新易盛','sz300394':'天孚通信',
    'sh600941':'中国移动','sz300442':'润泽科技',
    'sh600118':'中国卫星','sz002025':'航天电器',
    'sz000977':'浪潮信息','sh603019':'中科曙光',
    'sz002230':'科大讯飞','sz300624':'万兴科技','sh688111':'金山办公',
    'sh600588':'用友网络','sz300454':'深信服','sz002410':'广联达',
    'sz300033':'同花顺','sh600570':'恒生电子',
    'sz002624':'完美世界','sh603444':'吉比特','sz300315':'掌趣科技',
    'sz300058':'蓝色光标','sz300251':'光线传媒','sz002400':'省广集团',
    'sz002747':'埃斯顿','sz300124':'汇川技术','sz002527':'新时达','sh601689':'拓普集团','sz300660':'江苏雷利',
    'sz000988':'华工科技',
    'sh601012':'隆基绿能','sz002459':'晶澳科技',
    'sz300274':'阳光电源','sz300763':'锦浪科技',
    'sz300750':'宁德时代','sz002074':'国轩高科',
    'sz300443':'金雷股份',
    'sh600879':'航天电子',
    'sh600760':'中航沈飞','sh600893':'航发动力','sz000768':'中航西飞',
    'sz002405':'四维图新',
    'sh600391':'航发科技',
}

def scan_category(category, sectors, all_prices):
    """扫描一个分类下的所有子板块"""
    print(f"\n{'='*55}")
    print(f"  {category}")
    print(f"{'='*55}")
    
    results = []
    for sector_name, codes in sectors.items():
        chgs = []
        stocks_detail = []
        for c in codes:
            code_key = c.split('.')[-1]
            if code_key in all_prices:
                px, chg = all_prices[code_key]
                name = STOCK_NAMES.get(code_key, code_key)
                chgs.append(chg)
                stocks_detail.append((name, px, chg))
        
        if chgs:
            avg = sum(chgs) / len(chgs)
            max_c = max(chgs)
            min_c = min(chgs)
            results.append((avg, sector_name, stocks_detail, max_c, min_c))
    
    results.sort(key=lambda x: -x[0])
    
    for avg, name, stocks, mx, mn in results:
        bar = '🚀' if avg > 6 else ('🟢' if avg > 2 else ('🟡' if avg > 0 else ('🔴' if avg > -2 else '💀')))
        print(f"  {bar} {avg:+.1f}% {name}")
        for sn, sp, sc in stocks:
            b2 = '🚀' if sc > 6 else ('🟢' if sc > 2 else ('🟡' if sc > 0 else '🔴'))
            own = ' ✅持有' if sn in ['紫光国微','上海贝岭'] else ''
            print(f"      {sn:10s} {sp:.2f}  {sc:+.2f}%{own}")

    return results

def main():
    t0 = time.time()
    now = datetime.now().strftime('%m/%d %H:%M')
    
    print("━" * 55)
    print(f"  关平 V1.0 · 大A科技板块专属扫描 | {now}")
    print(f"  隶属：关羽 | 专注：科技细分赛道")
    print("━" * 55)
    
    # 获取所有股票数据
    all_codes_list = []
    for sectors in [TMT, HARD_TECH, US_LINK]:
        for codes in sectors.values():
            all_codes_list.append(codes)
    
    all_prices = fetch_sina(all_codes_list)
    
    # 分类扫描
    scan_category("📟 一、狭义TMT核心科技", TMT, all_prices)
    scan_category("⚙️ 二、广义硬科技", HARD_TECH, all_prices)
    scan_category("🌐 三、美股强联动", US_LINK, all_prices)
    
    # 资金流向汇总
    print(f"\n{'='*55}")
    print(f"  💰 资金流向汇总（最强细分 TOP5）")
    print(f"{'='*55}")
    
    all_sectors = {}
    for sectors in [TMT, HARD_TECH, US_LINK]:
        for name, codes in sectors.items():
            chgs = []
            for c in codes:
                code_key = c.split('.')[-1]
                if code_key in all_prices:
                    chgs.append(all_prices[code_key][1])
            if chgs:
                all_sectors[name] = sum(chgs)/len(chgs)
    
    top5 = sorted(all_sectors.items(), key=lambda x: -x[1])[:5]
    for name, avg in top5:
        bar = '🚀' if avg > 6 else '🟢'
        print(f"  {bar} {avg:+.1f}% {name}")
    
    elapsed = time.time() - t0
    print(f"\n  耗时: {elapsed:.1f}s")

if __name__ == '__main__':
    main()
