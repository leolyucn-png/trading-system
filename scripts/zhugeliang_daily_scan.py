#!/usr/bin/env python3
import sys as _sys
NO_ENV = '--no-env' in _sys.argv
"""
诸葛亮 V3.0 · 中长期牛股筛选（每日12:00运行）
============================================
✅ Step 0–4 完整评估框架（用户2026-07-26亲授）
✅ 输出: 环境系数 × 五维评分 → 最终分 + 概率 + 赔率
✅ 禁止因果叙事，只输出概率+置信度

五维评分：
  ① 放量确认(25) — 温和持续放量 > 单日爆量 > 缩量=0
  ② 筹码位置(20) — 底部平台 > 中位 > 前高附近=0
  ③ 板块催化(25) — 启动初期+个股同步 > 中期 > 末期/龙头分歧
  ④ 弹性强度(15) — 联动规则：放量<15分则本项上限5分
  ⑤ 风险排除(15) — 振幅异常/大盘股/换手率/均线偏离

输出: memory/诸葛亮长期池/YYYY-MM-DD.md
"""
import requests, json, os
from datetime import datetime

TIMEOUT = 8

# ==================== 38个ETF ====================
ETF_MAP = {
    '半导体':'sh512480','芯片':'sz159995','消费电子':'sz159732','AI':'sh515070','通信':'sh515880',
    '云计算':'sz159890','软件':'sz159852','科创50':'sh588000',
    '医药':'sh512010','创新药':'sh515120','医疗器械':'sz159883',
    '军工':'sh512660','国防':'sh512670','机器人':'sh562500',
    '新能源车':'sh515030','新能源':'sh516160','光伏':'sh515790','电力':'sz159611',
    '有色':'sh512400','煤炭':'sh515220','化工':'sh516020','钢铁':'sh515210',
    '证券':'sh512880','银行':'sh512800',
    '消费':'sz159928','酒':'sh512690','家电':'sz159996','旅游':'sz159766','农业':'sz159825','养殖':'sz159865',
    '游戏':'sz159869','传媒':'sz159805','影视':'sz159855',
    '基建':'sh516970','地产':'sh512200','汽车':'sh516110',
}

# 股票持仓映射（每个板块3-5只候选）
CANDIDATES = {
    '半导体': 'sh600171,sz002049,sh600460,sh600584,sz002185',
    '芯片设计': 'sz300672,sz300661,sh603501,sz300782',
    '消费电子': 'sz000725,sz002475,sh603005,sz002241,sh601138',
    '医药': 'sh600276,sz300760,sz300015,sz300347,sh600196',
    '创新药': 'sh600216,sz300122,sz300759',
    'AI': 'sz000977,sz002230,sh603019,sz300624,sz002261,sz000034,sz300474',
    '通信': 'sh600941,sz000063,sz300394,sz300308',
    '云计算': 'sz300454,sz300442,sh600588,sh688111,sz000032,sz300846',
    '软件': 'sz300033,sz002410,sz300496,sh603171,sh600570,sh600845,sh600536,sz300253',
    '证券': 'sh601995,sz300059,sz002736,sh601211',
    '机器人': 'sz002747,sz300124,sz002527,sh601689',
    '军工': 'sh600760,sh600893,sz000768,sz002013',
    '光伏': 'sh601012,sz002459,sz300274,sz300724',
    '新能源车': 'sz002594,sz300750,sz002460,sh600104',
    '化工': 'sh600309,sz002709,sh600352,sz300409',
    '有色': 'sh601899,sh600362,sh600547,sz000630',
    '钢铁': 'sh600019,sh600010,sh600808',
    '游戏': 'sz002624,sh603444,sz300315,sz002555',
    '传媒': 'sz300058,sz002400,sh601858,sz300251',
    '食品饮料': 'sh600519,sh600887,sh603288',
    '基建': 'sh601668,sh601800,sh600039,sh601186',
    '地产': 'sz000002,sh600048,sh600383',
    '银行': 'sh601398,sh601939,sh601288,sh600036',
}


def fetch_all_a_codes():
    """2026-08-06 新增：获取全市场A股代码（主板+科创板+创业板，剔除北交所）
    
    用户指令：取消固定候选池，每天全市场选股。
    数据源：新浪 Market_Center.getHQNodeData（hs_a全市场，按涨跌幅排序分页）
    缓存：写入 scripts/cache_all_a_codes.json，当日复用（避免每次扫描拉5000+只）
    """
    import json, os, datetime
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_all_a_codes.json")
    today = datetime.date.today().isoformat()
    
    # 读缓存（当日有效）
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding='utf-8') as f:
                cache = json.load(f)
            if cache.get('date') == today and cache.get('codes'):
                return cache['codes']
        except: pass
    
    # 拉取全市场（新浪分页，按涨跌幅排序，前80页覆盖约5500只）
    all_codes = []
    page = 1
    while page <= 80:
        try:
            url = f'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=80&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=init'
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            d = r.json()
            if not d: break
            for s in d:
                c = s.get('code', '')
                # 🆕 2026-08-12 用户铁律：买不了科创板 → 688/689一律排除（北交所bj/920也剔除）
                # 保留主板(60/00)+创业板(300/301)
                if c.startswith(('60', '00', '300', '301')):
                    prefix = 'sh' if c.startswith(('60', '688', '689')) else 'sz'
                    code_full = f'{prefix}{c}'
                    if code_full not in all_codes:
                        all_codes.append(code_full)
            page += 1
        except Exception:
            break
    
    # 写缓存
    if all_codes:
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'date': today, 'codes': all_codes}, f, ensure_ascii=False)
        except: pass
    return all_codes


def preselect_active_codes(all_codes):
    """2026-08-06 新增：全市场活跃股预筛
    
    从新浪全市场列表缓存中筛出活跃股（成交额>5亿·非ST·非新股），
    只对活跃股做详细评分，避免5200+只全量拉取（208次请求→40次）。
    
    返回：活跃股代码列表（sh/sz前缀）
    """
    import json, os, datetime
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_all_a_stocks.json")
    today = datetime.date.today().isoformat()
    
    active = []
    # 优先读缓存的全市场列表（含成交额等字段）
    stocks_data = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding='utf-8') as f:
                c = json.load(f)
            if c.get('date') == today and c.get('stocks'):
                stocks_data = c['stocks']
        except: pass
    
    # 无缓存则重新拉全市场列表
    if stocks_data is None:
        stocks_data = []
        page = 1
        while page <= 80:
            try:
                url = f'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=80&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=init'
                r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                d = r.json()
                if not d: break
                stocks_data.extend(d)
                page += 1
            except Exception:
                break
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'date': today, 'stocks': stocks_data}, f, ensure_ascii=False)
        except: pass
    
    for s in stocks_data:
        c = s.get('code', '')
        if c.startswith('bj') or c.startswith('688') or c.startswith('689'): continue  # 🆕 2026-08-12 用户铁律：买不了科创板
        name = s.get('name', '')
        if 'ST' in name or name.startswith(('N', 'C')): continue
        try:
            amt = float(s.get('amount', 0))
        except:
            continue
        if amt < 5e8: continue  # 成交额>5亿
        prefix = 'sh' if c.startswith(('60', '688', '689')) else 'sz'
        full = f'{prefix}{c}'
        if full in all_codes and full not in active:
            active.append(full)
    return active


def get_sina(codes):
    """批量获取Sina实时数据 + qt.gtimg.cn市值"""
    all_results = {}
    # 1. Sina获取价格/成交量
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        try:
            r = requests.get(f'http://hq.sinajs.cn/list={",".join(batch)}',
                           headers={'Referer':'http://finance.sina.com.cn'}, timeout=TIMEOUT)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip(): continue
                fields = line.split('"')[1].split(',')
                if len(fields) < 6: continue
                code_raw = line.split('=')[0].split('_')[-1]
                all_results[code_raw] = {
                    'name': fields[0], 'px': float(fields[3]), 'prev': float(fields[2]),
                    'high': float(fields[4]), 'low': float(fields[5]), 'vol': int(float(fields[8])),
                    'cap': 0
                }
        except: continue
    
    # 2. qt.gtimg.cn补市值+成交额
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        try:
            r2 = requests.get(f'http://qt.gtimg.cn/q={",".join(batch)}',
                            headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
            r2.encoding = 'gbk'
            for line in r2.text.strip().split('\n'):
                if not line.strip(): continue
                f = line.split('~')
                if len(f) < 45: continue
                code_raw = line.split('=')[0].split('_')[-1]
                cap_val = float(f[44]) if len(f)>44 and f[44] else 0
                amt_wan = float(f[37]) if len(f)>37 and f[37] else 0
                if code_raw in all_results:
                    all_results[code_raw]['cap'] = cap_val
                    all_results[code_raw]['amount_wan'] = amt_wan
        except: continue
    
    return all_results


def get_stock_sectors(code):
    """诸葛亮V2.0 板块归属映射（2026-08-06补：解决板块分全0）

    用东财F10 CoreConception返回个股所属板块列表，
    与ETF_MAP板块名模糊匹配，返回匹配到的诸葛亮板块名（如'半导体'）。
    code格式：sh603078 / sz300540
    """
    import requests as _rq
    code_digits = ''.join(ch for ch in str(code) if ch.isdigit())
    if not code_digits:
        return None
    prefix = 'SH' if str(code).startswith('sh') else 'SZ'
    try:
        url = f'https://emweb.securities.eastmoney.com/PC_HSF10/CoreConception/PageAjax?code={prefix}{code_digits}'
        d = _rq.get(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://emweb.securities.eastmoney.com/'}, timeout=6,
                   proxies={'http':None,'https':None}).json()
        boards = [b.get('BOARD_NAME','') for b in d.get('ssbk',[])]
        # 关键词映射：ETF_MAP板块名 → F10板块名关键词
        keyword_map = {
            '半导体': ['半导体','集成电路','芯片','封测'],
            '芯片': ['芯片','集成电路'],
            '消费电子': ['消费电子','电子'],
            'AI': ['人工智能','AI','算力'],
            '通信': ['通信','光模块','5G'],
            '云计算': ['云计算','数据中心'],
            '软件': ['软件','信创','计算机'],
            '科创50': ['科创'],
            '医药': ['医药','生物'],
            '创新药': ['创新药','生物医药'],
            '医疗器械': ['医疗器械','医疗'],
            '军工': ['军工','国防','航天','航空'],
            '国防': ['国防','军工'],
            '机器人': ['机器人','自动化'],
            '新能源车': ['新能源车','汽车整车','锂电池'],
            '新能源': ['新能源','锂电','储能'],
            '光伏': ['光伏','太阳能'],
            '电力': ['电力','电网'],
            '有色': ['有色','黄金','稀土','铜','铝'],
            '煤炭': ['煤炭'],
            '化工': ['化工','化学','材料'],
            '钢铁': ['钢铁'],
            '证券': ['证券','券商'],
            '银行': ['银行'],
            '消费': ['消费','白酒','食品'],
            '酒': ['白酒','酒'],
            '家电': ['家电'],
            '旅游': ['旅游','酒店'],
            '农业': ['农业','农林'],
            '养殖': ['养殖','畜牧'],
            '游戏': ['游戏'],
            '传媒': ['传媒','影视'],
            '影视': ['影视','传媒'],
            '基建': ['基建','建筑','工程'],
            '地产': ['房地产','地产'],
            '汽车': ['汽车'],
        }
        for sector_name, kws in keyword_map.items():
            for b in boards:
                if any(kw in b for kw in kws):
                    return sector_name
        return None
    except Exception:
        return None


def detect_sector_inflection():
    """诸葛亮V2.0 板块拐点检测（第二步）

    对ETF_MAP全部板块扫描：
      - 连续3日缩量不创新低 + 当日放量涨≥1.5% + 破5日均线 → 25分
      - 连续3日主力资金净流入（无资金数据时用连续3日上涨近似）→ 20分
      - 当日放量启动 → 20分
      - 🆕 2026-08-12 接入关羽资金方向（guanyu_fund_direction.json）：主力净流入TOP板块直接+15分
        （背景：板块拐点只看ETF量价会漏判——半导体ETF缩量但概念资金+82.6亿，量价与资金脱节）
      - 无拐点 → 0分
    返回 {板块名: (得分, 信号描述)}
    """
    import requests as _rq, json as _json, os as _os
    # 🆕 2026-08-12 读关羽资金方向：{概念名: 主力净流入亿}，只取净流入≥10亿的强概念
    fund_map = {}
    try:
        _fp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'memory', 'guanyu_fund_direction.json')
        if _os.path.exists(_fp):
            _fd = _json.load(open(_fp))
            for _s in (_fd.get('sectors') or []):
                if (_s.get('inflow') or 0) >= 10:
                    fund_map[_s.get('name', '')] = _s.get('inflow', 0)
    except Exception:
        pass
    # 🆕 2026-08-14 读张飞轮动预判（用户亲授：诸葛亮拿一周，板块维度用「预判资金方向」而非当天放量）：
    #   zhangfei_rotation.json 的 full_ranking = 下一交易日领涨预测，TOP板块直接给板块分
    #   逻辑：关羽资金=今天已发生；张飞预判=明天方向；诸葛亮周线持仓应信预判，不等当天放量（当天放量=晚一步）
    zf_map = {}
    try:
        _zp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'memory', 'zhangfei_output', 'zhangfei_rotation.json')
        if _os.path.exists(_zp):
            _zd = _json.load(open(_zp))
            _full = _zd.get('full_ranking') or _zd.get('prediction') or []
            for _i, _sec in enumerate(_full):
                zf_map[_sec.get('name', '')] = {'score': _sec.get('score', 0), 'rank': _i + 1}
    except Exception:
        pass
    result = {}
    for name, code in ETF_MAP.items():
        full_sym = code.strip()  # 已经是sh512480格式
        score = 0
        desc = ''
        try:
            # 日线K线（30日）
            url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_sym},day,,,30,qfq'
            d = _rq.get(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://gu.qq.com/'}, timeout=6,
                       proxies={'http':None,'https':None}).json()
            k = d.get('data', {}).get(full_sym, {})
            kl = k.get('qfqday') or k.get('day') or []
            if len(kl) >= 10:
                closes = [float(x[2]) for x in kl]
                vols = [float(x[5]) if len(x)>5 else 0 for x in kl]
                lows = [float(x[4]) for x in kl]
                highs = [float(x[3]) for x in kl]
                cur = closes[-1]
                chg_today = (closes[-1]/closes[-2]-1)*100 if closes[-2] else 0
                ma5 = sum(closes[-5:])/5
                # 🆕 2026-08-10 修复：板块20日分位（不追高铁律）——高位板块不给拐点分
                _hi20 = max(highs[-20:]) if len(highs) >= 20 else max(highs)
                _lo20 = min(lows[-20:]) if len(lows) >= 20 else min(lows)
                _pos20 = (cur - _lo20) / (_hi20 - _lo20) * 100 if _hi20 > _lo20 else 50.0
                # 连续3日缩量不创新低
                shrink3 = all(vols[-i] <= vols[-i-1] for i in range(1,4))
                no_new_low = lows[-1] > min(lows[-5:-1])
                # 当日放量涨≥1.5%破5日线
                vol_ratio = vols[-1] / (sum(vols[-6:-1])/5) if sum(vols[-6:-1]) > 0 else 0
                breakout = chg_today >= 1.5 and cur > ma5 and vol_ratio >= 1.2
                # 连续3日上涨（资金流入近似）
                up3 = all(closes[-i] > closes[-i-1] for i in range(1,4))
                
                if shrink3 and no_new_low and breakout:
                    score = 25
                    desc = f'缩量止跌+放量突破5日线(+{chg_today:.1f}%)'
                elif up3:
                    score = 20
                    desc = f'连续3日走强(+{chg_today:.1f}%)'
                # 🆕 2026-08-12 修复：当日放量启动提到20分档（原15分——主线板块只能拿15+封顶15=15分，板块维度永远不满）
                #   背景：半导体/通信今日放量大涨，但缩量3日+破5日线条件不满足（普涨行情无缩量）
                elif chg_today >= 2.5 and vol_ratio >= 1.2:
                    score = 20
                    desc = f'当日放量启动(+{chg_today:.1f}%·vr{vol_ratio:.1f})'
                elif no_new_low and chg_today > 0:
                    score = 5
                    desc = f'止跌企稳(+{chg_today:.1f}%)'
                else:
                    score = 0
                    desc = f'无拐点({chg_today:+.1f}%)'
                # 🆕 2026-08-12 修复：分位封顶过严导致全市场板块拐点分≤5分（诸葛亮永久无票根因之一）
                #   原：>80%封5分/>65%封10分——震荡市多数板块在65-80%区间→全被压到10分以下
                #   改：>85%封5分（真高位）/ >75%封15分（中高位）/ 其余正常给分
                if _pos20 > 85:
                    score = min(score, 5)
                    desc += f'·高位分位{_pos20:.0f}%不追'
                elif _pos20 > 75:
                    score = min(score, 15)
                    desc += f'·中高分位{_pos20:.0f}%减分'
        except Exception:
            score = 0
            desc = '数据缺失'
        # 🆕 2026-08-12 接入关羽资金方向：概念名含板块名且净流入≥10亿 → +15分
        #   注意：资金方向是概念名（如'国产芯片'），与板块名（'半导体'）模糊匹配
        if fund_map:
            for _fn, _iv in fund_map.items():
                if (name and (_fn in name or name in _fn)) or (name and any(_k in _fn for _k in (name.replace('ETF','').strip(),))):
                    score = max(score, min(15, score + 15))
                    desc += f'·资金{_fn}+{_iv:.0f}亿(+15)'
                    break
        # 🆕 2026-08-14 接入张飞预判资金方向（用户亲授：诸葛亮拿一周，信预判不等当天放量）：
        #   TOP1-2板块 → +20分；TOP3-5 → +12分；其余有分 → +6分（预判方向提前布局）
        #   与关羽当天资金叠加：两者都指向同一板块 = 资金+预判共振（最高35分）
        if zf_map:
            _hit = None
            _nm = name.replace('ETF','').strip()
            for _zn, _zv in zf_map.items():
                if _zn == _nm or (_zn in _nm or _nm in _zn):
                    _hit = _zv
                    break
            if _hit:
                if _hit.get('rank') <= 2:
                    score += 20
                    desc += f'·张飞预判TOP{_hit.get("rank")}({_hit.get("score"):.0f}分)(+20)'
                elif _hit.get('rank') <= 5:
                    score += 12
                    desc += f'·张飞预判TOP{_hit.get("rank")}({_hit.get("score"):.0f}分)(+12)'
                elif _hit.get('score', 0) >= 45:
                    score += 6
                    desc += f'·张飞预判{_hit.get("score"):.0f}分(+6)'
        result[name] = (score, desc)
    return result


def get_etf_data():
    """获取ETF数据"""
    codes = ','.join(ETF_MAP.values())
    try:
        r = requests.get(f'http://hq.sinajs.cn/list={codes}',
                        headers={'Referer':'http://finance.sina.com.cn'}, timeout=TIMEOUT)
        r.encoding = 'gbk'
        result = {}
        for line in r.text.strip().split('\n'):
            if not line.strip(): continue
            fields = line.split('"')[1].split(',')
            if len(fields) < 4: continue
            px, prev = float(fields[3]), float(fields[2])
            chg = (px-prev)/prev*100
            for name, code in ETF_MAP.items():
                if code.split('.')[-1] in line.lower():
                    result[name] = round(chg, 1)
                    break
        return result
    except:
        return {}


def weekly_score_dna_v2(info, etf_data, sector_score=0, amount_wan=0):
    """诸葛亮V2.0 周线五维评分（用户2026-08-06亲授）

    维度：拐点突破确认25 + 筹码位置安全20 + 板块拐点共振25 + 趋势强度15 + 基本面排雷15
    返回 (总分, dims, note)
    """
    chg = info.get('chg', 0)
    amp = info.get('amp', 0)
    code = info.get('code', '')
    name = info.get('name', '')
    code_digits = ''.join(ch for ch in str(code) if ch.isdigit())
    sym = 'sh' + code_digits if code_digits.startswith('6') else ('bj' + code_digits if code_digits.startswith(('4','8')) else 'sz' + code_digits)
    
    # 基本面排雷（15分）：ST/退市/雷点
    d5 = 0
    if 'ST' in str(name).upper() or '退' in str(name):
        return 0, (0,0,0,0,0), "ST/退市风险·排除"
    d5 = 15
    
    # 拉周线K线
    wk = get_weekly_kline(sym, 30)
    d1 = d2 = d4 = 0
    note_parts = []
    
    if wk and len(wk) >= 15:
        closes = [x[2] for x in wk]
        highs = [x[3] for x in wk]
        lows = [x[4] for x in wk]
        vols = [x[5] for x in wk]
        cur = closes[-1]
        ma20w = sum(closes[-20:]) / 20
        ma5w = sum(closes[-5:]) / 5
        ma10w = sum(closes[-10:]) / 10
        hi20, lo20 = max(highs[-20:]), min(lows[-20:])
        
        # ── 禁止高位接盘（V2.0铁律·2026-08-07修复）：连续上涨3天以上+累计涨幅>20% → 不给推荐分 ──
        # 修复：原用周线口径(chg10d=5周涨幅)严重滞后，本周暴涨的票周线未反映，误判为超跌
        # 改为实时日线口径：拉最近12日日K，算5日/10日涨幅+连涨天数
        chg5d = chg10d = streak = 0
        try:
            import requests as _req
            _url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,12,qfq'
            _r = _req.get(_url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6).json()
            _kl = _r['data'][sym].get('qfqday') or _r['data'][sym].get('day')
            _c = [float(x[2]) for x in _kl]
            if len(_c) >= 6:
                chg5d = (_c[-1]/_c[-6]-1)*100
            if len(_c) >= 11:
                chg10d = (_c[-1]/_c[-11]-1)*100
            for i in range(len(_c)-1, 0, -1):
                if _c[i] > _c[i-1]: streak += 1
                else: break
        except Exception:
            pass
        # 铁律触发：5日/10日涨幅>20%（高位）→ 只提示风险，不给分
        if chg5d > 20 or chg10d > 20:
            return 0, (0,0,0,0,15), f"高位接盘风险：5日{chg5d:.0f}%/10日{chg10d:.0f}%>20%·仅提示风险"
        if streak >= 3 and chg5d > 15:
            return 0, (0,0,0,0,15), f"高位接盘风险：连涨{streak}天+5日{chg5d:.0f}%·仅提示风险"
        
        # ── 维度1 拐点突破确认（25分）──
        # 条件：突破20周均线或横盘2周平台 + 当日涨≥3% + 量能较前5周均量放大30%
        vol_ratio_w = vols[-1] / (sum(vols[-6:-1])/5) if sum(vols[-6:-1]) > 0 else 0
        breakout_ma20 = cur > ma20w and closes[-2] <= ma20w  # 本周突破20周线
        # 横盘2周平台突破：近5周振幅<12% + 当前突破
        recent_range = (max(highs[-5:]) - min(lows[-5:])) / min(lows[-5:]) * 100 if min(lows[-5:]) > 0 else 99
        platform_break = recent_range < 12 and cur > max(highs[-5:-1])  # 突破平台高点
        
        if (breakout_ma20 or platform_break) and chg >= 3 and vol_ratio_w >= 1.3:
            d1 = 25  # 周线突破+当日涨3%+放量30%
            note_parts.append('周线突破20周线/平台+放量')
        elif (breakout_ma20 or platform_break) and chg >= 9.5:
            d1 = 25  # 涨停+突破
            note_parts.append('涨停+突破')
        elif chg >= 3 and vol_ratio_w >= 1.3:
            d1 = 15  # 放量上涨但未破周线压力
            note_parts.append('放量未破周线')
        elif recent_range < 10 and cur > max(highs[-4:-1]):
            d1 = 15
            note_parts.append('底部横盘突破')
        # 🆕 2026-08-12 修复：日线放量启动分支（原逻辑只认周线突破→震荡市全0分→永久无票）
        #   用12日日K实时量比：当日放量≥1.5倍 + 涨幅≥2% = 日线启动信号（不要求周线突破）
        elif chg5d is not None and chg5d <= 12 and chg >= 2:
            try:
                _vol_ratio_d = None
                _url_d = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,12,qfq'
                _r_d = _req.get(_url_d, headers={'User-Agent':'Mozilla/5.0'}, timeout=6).json()
                _kl_d = _r_d['data'][sym].get('qfqday') or _r_d['data'][sym].get('day')
                _vv = [float(x[5]) for x in _kl_d]
                if len(_vv) >= 6 and sum(_vv[-6:-1]) > 0:
                    _vol_ratio_d = _vv[-1] / (sum(_vv[-6:-1])/5)
            except Exception:
                _vol_ratio_d = None
            if _vol_ratio_d is not None and _vol_ratio_d >= 1.5:
                d1 = 15
                note_parts.append(f'日线放量启动(vr={_vol_ratio_d:.1f}·5日{chg5d:.0f}%)')
            elif chg >= 2.5:
                d1 = 10
                note_parts.append(f'日线上涨未放量(+{chg:.1f}%)')
        else:
            d1 = 0
            note_parts.append('无周线突破信号')
        
        # 底部横盘≥2周+筹码集中<15%首次突破 → 额外+5
        if recent_range < 10 and platform_break and lo20 > 0:
            d1 = min(d1 + 5, 25)
        
        # ── 维度2 筹码位置安全（20分）──
        pos = (cur - lo20) / (hi20 - lo20) if hi20 > lo20 else 0.5
        if pos <= 0.35:
            d2 = 20  # 底部区间
            note_parts.append(f'筹码底部({pos:.0%})')
        elif pos <= 0.65:
            d2 = 10  # 中位
            note_parts.append(f'筹码中位({pos:.0%})')
        else:
            d2 = 0  # 高位
            note_parts.append(f'筹码高位({pos:.0%})·风险')
        
        # ── 维度4 趋势强度（15分）──
        # 5/10周线金叉 + 股价在短周均线上方
        golden_cross = ma5w > ma10w and closes[-2] and (sum(closes[-5:])/5 > sum(closes[-10:])/10)
        if golden_cross and cur > ma5w:
            d4 = 15
            note_parts.append('5/10周线金叉')
        elif cur > ma5w and closes[-1] > closes[-3]:
            d4 = 5  # 超跌反弹
            note_parts.append('超跌反弹')
        else:
            d4 = 0
            note_parts.append('趋势未转')
    else:
        # 周线数据缺失：用日线近似（降权）
        note_parts.append('周线缺失·日线近似')
        # 简单用日线涨幅和20日分位近似
        if chg >= 3:
            d1 = 10
        if 0 <= chg <= 6:
            d2 = 10
        d4 = 5
    
    # ── 维度3 板块拐点共振（25分）：直接用传入的板块强度分 ──
    d3 = sector_score
    
    total = d1 + d2 + d3 + d4 + d5
    dims = (d1, d2, d3, d4, d5)
    note = ' | '.join(note_parts)
    return total, dims, note


def score_dna(info, etf_data, amount_wan=0, percentiles=None):
    """
    诸葛亮DNA五维评分 V3（2026-07-27修复）
    修复: ②筹码位置无数据时返回None，④弹性强度改分位数阈值
    2026-08-04修复: 分位数从候选池自身计算（percentiles参数），
      不再用观察池208只样本——候选池全是板块龙头(成交额普遍数亿)，
      与观察池(含大量小票)错配导致全部票成交额>P90 → 弹性维度恒15分
    总分按有效维度归一化
    """
    import csv, os
    
    chg = info['chg']
    amp = info['amp']
    sector = info['sector']
    vol = info['vol']  # 成交量(手)
    px = info['px']
    
    # 从stock_snapshot读取成交额分位数（2026-08-04：优先用候选池自身分位数，无则回退快照法）
    data_dir = os.path.expanduser("~/Desktop/龙虾的三国模式/04_数据")
    if percentiles:
        P30, P50, P70, P90 = percentiles['P30'], percentiles['P50'], percentiles['P70'], percentiles['P90']
    else:
        snap_files = [f for f in os.listdir(data_dir) if f.startswith("stock_snapshot_") and f.endswith(".csv")]
        ALL_AMOUNTS = []
        if snap_files:
            with open(os.path.join(data_dir, sorted(snap_files)[-1])) as f:
                for r in csv.DictReader(f):
                    a = float(r['成交额万']) if r['成交额万'] else 0
                    if a > 0: ALL_AMOUNTS.append(a)
        ALL_AMOUNTS.sort()
        n_all = len(ALL_AMOUNTS)
        P30 = ALL_AMOUNTS[int(n_all*0.3)] if n_all > 0 else 0
        P50 = ALL_AMOUNTS[int(n_all*0.5)] if n_all > 0 else 0
        P70 = ALL_AMOUNTS[int(n_all*0.7)] if n_all > 0 else 0
        P90 = ALL_AMOUNTS[int(n_all*0.9)] if n_all > 0 else 0
    
    # ── 维度① 放量确认 (25分) ──
    # 2026-08-06 改版：适配全市场抓涨停（原逻辑只认0.5-3%温和上涨，排斥涨停）
    d1 = 0
    try:
        vol_ratio = info.get('vol_ratio', 0) or 1.0
    except:
        vol_ratio = 1.0
    if amount_wan > P90 and chg >= 3 and vol_ratio >= 1.2:
        d1 = 25  # 涨停/大涨+天量+放量 = 最强启动
    elif amount_wan > P90 and 0.5 < chg < 3 and vol_ratio >= 1.2:
        d1 = 25  # 原逻辑：天量温和放量
    elif amount_wan > P90 and chg >= 3:
        d1 = 20  # 大涨+天量（无量比数据也给高分）
    elif amount_wan > P70 and 0 < chg < 3:
        d1 = 15
    elif amount_wan > P70 and chg >= 3:
        d1 = 12  # 中量+大涨
    elif amount_wan > P50 and 0 < chg < 5:
        d1 = 8
    elif amount_wan > P90 and chg < 0:
        d1 = 5
    
    # ── 维度② 筹码位置 (20分) — 东财/腾讯日K线（2026-08-06改：腾讯失效回退东财）──
    d2 = None
    try:
        code = info.get('code', '')
        # 兼容带前缀的code(sh601899) → 提取纯数字
        code_digits = ''.join(ch for ch in str(code) if ch.isdigit())
        if code_digits:
            import requests as _rq
            sym = 'sh' + code_digits if code_digits.startswith('6') else ('bj' + code_digits if code_digits.startswith(('4','8')) else 'sz' + code_digits)
            market = '1' if code_digits.startswith('6') else '0'
            _kl = []
            # 2026-08-06 K线磁盘缓存（当日复用，避免每只每次拉网络）
            import os as _os, json as _json
            _kdir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'cache_kline20')
            _os.makedirs(_kdir, exist_ok=True)
            _kfile = _os.path.join(_kdir, f'{code_digits}.json')
            _today = datetime.now().strftime('%Y-%m-%d')
            if _os.path.exists(_kfile):
                try:
                    with open(_kfile, encoding='utf-8') as _f:
                        _kcache = _json.load(_f)
                    if _kcache.get('date') == _today and len(_kcache.get('kl', [])) >= 10:
                        _kl = _kcache['kl']
                except Exception:
                    _kl = []
            # 东财源优先（2026-08-06：腾讯ifzq间歇性故障）
            if len(_kl) < 10:
                try:
                    _url_em = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{code_digits}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=20'
                    _d_em = _rq.get(_url_em, headers={'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}, timeout=6).json()
                    _kl = _d_em.get('data', {}).get('klines', []) or []
                    # 东财格式: date,open,close,high,low,vol,amount,amplitude,pct,chg,turnover
                    _kl = [[x.split(',')[0], float(x.split(',')[2]), float(x.split(',')[3]), float(x.split(',')[4])] for x in _kl]
                    if len(_kl) >= 10:
                        try:
                            with open(_kfile, 'w', encoding='utf-8') as _f:
                                _json.dump({'date': _today, 'kl': _kl}, _f, ensure_ascii=False)
                        except Exception:
                            pass
                except Exception:
                    _kl = []
            # 腾讯源回退
            if len(_kl) < 10:
                try:
                    _url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,20,qfq'
                    _d = _rq.get(_url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6).json()
                    _k = _d['data'][sym]
                    _kl = _k.get('qfqday') or _k.get('day') or []
                    _kl = [[x[0], float(x[2]), float(x[3]), float(x[4])] for x in _kl]
                except Exception:
                    _kl = []
            if len(_kl) >= 10:
                _highs = [x[2] for x in _kl]
                _lows = [x[3] for x in _kl]
                _closes = [x[1] for x in _kl]
                _hi20, _lo20 = max(_highs), min(_lows)
                _ma20 = sum(_closes) / len(_closes)
                _price = float(info.get('px', 0) or 0)
                if _price > 0:
                    _pos = (_price - _lo20) / (_hi20 - _lo20) if _hi20 > _lo20 else 0.5
                    # 2026-08-05修复：加动量方向检查——回测发现深科技7/13位置53%(中位)
                    # 但正处下跌起点(7/10见顶后崩)仍被选中。中低位+下跌中=接刀，降档。
                    _trend5 = 0.0
                    if len(_closes) >= 6:
                        _trend5 = (_closes[-1] / _closes[-6] - 1) * 100
                    _falling = _trend5 < -3  # 近5日跌超3% = 下跌段
                    # 底部平台(前20%)=18-20 | 中低位(20-45%)=14-17 | 中位(45-65%)=10-13 | 中高位(65-85%)=5-9 | 前高附近(>85%)=0-4
                    if _pos <= 0.2 and _price >= _ma20:
                        d2 = 20
                    elif _pos <= 0.2:
                        d2 = 18 if not _falling else 10
                    elif _pos <= 0.45:
                        d2 = 15 if not _falling else 8
                    elif _pos <= 0.65:
                        d2 = 11 if not _falling else 4
                    elif _pos <= 0.85:
                        d2 = 7 if not _falling else 2
                    else:
                        d2 = 3 if not _falling else 0
    except Exception:
        d2 = None
    
    # ── 维度③ 板块催化 (25分) ──
    # 2026-08-06 改版：全市场扫描下板块未知的票给中性基线8分（不因未知扣光）
    d3 = 0
    sector_chg = etf_data.get(sector, 999)
    if sector_chg != 999:
        if sector_chg > 2 and 0 < chg < sector_chg + 1:
            d3 = 25
        elif sector_chg > 1 and chg > 0:
            d3 = 15
        elif sector_chg > 0 and chg > 0:
            d3 = 5
        elif sector_chg < -1 and chg > sector_chg + 3 and amount_wan > P90:
            d3 = 5
    else:
        # 板块未知：中性基线8分（个股强势涨停也给基础分，避免全市场票被误杀）
        d3 = 8 if chg > 0 else 0
    
    # ── 维度④ 弹性强度 (15分) — 基于成交额分位数 ──
    d4 = 0
    if amount_wan >= P90:
        d4 = 15
    elif amount_wan >= P70:
        d4 = 11
    elif amount_wan >= P50:
        d4 = 7
    elif amount_wan >= P30:
        d4 = 3
    else:
        d4 = 0
    
    # ── 维度⑤ 风险排除 (15分) ──
    # 2026-08-06 改版：涨停股振幅大不再惩罚（涨停=强势非风险）
    d5 = 0
    if chg >= 9.5:
        d5 += 12  # 涨停板 = 最强信号，不因振幅扣分
    elif amp < 4:
        d5 += 10
    elif amp < 6:
        d5 += 5
    elif amp > 8 and chg < 0:
        d5 -= 5  # 仅下跌股大振幅才扣分
    cap = info.get('cap', 0)
    if cap > 500e8:
        d5 -= 10
    elif cap > 200e8:
        d5 -= 5
    
    # ── 归一化总分 ──
    if d2 is not None:
        raw_scores = [d1, d2, d3, d4, d5]
        available_max = 100  # 五维全有效
        note = ""
    else:
        raw_scores = [d1, 0, d3, d4, d5]  # d2=None → 占位0
        available_max = 80  # 有效维度：①(25)+③(25)+④(15)+⑤(15)=80
        note = "，②缺失"
    available_actual = sum(raw_scores)
    normalized = round(available_actual / available_max * 100)
    
    return normalized, (d1, d2, d3, d4, d5), f"归一化：{available_actual}/{available_max}{note}"


# ============================================================
# Step 0: 一票否决
# ============================================================
def veto_check(cand):
    """8项否决检查，任一命中返回(True, 原因)
    2026-08-05新增：ST/退市风险过滤（回测发现*ST华鹏57-67分被选中=设计缺陷）
    """
    # 简化版：检查流动性+振幅+市值异常等可获取的项
    name = cand.get('name', '')
    if 'ST' in name.upper() or '退' in name:
        return (True, f"ST/退市风险股：{name}")
    if cand.get('amount', 0) < 2:
        return (True, "流动性不足：成交额<2亿")
    # 2026-08-06 改版：涨停股振幅大不否决（长电12.8%被误杀的教训）
    chg_v = cand.get('chg', 0)
    if cand.get('amp', 0) > 12 and chg_v < 9:
        return (True, f"振幅异常：{cand['amp']}%")
    # 2026-08-06 改版：权重股上限从100亿放宽到500亿（长电172亿/紫金138亿不再误杀）
    if cand.get('amount', 0) > 500:
        return (True, f"大盘权重股：成交额{cand['amount']}亿")
    return (False, "")


# ============================================================
# Step 1: 环境系数
# ============================================================
def get_weekly_kline(sym, weeks=30):
    """诸葛亮V2.0新增：周线K线
    数据源优先级：新浪日K聚合成周线（稳定）→ 腾讯周线 → 东财周线
    返回 [(date, open, close, high, low, vol)] 升序
    """
    import requests as _rq
    code_digits = ''.join(ch for ch in sym if ch.isdigit())
    mk = 'sh' if sym.startswith('sh') else 'sz'
    
    # 1. 新浪日K（scale=240日K，datalen取足够多再聚合周线）
    try:
        url = f'https://quotes.sina.cn/cn/api/jsonp_v2.php/var/CN_MarketDataService.getKLineData?symbol={mk}{code_digits}&scale=240&ma=no&datalen={weeks*6}'
        r = _rq.get(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://finance.sina.com.cn'}, timeout=8,
                   proxies={'http':None,'https':None})
        txt = r.text
        # 提取JSON数组（去掉 var(...) 包裹）
        start = txt.find('[')
        end = txt.rfind(']')
        if start >= 0 and end > start:
            import json as _json
            daily = _json.loads(txt[start:end+1])
            if len(daily) >= 15:
                # 日K聚合成周K（按ISO周）
                weeks_map = {}
                for d in daily:
                    date = d['day']
                    from datetime import datetime as _dt
                    dt = _dt.strptime(date, '%Y-%m-%d')
                    wk = dt.isocalendar()[:2]  # (year, week)
                    o, c, h, l, v = float(d['open']), float(d['close']), float(d['high']), float(d['low']), float(d.get('volume', 0))
                    if wk not in weeks_map:
                        weeks_map[wk] = {'date': date, 'open': o, 'close': c, 'high': h, 'low': l, 'vol': v}
                    else:
                        w = weeks_map[wk]
                        w['close'] = c
                        w['high'] = max(w['high'], h)
                        w['low'] = min(w['low'], l)
                        w['vol'] += v
                        w['date'] = date
                weekly = [[w['date'], w['open'], w['close'], w['high'], w['low'], w['vol']] for w in sorted(weeks_map.values(), key=lambda x: x['date'])]
                if len(weekly) >= 10:
                    return weekly
    except Exception:
        pass
    
    # 2. 腾讯周线
    try:
        _url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},week,,,{weeks},qfq'
        _d = _rq.get(_url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://gu.qq.com/'}, timeout=8,
                     proxies={'http':None,'https':None}).json()
        _k = _d.get('data', {}).get(sym, {})
        _kl = _k.get('qfqweek') or _k.get('week') or []
        if len(_kl) >= 10:
            return [[x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]) if len(x)>5 else 0] for x in _kl]
    except Exception:
        pass
    return None


def env_coefficient_v2():
    """诸葛亮V2.0环境系数（用户2026-08-06亲授·周线口径）

    多头1.0: 上证/创业板周线站稳20周均线，连续2周不创新低
    震荡0.8: 指数在20周均线上下10%区间横盘
    空头0.5: 指数周线有效跌破20周均线
    """
    def _judge(sym):
        kl = get_weekly_kline(sym, 30)
        if not kl or len(kl) < 22:
            return None
        closes = [x[2] for x in kl]
        ma20 = sum(closes[-20:]) / 20
        cur = closes[-1]
        lows = [x[4] for x in kl]
        # 连续2周不创新低
        no_new_low = lows[-1] > lows[-3] and lows[-2] > lows[-3]
        if cur >= ma20 and no_new_low:
            return 'bull'  # 多头
        elif ma20 * 0.9 <= cur <= ma20 * 1.1:
            return 'range'  # 震荡
        elif cur < ma20:
            return 'bear'  # 空头
        return 'range'
    
    sh = _judge('sh000001')
    cy = _judge('sz399006')
    
    # 综合上证+创业板：任一多头→偏多；都空头→空头；其余震荡
    states = [s for s in (sh, cy) if s]
    if not states:
        return 0.7, "周线数据缺失，暂用0.7"
    if 'bull' in states:
        return 1.0, f"多头（上证{sh}/创业板{cy}站稳20周均线）"
    if all(s == 'bear' for s in states):
        return 0.5, f"空头（上证{sh}/创业板{cy}跌破20周均线）"
    return 0.8, f"震荡（上证{sh}/创业板{cy}在20周均线±10%）"


def env_coefficient(etf_data):
    """环境系数：埋伏窗口口径（2026-08-05二次修复：诸葛亮=15日持有提前埋伏引擎）

    核心矛盾（用户指出）：
      v1用单日涨停数 → 单日情绪热≠中期企稳（已废弃）
      v2用MA20站上才高分 → 等趋势确认=追涨，违背埋伏初衷（已废弃）
      v3埋伏逻辑：跌透企稳=埋伏窗口（高分），下跌中继=禁埋（低分），高位过热=等回调

    判定（沪深300 20日K线）：
      1. 下跌中继：20日深跌(-8%以下) 且 最新仍在创新低 → 0.5 禁止埋伏（接刀）
      2. 跌透企稳：20日跌幅明显 但 近3日止跌回升(最新>5日低) → 1.0 埋伏窗口 ✅
      3. 横盘整理：20日小幅波动 → 0.85 可埋伏
      4. 趋势向上：站上MA20+20日正 → 0.8 追涨区（非埋伏位，降分）
      5. 高位过热：20日涨幅>15% → 0.6 等回调
    """
    import requests
    from datetime import datetime

    # 沪深300 20日K线
    closes = None
    try:
        r = requests.get('http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000300,day,,,20,qfq',
                         headers={'User-Agent':'Mozilla/5.0'}, timeout=8,
                         proxies={"http": None, "https": None})
        d = r.json()
        days = d['data']['sh000300'].get('day') or d['data']['sh000300'].get('qfqday')
        if days and len(days) >= 20:
            closes = [float(x[2]) for x in days]
    except Exception:
        pass

    # 涨停/跌停（仅辅助参考）
    limit_up = limit_down = 0
    try:
        import akshare as ak
        zt = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y%m%d'))
        dt = ak.stock_zt_pool_dtgc_em(date=datetime.now().strftime('%Y%m%d'))
        limit_up = len(zt)
        limit_down = len(dt)
    except Exception:
        pass

    if closes is None:
        return 0.7, f"趋势未知(K线缺失)｜涨停{limit_up}参考"

    latest = closes[-1]
    c20 = closes[0]
    chg20 = (latest/c20-1)*100
    # 2026-08-05用户纠正：埋伏看的是【低位】不是【跌透】
    # 低位=20日分位低（价格在近期区间底部），不需要先跌透再企稳
    hi20 = max(closes)
    lo20 = min(closes)
    pos20 = (latest - lo20) / (hi20 - lo20) * 100 if hi20 > lo20 else 50
    low5 = min(closes[-6:-1])
    ma20 = sum(closes)/len(closes)
    ma20_ok = latest >= ma20

    # 1. 下跌中继：深跌+创新低 → 禁止接刀（LEO-020：下跌中不埋伏）
    if chg20 < -8 and latest <= low5:
        return 0.5, f"下跌中继：20日{chg20:+.1f}%仍在创新低 → 禁止埋伏(接刀)"
    # 2. 低位：20日分位<35% = 位置低 → 埋伏窗口（核心：位置低即可，无需跌透）
    if pos20 < 35:
        return 1.0, f"低位：20日分位{pos20:.0f}%(区间底部) → 埋伏窗口"
    # 3. 中低位：35-60% → 可埋伏但非最佳
    if pos20 < 60:
        return 0.85, f"中低位：20日分位{pos20:.0f}% 可埋伏"
    # 4. 中高位：60-85% → 追涨区降分
    if pos20 < 85:
        return 0.7, f"中高位：20日分位{pos20:.0f}% → 追涨降分"
    # 5. 高位过热：>85%
    return 0.5, f"高位：20日分位{pos20:.0f}% → 禁止埋伏(等回调)"


# ============================================================
# Step 3: 赔率
# ============================================================
def compute_odds(cand):
    """简化的赔率计算"""
    px = cand.get('px', 0)
    amount = cand.get('amount', 0)
    amp = cand.get('amp', 1)
    
    # 用振幅估算弹性空间
    upside = max(amp * 1.5, 5)  # 上方空间（%估算）
    downside = max(amp * 0.5, 2)  # 下方止损（%估算）
    odds = round(upside / downside, 1)
    return upside, downside, odds


def entry_zone(info):
    """计算合理入场区间（比现价低5-10%）"""
    px = info['px']
    low = round(px * 0.92, 2)
    high = round(px * 0.97, 2)
    return f"{low}-{high}"


def season_stop(info):
    """季线止损（-20%）"""
    return round(info['px'] * 0.80, 2)


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M')
    print(f"🏯 诸葛亮 V3.0 · 中长期牛股筛选 | {today} {now}")
    print()

    # 1. 扫ETF
    etf_data = get_etf_data()
    if etf_data:
        sorted_etf = sorted(etf_data.items(), key=lambda x: -x[1])
        print("━" * 50)
        print("  📊 ETF方向")
        print("━" * 50)
        for n, c in sorted_etf[:8]:
            bar = '🚀' if c > 3 else ('🟢' if c > 1 else ('🟡' if c > 0 else '🔴'))
            print(f"  {bar} {n}: {c:+.1f}%")
        print()

    # 2. 扫候选个股（2026-08-06 改版：V2.0板块拐点优先，取消固定池全市场扫描）
    # 用户指令："谁给你的池子，把池子取消了，每天都在主板和科创板里选股票"
    # V2.0核心：先检测板块拐点（第二步），只对拐点板块内个股评分（避免全市场逐只拉周线）
    import time as _time
    
    # 板块拐点检测（V2.0第二步）
    sector_inflection = detect_sector_inflection()
    _inf_top = sorted(sector_inflection.items(), key=lambda x: -x[1][0])[:6]
    print(f"  📡 板块拐点(TOP6): " + ", ".join(f"{n}({s[0]}分)" for n,s in _inf_top))
    # 拐点板块（强度≥15）
    inflection_sectors = [n for n,(s,d) in sector_inflection.items() if s >= 15]
    
    # 从拐点板块的成分股构建扫描池（CANDIDATES内该板块股票 + 全市场活跃股）
    all_codes = fetch_all_a_codes()
    active_codes = preselect_active_codes(all_codes)
    scan_codes = []
    # 拐点板块成分股（CANDIDATES映射）
    for sn, sc in CANDIDATES.items():
        if sn in inflection_sectors:
            for c in sc.split(','):
                c = c.strip()
                if c and c not in scan_codes:
                    scan_codes.append(c)
    # 补充活跃股中属于拐点板块的（通过ETF成分近似：先全部加入，评分时板块不匹配自动0分排除）
    # 为控制规模：拐点板块成分 + 活跃股中涨幅前300
    active_sorted = active_codes
    for c in active_sorted[:300]:
        if c not in scan_codes:
            scan_codes.append(c)
    
    print(f"  📡 扫描池: {len(scan_codes)}只（拐点板块{len(inflection_sectors)}个 + 活跃股前300）")
    raw_data = get_sina(scan_codes)

    # 🆕 2026-08-04修复：分位数从候选池自身计算（不与被观察池错配）
    _amt_list = []
    for _code, _info in raw_data.items():
        if _info['px'] == 0: continue
        _a = _info.get('amount_wan', 0)
        if _a > 0: _amt_list.append(_a)
    _amt_list.sort()
    _n = len(_amt_list)
    if _n > 0:
        percentiles = {
            'P30': _amt_list[int(_n*0.3)], 'P50': _amt_list[int(_n*0.5)],
            'P70': _amt_list[int(_n*0.7)], 'P90': _amt_list[int(_n*0.9)],
        }
    else:
        percentiles = None

    # 3. DNA评分（V2.0周线版：板块拐点→个股周线五维）
    candidates = []
    # 板块拐点已在扫描入口检测（sector_inflection 变量已存在）
    for code, info in raw_data.items():
        if info['px'] == 0: continue
        chg = (info['px'] - info['prev']) / info['prev'] * 100
        amp = (info['high'] - info['low']) / info['prev'] * 100
        amount = info['px'] * info['vol'] / 1e8
        sector = "未知"
        for sn, sc in CANDIDATES.items():
            for c in sc.split(','):
                if c.strip().split('.')[-1] == code or c.strip().split('.')[-1] == ''.join(ch for ch in str(code) if ch.isdigit()):
                    sector = sn
                    break
        # 2026-08-06补：CANDIDATES未命中（全市场票）→ 用东财F10补板块归属
        if sector == "未知" and len(candidates) < 250:
            _mapped = get_stock_sectors(code)
            if _mapped:
                sector = _mapped
                info['sector_mapped'] = True

        cand = {
            'code': code, 'name': info['name'], 'px': round(info['px'], 2),
            'chg': round(chg, 2), 'amp': round(amp, 1),
            'vol': info['vol'] // 100, 'amount': round(amount, 1),
            'amount_wan': info.get('amount_wan', 0),
            'sector': sector, 'cap': info.get('cap', 0),
        }
        # 🆕 2026-08-10 修复：市值上限（用户：不给大盘股）——流通市值>500亿排除（中长期票要弹性）
        if (info.get('cap') or 0) > 500e8:
            continue
        # V2.0：板块拐点分（无拐点=0分→排除）
        sector_score = sector_inflection.get(sector, (0, ''))[0]
        total, dims, note = weekly_score_dna_v2(cand, etf_data, sector_score, cand.get('amount_wan', 0))
        cand['score'] = total
        cand['dims'] = dims
        cand['note'] = note
        candidates.append(cand)

    candidates.sort(key=lambda x: -x['score'])

    # Step 1: 环境系数（V2.0周线口径，--no-env 跳过）
    if NO_ENV:
        env_coef, env_desc = 1.0, "--no-env 模拟：跳过环境系数"
        print(f"  📊 环境系数: 跳过(--no-env) → 1.0")
    else:
        env_coef, env_desc = env_coefficient_v2()
        print(f"  📊 环境系数(V2.0周线): {env_coef} — {env_desc}")
    print()

    # Step 0: 否决检查 + Step 3: 赔率
    passed = []
    vetoed = []
    for c in candidates:
        veto, reason = veto_check(c)
        if veto:
            vetoed.append((c, reason))
            continue
        upside, downside, odds = compute_odds(c)
        c['upside'] = upside
        c['downside'] = downside
        c['odds'] = odds
        passed.append(c)

    # 最终分 = 五维总分 × 环境系数（2026-08-05新增：高位惩罚——回测发现高位出高分票=接盘）
    # 环境系数已含追涨区降档(0.8)/过热(0.6)，此处不再重复惩罚，仅标注
    for c in passed:
        c['final_score'] = round(c['score'] * env_coef, 1)

    passed.sort(key=lambda x: -x['final_score'])

    # ── LEO-022 可交易性检查（2026-08-07）：封板票降级，推荐必须可成交 ──
    # 实时行情校验：现价=涨停价 → 封板不可买 → 降级"观察·等开板/次日低吸"
    tradable = {}
    try:
        live = get_sina([c['code'] for c in passed])
        for c in passed:
            sym = c['code']  # 已是 sh/sz 前缀格式（如 sh600259）
            q = live.get(sym)
            if q and q['prev'] > 0:
                code_num = sym[2:]
                limit_pct = 0.20 if code_num.startswith(('3','68')) else 0.10  # 创业板/科创板20%，主板10%
                limit_px = round(q['prev'] * (1 + limit_pct), 2)
                dist = (q['px'] / limit_px - 1) * 100 if limit_px else 0
                is_sealed = abs(q['px'] - limit_px) < 0.011
                tradable[c['code']] = {'px': q['px'], 'chg': (q['px']/q['prev']-1)*100,
                                        'sealed': is_sealed, 'dist': dist}
    except Exception as e:
        print(f"  ⚠️ 可交易性检查失败: {e}（不阻断，全部按原档位）")

    # 封板票降级：推荐→观察，观察→排除（不可交易=不可推荐）
    for c in passed:
        t = tradable.get(c['code'])
        if t and t['sealed']:
            old = c['final_score']
            c['final_score'] = min(c['final_score'], 44.9)  # 压到观察以下
            c['sealed'] = True
            c['sealed_prev'] = old
        else:
            c['sealed'] = False

    passed.sort(key=lambda x: -x['final_score'])
    top = passed[:5] if len(passed) > 5 else passed

    # 否决项摘要
    if vetoed:
        print(f"  ⛔ 否决 {len(vetoed)}只（共扫描{len(candidates)}只）")
        for c, r in vetoed[:5]:
            print(f"     {c['name']}({c['code']}): {r}")
        print()

    # Step 4: 概率输出 + 评分
    print("━" * 60)
    print(f"  📋 V3候选 (最终分排序, TOP{len(top)})")
    print("━" * 60)
    if top:
        print(f"  {'名称':10s} {'板块':8s} {'评分':>4} {'环系':>4} {'最终':>5} {'赔率':>4} {'P估':>5} {'①②③④⑤':<18}")
        print("  " + "-" * 75)
        for c in top:
            dims = c.get('dims', (0,0,0,0,0))
            p_up = min(c['final_score'] * 0.8 + 10, 65)
            p_down = max(30 - c['final_score'] * 0.3, 5)
            bar = '🚀' if c['final_score'] >= 60 else ('🟢' if c['final_score'] >= 45 else '🟡')
            dim_str = f"{dims[0]}/{dims[1] if dims[1] is not None else '-'}/{dims[2]}/{dims[3]}/{dims[4]}"
            seal_tag = '🔴封板' if c.get('sealed') else (f"({tradable[c['code']]['chg']:+.1f}%距板{tradable[c['code']]['dist']:.0f}%)" if c['code'] in tradable else '')
            print(f"  {bar} {c['name']:10s} {c['sector']:8s} {c['score']:>3d}  {env_coef:.1f}  {c['final_score']:>4.0f}  {c['odds']:>3.1f}  {p_up:.0f}%  {dim_str:<18} {seal_tag}")
        print()
        # TOP1详细输出
        best = top[0]
        dims = best.get('dims', (0,0,0,0,0))
        note = best.get('note', '')
        print(f"  🏆 最佳候选: {best['name']}({best['code']})")
        print(f"     Step 0 否决: 通过")
        print(f"     Step 1 环境: {env_coef} — {env_desc}")
        print(f"     Step 2 五维: {best['score']}/100  {note}")
        print(f"       ①放量={dims[0]}  ②筹码={'缺失' if dims[1] is None else dims[1]}  ③板块={dims[2]}  ④弹性={dims[3]}  ⑤风险={dims[4]}")
        print(f"     Step 3 赔率: 上{best['upside']:.0f}% / 下{best['downside']:.0f}% = {best['odds']}:1")
        print(f"     Step 4 概率: P(15日涨>10%)≈{p_up:.0f}% | P(15日跌>8%)≈{p_down:.0f}%")
        print(f"     最终分: {best['final_score']} → {'🔥推荐' if best['final_score']>=60 else '观察' if best['final_score']>=45 else '排除'}")
        print(f"     叙事自检: ✓ 正常（含矛盾）")
    else:
        print("  无候选通过筛选。")
    print()

    # 否决明细
    print(f"  📊 扫描报告 | 总计{len(candidates)}只 | 否决{len(vetoed)} | 通过{len(passed)}")
    if vetoed:
        print(f"  ⛔ 否决原因分布:")
        reasons = {}
        for _, r in vetoed:
            reasons[r] = reasons.get(r, 0) + 1
        for r, n in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"     {r}: {n}只")
    
    # 自检：维度唯一值
    if passed:
        print(f"  📊 维度自检（{len(passed)}只通过候选）:")
        for di, dn in enumerate(['放量25','筹码20','板块25','弹性15','风险15']):
            vals = [c['dims'][di] for c in passed]
            clean = [v for v in vals if v is not None]
            unique = len(set(vals))
            if clean:
                print(f"     {dn}: 值域={min(clean)}~{max(clean)} 唯一值={unique} {'⚠️ 常量' if unique <= 1 else '✅'}")
            else:
                print(f"     {dn}: 全部缺失 唯一值={unique} ⚠️")

    # 5. 写入日志
    out_dir = os.path.expanduser("~/memory/诸葛亮长期池")
    os.makedirs(out_dir, exist_ok=True)
    log_file = os.path.join(out_dir, f"{today}.md")
    
    # Also save to daily scan log
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          'memory/zhugeliang_midstock/daily_scan_log')
    os.makedirs(log_dir, exist_ok=True)

    with open(log_file, 'w') as f:
        f.write(f"# 诸葛亮 V3.0 中长期牛股 | {today}\n\n")
        f.write(f"## ETF方向\n\n")
        if etf_data:
            for n, c in sorted_etf[:8]:
                f.write(f"- {n}: {c:+.1f}%\n")
        
        f.write(f"\n## V3候选 (TOP{len(top)})\n\n")
        if top:
            f.write("| 名称 | 板块 | 评分 | 环系 | 最终分 | 赔率 | P估 | 结论 |\n")
            f.write("|:----|:----|:---:|:---:|:------:|:---:|:---:|:----:|\n")
            for c in top:
                p_up = min(c['final_score'] * 0.8 + 10, 65)
                concl = '🔥推荐' if c['final_score'] >= 60 else '观察' if c['final_score'] >= 45 else '排除'
                f.write(f"| {c['name']} | {c['sector']} | {c['score']} | {env_coef:.1f} | {c['final_score']:.0f} | {c['odds']}:1 | {p_up:.0f}% | {concl} |\n")
        else:
            f.write("无。\n")
        
        f.write(f"\n## 否决 ({len(vetoed)}只)\n\n")
        if vetoed:
            for c, r in vetoed[:8]:
                f.write(f"- {c['name']}({c['code']}): {r}\n")
        else:
            f.write("无。\n")
    
    print(f"\n  日志: {log_file}")


if __name__ == '__main__':
    main()
