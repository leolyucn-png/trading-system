#!/usr/bin/env python3
"""
孙权 V3.0 — 超短线龙头模式 · 打板评估
============================================
独立数据系统（不依赖任何模型）
资金：¥1,000/笔（建议¥3,000–5,000）
时点：9:45主扫描 | 10:15复扫 | 14:50持仓处置

输出（用户2026-07-26亲授）：
  - 情绪周期 + 动态阈值
  - 五维评分（板块分改相对排名 + 地位分改梯队时间）
  - 透支扣分（−30分反向维度）
  - P(封板) + P(高开) + P(盈利出局) 概率
  - 卖出预案（T日+T+1日）
"""

import os, sys, json, datetime as dt, requests, re

TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0"}
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SECTOR_ETFS = {
    "半导体":"sh512480","芯片":"sz159995","有色":"sh512400","新能源":"sh516160",
    "光伏":"sh515790","军工":"sh512660","银行":"sh512800","证券":"sh512880",
    "AI":"sz159819","通信":"sh515880","机器人":"sh562500","医药":"sh512010",
    "消费":"sz159928","酒":"sh512690","软件":"sh515230","养殖":"sz159865",
}

# ============================================================
# 独立数据层
# ============================================================

def get_etf_prices():
    """独立拉ETF行情"""
    etf_data = {}
    names = {}
    codes = ",".join(SECTOR_ETFS.values())
    try:
        r = requests.get(f"http://hq.sinajs.cn/list={codes}",
                         headers={"Referer":"http://finance.sina.com.cn",**HEADERS}, timeout=6)
        r.encoding = 'gbk'
        for line in r.text.strip().split('\n'):
            if not line.strip() or '"' not in line: continue
            parts = line.split('"')[1].split(',')
            px, prev = float(parts[3]), float(parts[2])
            chg = (px - prev) / prev * 100 if prev else 0
            for name, sym in SECTOR_ETFS.items():
                if sym in line.lower() or sym.replace('sh','').replace('sz','') in line:
                    etf_data[name] = round(chg, 2)
                    names[name] = parts[0]
                    break
    except:
        pass
    return etf_data


def get_market_sentiment():
    """市场情绪：akshare主力 + 东财备源"""
    result = {"limit_up": 0, "limit_down": 0, "total_trade": 0, "up_count": 0, "down_count": 0}
    
    # 涨停/跌停: akshare（独立源，不依赖东财push2）
    try:
        import akshare as ak
        zt = ak.stock_zt_pool_em(date=dt.datetime.now().strftime("%Y%m%d"))
        _dtgc = ak.stock_zt_pool_dtgc_em(date=dt.datetime.now().strftime("%Y%m%d"))
        result['limit_up'] = len(zt)
        result['limit_down'] = len(_dtgc)
    except:
        # 备源：东财push2（可能502）
        try:
            r = requests.get(
                "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=0&np=1&fltt=2&fid=f3&fs=m:0+t:6+f:50&fields=f3",
                headers=HEADERS, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if data.get('data') and data['data'].get('total'):
                    result['limit_up'] = int(data['data']['total'])
        except:
            pass
        try:
            r = requests.get(
                "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&fid=f3&fs=m:0+t:6+f:52&fields=f3",
                headers=HEADERS, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if data.get('data') and data['data'].get('total'):
                    result['limit_down'] = int(data['data']['total'])
        except:
            pass
    
    # 涨跌家数: 用日K缓存估算（东财502时不可用）
    # 源已坏：东财push2全天502，腾讯/Sina无此字段
    return result


def get_stock_quotes(codes):
    """独立拉个股行情（腾讯QT+Sina双源）"""
    result = {}
    batch_size = 20
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        symbols = ','.join(['sh'+c if c.startswith(('6','9')) else 'sz'+c for c in batch])
        try:
            r = requests.get(f'http://qt.gtimg.cn/q={symbols}',
                             headers=HEADERS, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip() or '~' not in line: continue
                f = line.split('~')
                if len(f) < 40: continue
                code = f[0].split('_')[-1].split('=')[0][2:]
                result[code] = {
                    "name": f[1], "price": float(f[3]) if f[3] else 0,
                    "prev": float(f[4]) if f[4] else 0,
                    "vol_ratio": float(f[49]) if len(f)>49 and f[49] else 0,
                    "volume": int(f[6]) if f[6] else 0,
                    "amount": float(f[37]) if f[37] else 0,
                    "high": float(f[33]) if f[33] else 0,
                    "low": float(f[34]) if f[34] else 0,
                    "open": float(f[5]) if f[5] else 0,
                    "float_cap": float(f[44]) if len(f)>44 and f[44] else 0,  # 2026-08-03: 流通市值(亿)
                    "pct": (float(f[3]) - float(f[4])) / float(f[4]) * 100 if f[3] and f[4] and float(f[4]) else 0,
                }
        except:
            pass
    # Sina补缺
    missing = [c for c in codes if c not in result]
    if missing:
        try:
            symbols = ','.join(['sh'+c if c.startswith(('6','9')) else 'sz'+c for c in missing])
            r = requests.get(f'http://hq.sinajs.cn/list={symbols}',
                             headers={"Referer":"http://finance.sina.com.cn",**HEADERS}, timeout=6)
            r.encoding = 'gbk'
            for line in r.text.strip().split('\n'):
                if not line.strip() or '"' not in line: continue
                parts = line.split('"')[1].split(',')
                code = line.split('_')[-1].split('=')[0][2:]
                if code not in result and len(parts) > 30:
                    px, prev = float(parts[3]), float(parts[2])
                    result[code] = {
                        "name": parts[0], "price": px, "prev": prev,
                        "vol_ratio": 0, "volume": 0, "amount": float(parts[9]) if parts[9] else 0,
                        "high": float(parts[4]), "low": float(parts[5]), "open": float(parts[1]),
                        "pct": (px - prev) / prev * 100 if prev else 0,
                    }
        except:
            pass
    return result


def get_top_gainers(n=30):
    """独立拉今日涨幅榜（东财优先 → Sina回退）"""
    # 主源：东财
    em_ok = False
    try:
        r = requests.get(
            f"https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={n}&po=1&np=1&fltt=2&fid=f3&fs=m:0+t:1&fields=f2,f3,f12,f14,f62,f100",
            headers=HEADERS, timeout=6)
        if r.status_code == 200:
            j = r.json()
            if j and j.get('data') and j['data'].get('diff'):
                items = j['data']['diff']
                em_ok = True
                return [{
                    "code": s['f12'], "name": s['f14'],
                    "price": s.get('f2',0), "pct": s.get('f3',0),
                    "net_inflow": s.get('f62',0),
                    "sector": s.get('f100','未知'),  # 2026-08-03：所属行业（准涨停池板块映射）
                } for s in items[:n] if abs(s.get('f3',0)) <= 10]
    except:
        pass
    # 回退：Sina行情中心（东财502时用）
    try:
        rows = []
        for page in range(1, 12):
            url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
            r = requests.get(url, params={"page":page,"num":80,"sort":"changepercent","asc":0,"node":"hs_a","symbol":"","_s_r_a":"init"},
                             headers={"User-Agent":"Mozilla/5.0","Referer":"http://finance.sina.com.cn"}, timeout=10)
            d = r.json()
            if not d: break
            rows += d
            if float(d[-1].get('changepercent', 0) or 0) < 5:
                break
        return [{
            "code": s.get('code',''), "name": s.get('name',''),
            "price": float(s.get('trade',0) or 0), "pct": float(s.get('changepercent',0) or 0),
            "net_inflow": 0, "sector": '未知',
        } for s in rows if 5 <= float(s.get('changepercent',0) or 0) <= 10][:n]
    except:
        pass
    return []


# ============================================================
# 情绪周期判定（独立数据驱动）
# ============================================================

def get_qianfu_pool():
    """孙权潜伏票候选池（2026-08-03用户亲授：找今天没启动、明天可能被游资拉的票）
    🆕 2026-08-11 A方案重构（用户拍板）：来源从「当日资金方向」改为「张飞TOP3轮入板块」，
        资金方向只做inflow标注（不做出入池条件）——根治追涨：只埋伏预判轮入板块。
    🆕🆕 2026-08-12 B方案升级（用户拍板）：**全板块扫描**——不限于张飞TOP3，
        全市场板块内寻找「妖股基因」：低价(<20元)+小市值(<100亿)+缩量+未启动(-3~+5%)
        张飞预判变为评分项（加分/降级），不再是入池门槛。
    返回 (list, fund_sectors)
    """
    import json, os
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    fund_sectors = {}
    fund_path = os.path.join(SCRIPT_DIR, '..', 'memory', 'guanyu_fund_direction.json')
    if os.path.exists(fund_path):
        try:
            fdir = json.load(open(fund_path))
            for s in fdir.get('sectors', []):
                if (s.get('inflow') or 0) >= 3:
                    fund_sectors[s['name']] = s['inflow']
        except Exception:
            pass
    pool = {}
    pool_path = os.path.join(SCRIPT_DIR, 'guanyu_pool.json')
    if os.path.exists(pool_path):
        try:
            pool = json.load(open(pool_path)).get('sectors', {})
        except Exception:
            pass
    # 🆕 2026-08-12 B方案：全板块扫描（不再依赖张飞TOP3为入口，张飞只做评分）
    # 板块名→资金方向名 模糊匹配（inflow标注用）
    fund_alias = {
        'HJT电池': '光伏', '光伏设备': '光伏', '钙钛矿电池': '光伏',
        '绿色电力': '电力', '智能电网': '电网', '抽水蓄能': '电力',
        '核能核电': '核电', '可控核聚变': '核电', '雅下水电概念': '电力',
        '新能源': '新能源', '商业航天': '商业航天',
        'PCB': '通信', '通信技术': '通信', '5G概念': '通信', '光通信模块': '通信',
        '半导体概念': '半导体', '芯片': '芯片', '华为概念': '芯片', '国产芯片': '芯片',
        'AI': 'AI', '人工智能': 'AI', '算力': 'AI', '数据中心': 'AI',
        '软件': '软件', '信创': '软件', '游戏': '游戏', '传媒': '游戏',
        '机器人': '机器人', '工业机器人': '机器人',
        '军工': '军工', '商业航天': '军工',
        '有色金属': '有色', '黄金': '有色', '稀土': '有色',
        '光伏': '光伏', '储能': '新能源', '新能源车': '新能源',
        '医药': '医药', '医疗': '医疗', '创新药': '医药',
        '证券': '证券', '银行': '银行', '保险': '证券',
        '消费电子': '消费电子', '家电': '消费', '白酒': '酒', '消费': '消费',
        '养殖': '养殖', '农业': '养殖',
    }
    out = []
    seen = set()
    # 🆕 2026-08-12 妖股基因参数（由8/12六妖股解剖固化）
    #   传智5元/北京文化3.5元/百花7元/泰坦41元(深跌)/蓝盾16元/云赛18元
    PRICE_MAX = 25      # 启动价普遍<25元（低价=游资最爱）
    MCAP_MAX = 200      # 2026-08-13 用户指令：放宽到<200亿（移远通信198亿成功案例：8/10入池→8/13涨停）
    for k, v in pool.items():
        name = v.get('name', '')
        sector = v.get('sector', '') or ''
        name_clean = name.replace('ETF', '').strip()
        zsector = sector or name_clean
        # inflow标注（仅标注，不做入池条件）
        inflow = 0
        for fn, iv in fund_sectors.items():
            if (zsector and (zsector in fn or fn in zsector)) or (name_clean in fn or fn in name_clean):
                inflow = max(inflow, iv)
        for fn, alias in fund_alias.items():
            if fn in fund_sectors and ((alias and zsector and alias in zsector) or (alias in name_clean or name_clean in alias)):
                inflow = max(inflow, fund_sectors[fn])
        for st in v.get('stocks', []):
            sym = st.get('sym', '')
            nm_st = st.get('name', '') or ''
            if not sym or sym in seen:
                continue
            # 🆕 2026-08-12 用户铁律：买不了科创板 → 688开头一律排除（孙权/刘彻/诸葛亮三模型同规则）
            if sym.startswith('688'):
                continue
            # 🆕 2026-08-12 补充：北交所(920/8/4开头)排除 + ST排除（普通账户不可买/风险票不推）
            if sym.startswith(('920', '8', '4')):
                continue
            if 'ST' in nm_st.upper() or '退' in nm_st:
                continue
            chg = st.get('chg', 0)
            mcap = (st.get('mcap') or 0) / 1e8
            price = st.get('price', 0) or 0
            vr = st.get('vr', 0) or 0
            # 🆕 2026-08-12 妖股基因过滤：未启动(-3~+5%) + 低价(<25元) + 小市值(<100亿)
            if not (-3 <= chg <= 5):
                continue  # 未启动：-3%~+5%
            if mcap > MCAP_MAX or mcap <= 0:
                continue  # 妖股市值上限100亿
            if 0 < price < PRICE_MAX * 0.4:
                continue  # 低于10元超低价有ST/退市风险嫌疑，过滤（保留10-25元）
            if price > PRICE_MAX:
                continue  # 低价妖股基因：>25元不入选
            seen.add(sym)
            out.append({
                'sym': sym, 'name': st.get('name', ''),
                'sector': zsector, 'chg': chg, 'inflow': inflow,
                'amount': st.get('amount', 0), 'mcap': mcap,
                'vr': vr, 'amp': st.get('amp', 0),
                'price': price,
                'zf_panel': zsector,
            })
    if not out:
        print("   ⚠️ 全板块无「妖股基因」未启动股（低价<25元+小市值<100亿+未启动） → 潜伏池空（宁缺毋滥）")
    else:
        print(f"   🆕 B方案：全板块妖股基因池（低价<25元+市值<100亿+未启动） {len(out)}只")
    return out, fund_sectors


_POS20_CACHE = {}  # 🆕 2026-08-10 分位缓存：避免潜伏池重复请求

# 🆕 2026-08-11 张飞预判接入：板块→张飞评分（读取zhangfei_rotation.json）
_ZHANGFEI_CACHE = {}
def get_zhangfei_scores():
    """读取张飞轮动预测，返回 {板块名: {score, pos, rank}}；失败返回 {}"""
    global _ZHANGFEI_CACHE
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                         'memory', 'zhangfei_output', 'zhangfei_rotation.json')
        if not os.path.exists(p):
            return {}
        d = json.load(open(p))
        full = d.get('full_ranking') or d.get('prediction') or []
        out = {}
        for i, sec in enumerate(full):
            out[sec.get('name')] = {'score': sec.get('score', 0),
                                     'pos': sec.get('pos', None),
                                     'rank': i + 1}
        return out
    except Exception:
        return {}


def zhangfei_panel(stock_sector):
    """张飞预判标注：返回 (delta_score, label)。<50分板块降级（2026-08-11用户拍板）
    2026-08-11 14:05修订：降级力度-10→-30（-10不足以压过基础分，光伏票仍可买入=没执行回避）"""
    zf = get_zhangfei_scores()
    if not zf:
        return 0, ''
    # 板块名归一化：pool板块名如'半导体ETF'→'半导体'
    nm = (stock_sector or '').replace('ETF', '').strip()
    hit = zf.get(nm)
    if not hit:
        # 尝试模糊匹配
        for k, v in zf.items():
            if k in nm or nm in k:
                hit = v
                break
    if not hit:
        return 0, ''
    sc = hit.get('score', 0)
    if sc >= 70:
        return 5, f"张飞{sc:.0f}分TOP({hit.get('rank')})·轮入+5"
    elif sc >= 50:
        return 2, f"张飞{sc:.0f}分·中性+2"
    else:
        return -30, f"张飞{sc:.0f}分·回避榜({hit.get('rank')})·降级-30"

def get_pos20(sym):
    """腾讯日K 60日 → 20日分位（埋伏标准②：低位<40%） 失败返回None"""
    if sym in _POS20_CACHE:
        return _POS20_CACHE[sym]
    if not sym:
        return None
    _s = str(sym).strip()
    # 🆕 2026-08-10：pool.sym可能是裸6位代码，补交易所前缀
    if _s.isdigit() and len(_s) == 6:
        _s = f"sh{_s}" if _s.startswith(('5', '6')) else f"sz{_s}"
    try:
        import requests as _rq
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={_s},day,,,60,qfq'
        d = _rq.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4).json()
        kl = d['data'][_s].get('qfqday') or d['data'][_s].get('day') or []
        if len(kl) < 21:
            _POS20_CACHE[sym] = None
            return None
        rows = [{'high': float(k[3]), 'low': float(k[4]), 'close': float(k[2])} for k in kl]
        hi20 = max(r['high'] for r in rows[-20:])
        lo20 = min(r['low'] for r in rows[-20:])
        px = rows[-1]['close']
        _POS20_CACHE[sym] = (px - lo20) / (hi20 - lo20) * 100 if hi20 > lo20 else 50.0
        return _POS20_CACHE[sym]
    except Exception:
        _POS20_CACHE[sym] = None
        return None


def _zhangfei_sector_score(sector_name):
    """V2.2（2026-08-14）：板块明日轮入方向分（张飞rotation）。失败返回None（回退关羽当天资金）
    2026-08-14曹操校准：潜伏赌明天，板块维度必须用张飞「明日轮入方向」而非关羽「当天资金流入”
    （永安109=医药当天+36亿→次日熄火；蓝箭98被扣分→次日+15%——当天资金强=已price in）
    """
    try:
        zf = get_zhangfei_scores()
        if not zf:
            return None
        nm = (sector_name or '').replace('ETF', '').strip()
        hit = zf.get(nm)
        if not hit:
            for k, v in zf.items():
                if k in nm or nm in k:
                    hit = v
                    break
        if not hit:
            return None
        return hit.get('score')
    except Exception:
        return None


def score_qianfu_v1(stock, pos20=None):
    """孙权潜伏票评分 V1（2026-08-03用户亲授：明天最可能被游资拉的票）
    ①板块资金20 ②启动信号30 ③游资偏好25 ④蓄势形态15 ⑤风险10
    V2.2（2026-08-14曹操校准）：①板块资金口径换源——关羽当天资金→张飞明日轮入方向
    病根：潜伏赌明天，板块维度却用昨天的钱（永安109=医药当天+36亿→次日熄火；蓝箭98被扣分→次日+15%）
    """
    s = 0
    detail = {}
    inflow = stock.get('inflow', 0)
    chg = stock.get('chg', 0)
    mcap = stock.get('mcap', 0)
    vr = stock.get('vr', 0) or 0
    amount = stock.get('amount', 0) or 0
    amp = stock.get('amp', 0) or 0

    # ① 板块资金 20（V2.2换源：张飞「明日轮入方向」优先，关羽当天资金仅标注）
    zf_sector_score = _zhangfei_sector_score(stock.get('sector', ''))
    if zf_sector_score is not None:
        # 张飞明日轮入方向（潜伏赌明天）：TOP轮入→20，中性偏上→16，中性→12，回避→8
        if zf_sector_score >= 70:
            d1 = 20
        elif zf_sector_score >= 55:
            d1 = 16
        elif zf_sector_score >= 45:
            d1 = 12
        else:
            d1 = 8
        detail['板块资金'] = f"{d1}/20 (张飞明日{zf_sector_score:.0f}分)"
    else:
        # 张飞盲区回退：关羽当天资金（标注口径=当天，不代表次日方向）
        if inflow >= 20:
            d1 = 20
        elif inflow >= 10:
            d1 = 16
        elif inflow >= 5:
            d1 = 12
        else:
            d1 = 8
        detail['板块资金'] = f"{d1}/20 (回退关羽当天{inflow:.0f}亿·非次日方向)"
    s += d1

    # ② 启动信号 30（未启动程度 + 量能蓄势）
    d2 = 0
    if -2 <= chg <= 2:
        d2 += 12  # 完全没启动（平盘）
    elif chg < 0:
        d2 += 10  # 还在跌（更没启动）
    elif chg <= 4:
        d2 += 6
    else:
        d2 += 3
    if 0.8 <= vr <= 2.5:
        d2 += 12  # 温和放量（蓄势）
    elif vr < 0.8:
        d2 += 8  # 缩量（底部）
    elif vr <= 4:
        d2 += 5
    else:
        d2 += 0
    if 0.5e8 <= amount <= 15e8:
        d2 += 6
    else:
        d2 += 2
    detail['启动信号'] = f"{d2}/30"
    s += d2

    # ③ 游资偏好 25（小市值+低位）
    if mcap < 30:
        d3 = 25
    elif mcap < 50:
        d3 = 20
    elif mcap < 80:
        d3 = 14
    else:
        d3 = 8
    detail['游资偏好'] = f"{d3}/25"
    s += d3

    # ④ 蓄势形态 15（振幅小=蓄势；今天微跌/平盘=启动前夜）
    # V2.2（2026-08-14）：尾盘跳水不再一刀切加分/减分——低位缩量跳水=洗盘（不罚），高位跳水=风险
    # 蓝箭案例：8/13尾盘跳水-1.98%被判风险（实际分位79%高位，但次日+15%——跳水≠出货，需结合分位）
    if amp <= 3:
        d4 = 12
    elif amp <= 5:
        d4 = 8
    else:
        d4 = 4
    if chg < 0:
        # 微跌：分位<60%视为洗盘（蓄势加分），分位≥60%视为高位风险（不加分）
        if pos20 is not None and pos20 < 60:
            d4 += 3
            detail['蓄势形态'] = f"{d4}/15 (跌·低位{pos20:.0f}%=洗盘)"
        elif pos20 is not None:
            detail['蓄势形态'] = f"{d4}/15 (跌·高位{pos20:.0f}%=风险不加)"
        else:
            d4 += 3
            detail['蓄势形态'] = f"{d4}/15 (跌·分位未知)"
    else:
        detail['蓄势形态'] = f"{d4}/15"
    s += d4

    # ⑤ 风险 10
    d5 = 10
    if amount < 0.3e8:
        d5 -= 4
    if amp > 8:
        d5 -= 2
    if vr > 4:
        d5 -= 2
    detail['风险'] = f"{d5}/10"
    s += d5

    # 🆕 2026-08-12 妖股基因维度（由8/12六妖股解剖固化：低价+缩量沉淀=游资启动前夜）
    #   六妖股启动价：传智5元/北京文化3.5元/百花7元/蓝盾16元/云赛18元 → 低价是共性
    #   启动前全部缩量（量比<1）沉淀 → 缩量=筹码锁定
    d7 = 0
    price = stock.get('price', 0) or 0
    if 0 < price <= 8:
        d7 += 8
        detail['妖股基因'] = f"低价{price:.1f}元(+8)"
    elif 8 < price <= 15:
        d7 += 6
        detail['妖股基因'] = f"低价{price:.1f}元(+6)"
    elif 15 < price <= 25:
        d7 += 4
        detail['妖股基因'] = f"中价{price:.1f}元(+4)"
    else:
        detail['妖股基因'] = f"高价{price:.1f}元(0)"
    if vr < 0.8:
        d7 += 6
        detail['妖股基因'] += "·缩量沉淀(+6)"
    elif vr < 1.2:
        d7 += 4
        detail['妖股基因'] += "·量能温和(+4)"
    else:
        detail['妖股基因'] += f"·量比{vr:.1f}(0)"
    s += d7

    # 🆕 2026-08-10 埋伏标准②：20日分位<40% = 低位埋伏加分（+5，位置维度）
    d6 = 0
    if pos20 is not None:
        if pos20 < 40:
            d6 = 5
            detail['低位埋伏'] = f"{d6}/5 (分位{pos20:.0f}%)"
        elif pos20 < 60:
            d6 = 2
            detail['低位埋伏'] = f"{d6}/5 (分位{pos20:.0f}%)"
        else:
            detail['低位埋伏'] = f"0/5 (分位{pos20:.0f}%·高位)"
    s += d6

    return s, detail


def get_limit_up_pool():
    """今日涨停股全量池（akshare涨停池，独立源）——2026-08-03用户确认：候选池改涨停全量入池
    返回 [{'code','name','sector','pct','float_cap','lianban','seal'}]，失败返回 []
    """
    try:
        import akshare as ak
        zt = ak.stock_zt_pool_em(date=dt.datetime.now().strftime("%Y%m%d"))
        if zt is None or len(zt) == 0:
            return []
        pool = []
        for _, r in zt.iterrows():
            code = str(r.get('代码', '')).zfill(6)
            if not code or code == '000000':
                continue
            # 🆕 2026-08-12 用户铁律：买不了科创板 → 688开头一律排除
            if code.startswith('688'):
                continue
            try:
                fc = float(r.get('流通市值', 0) or 0) / 1e8  # 元→亿
            except:
                fc = 0
            pool.append({
                "code": code,
                "name": str(r.get('名称', code)),
                "sector": str(r.get('所属行业', '未知')),
                "pct": float(r.get('涨跌幅', 0) or 0),
                "float_cap": fc,
                "lianban": int(r.get('连板数', 1) or 1),
                "seal": float(r.get('封板资金', 0) or 0),
            })
        return pool
    except Exception as e:
        print(f"   (涨停池获取失败: {e})")
        return []


def get_cycle_data():
    """采集情绪周期所需全量数据：炸板率、昨日涨停表现、最高连板"""
    import akshare as ak, json, os
    
    result = {
        'limit_up': 0, 'limit_down': 0, '炸板率': None,
        '昨日涨停均涨幅': None, '最高连板': None, '最高连板股': None,
        'hs300_chg': None, 'zz1000_chg': None, 'hs300_ma20': None,
    }
    today = dt.datetime.now().strftime("%Y%m%d")
    
    # 涨停/跌停
    try:
        zt = ak.stock_zt_pool_em(date=today)
        result['limit_up'] = len(zt)
    except:
        pass
    try:
        _dtgc = ak.stock_zt_pool_dtgc_em(date=today)
        result['limit_down'] = len(_dtgc)
    except:
        pass
    
    # 炸板率 = 炸板数 / (涨停数+炸板数)
    zb_list = None
    try:
        zb = ak.stock_zt_pool_zbgc_em(date=today)
        zb_list = len(zb)
        total_zt = result['limit_up'] + zb_list
        result['炸板率'] = round(zb_list / total_zt * 100, 1) if total_zt > 0 else None
    except:
        pass
    
    # 最高连板高度
    try:
        strong = ak.stock_zt_pool_strong_em(date=today)
        if len(strong) > 0:
            # 涨停统计格式如 "4/4" = 连板天/连续涨停天
            max_boards = 0; max_name = ''
            for _, r in strong.iterrows():
                stat = str(r.get('涨停统计','0/0'))
                try:
                    boards = int(stat.split('/')[1])
                    if boards > max_boards:
                        max_boards = boards
                        max_name = r.get('名称','')
                except:
                    pass
            result['最高连板'] = max_boards
            result['最高连板股'] = max_name
    except:
        pass
    
    # 昨日涨停今日平均涨幅
    try:
        prev = ak.stock_zt_pool_previous_em(date=today)
        if len(prev) > 0 and '涨跌幅' in prev.columns:
            result['昨日涨停均涨幅'] = round(prev['涨跌幅'].mean(), 2)
    except:
        pass
    
    # 沪深300 / 中证1000 指数涨跌幅 — 腾讯API
    try:
        r = requests.get('http://qt.gtimg.cn/q=sh000300,sh000852',
                         headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        r.encoding = 'gbk'
        for line in r.text.strip().split(';'):
            if not line.strip() or '~' not in line: continue
            f = line.split('~')
            if len(f) < 35: continue
            code = f[0].split('_')[-1].split('=')[0]
            px = float(f[3]) if f[3] else 0
            prev = float(f[4]) if f[4] else 0
            chg = round((px - prev) / prev * 100, 2) if prev else None
            name = f[1]
            if '000300' in code:
                result['hs300_chg'] = chg
            elif '000852' in code:
                result['zz1000_chg'] = chg
    except Exception as e:
        pass

    # 2026-08-05修复：hs300_ma20 定义后从未赋值（fetch_index_ma20未被调用）
    try:
        result['hs300_ma20'] = fetch_index_ma20('sh000300')
    except Exception:
        result['hs300_ma20'] = None
    
    return result


def fetch_index_ma20(index_code):
    """拉取指数K线判断是否站上MA20（简化：用最近20日收盘均价估算）"""
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol=index_code)
        if len(df) >= 20:
            ma20 = df['close'].tail(20).mean()
            latest = df['close'].iloc[-1]
            return latest >= ma20
    except:
        pass
    return None


def judge_emotion_phase(cycle_data, prev_phase="未知"):
    """养家心法情绪时钟·12阶段识别（2026-08-08固化）

    多方循环(贪婪): 🌱酝酿→⚡扩散→🚀高潮→🔥疯狂→😰期待→📉消亡
    空方循环(恐惧): 💭幻想→😐犹豫→🛡️抵抗→💥崩溃→🪦麻木→🕊️解脱

    核心：赚钱效应是市场最直接的信号。
      赚钱效应(短线选手阶段内赚钱→自信→投入下一品种→热点有持续性)
      亏钱效应(追涨接二连三失手→资金缩水→减少操作→强势股补跌)

    量化信号：涨停数/跌停数/炸板率/昨日涨停均涨幅/最高连板/指数
    返回 (phase_name, phase_val, reason)；缺数据返回 (None, 0, "BLIND...")
    """
    limit_up   = cycle_data.get('limit_up', 0) or 0
    limit_down = cycle_data.get('limit_down', 0) or 0
    zb_rate    = cycle_data.get('炸板率')
    prev_avg   = cycle_data.get('昨日涨停均涨幅')
    max_board  = cycle_data.get('最高连板') or 0
    hs300_chg  = cycle_data.get('hs300_chg')

    missing = []
    if zb_rate is None: missing.append('炸板率')
    if prev_avg is None: missing.append('昨涨停均涨幅')
    if limit_up == 0 and limit_down == 0: missing.append('涨跌停数')
    if missing:
        return None, 0.0, f"BLIND：缺{'/'.join(missing)}"

    # ── 空方优先：恐慌是最危险的信号，即使涨停多也要先判崩溃 ──
    # 💥 崩溃期：连续大跌恐慌抛售（跌停>15，或涨停枯竭+跌停增多）
    if limit_down > 15 or (limit_up < 15 and limit_down > 5):
        return "💥 崩溃期", 0.15, f"涨停{limit_up}/跌停{limit_down} → 恐慌抛售，割肉离场"

    # ── 多方循环（贪婪）──
    # 🔥 疯狂期：全民参与、情绪亢奋，龙头成精神领袖（昨涨停均涨>5%+超高连板）
    if limit_up > 100 and (prev_avg or 0) > 5 and max_board >= 7:
        return "🔥 疯狂期", 0.9, f"涨停{limit_up}/昨涨{prev_avg}%/连板{max_board}板 → 全民亢奋，龙头精神领袖"
    # 🚀 高潮期：板块轮动、热点扩散，增量资金持续入场（涨停高位+封板质量好）
    if limit_up >= 70 and zb_rate <= 30:
        return "🚀 高潮期", 0.8, f"涨停{limit_up}/炸板{zb_rate}% → 增量资金入场，热点扩散"
    # 😰 期待期：多数人仍期待再涨一点，此时风险已高（涨停高位但炸板率升高=预期透支）
    if limit_up >= 60 and zb_rate > 30:
        return "😰 期待期", 0.5, f"涨停{limit_up}/炸板{zb_rate}%升高 → 预期透支，风险累积"
    # ⚡ 扩散期：赚钱效应扩散，怕踏空>落袋为安，上涨加速
    if limit_up >= 50 and zb_rate <= 25 and max_board >= 4 and (prev_avg or 0) > 2:
        return "⚡ 扩散期", 0.75, f"涨停{limit_up}/炸板{zb_rate}%/连板{max_board}板/昨涨{prev_avg}% → 赚钱效应扩散"
    # 🌱 酝酿期：少数人开始赚钱，赚钱效应初显
    if limit_up >= 30 and zb_rate <= 30 and max_board >= 2:
        return "🌱 酝酿期", 0.6, f"涨停{limit_up}/炸板{zb_rate}%/连板{max_board}板 → 赚钱效应初显"

    # ── 空方循环（恐惧）──
    # 🛡️ 抵抗期：小幅反弹以为企稳，实则是诱多（LEO-012：弱反弹不可信）
    # 信号收紧：昨涨停均涨明显为负(<-1.5%)才算亏钱效应下的诱多反弹；
    # 轻微回落(>-1.5%)且跌停少=下跌初期幻想期，不误判
    if 20 <= limit_up < 45 and (prev_avg or 0) < -1.5 and max_board <= 3:
        return "🛡️ 抵抗期", 0.35, f"涨停{limit_up}/昨涨{prev_avg}%/连板{max_board}板 → 弱反弹=诱多(LEO-012)"
    # 😐 犹豫期：怀疑、纠结，不知道该卖还是等（涨停不少但炸板率飙高）
    if 30 <= limit_up < 60 and zb_rate > 40:
        return "😐 犹豫期", 0.3, f"涨停{limit_up}/炸板{zb_rate}% → 怀疑纠结"
    # 🕊️ 解脱期：多数人割肉、麻木到极致，市场见底（涨停回升+连板梯队恢复+昨涨转正）
    if 15 <= limit_up < 30 and max_board >= 3 and (prev_avg or 0) > 0:
        return "🕊️ 解脱期", 0.45, f"涨停{limit_up}/连板{max_board}板/昨涨{prev_avg}% → 见底修复"
    # 💭 幻想期：下跌初期，仍抱有反弹幻想（涨停回落但跌停少，无连板梯队）
    if 15 <= limit_up < 30 and limit_down <= 5:
        return "💭 幻想期", 0.4, f"涨停{limit_up}/跌停{limit_down} → 下跌初期，反弹幻想"
    # 🪦 麻木期：深度套牢，不再看账户，等待解套（涨停枯竭+跌停也少=地量特征）
    if limit_up < 15:
        return "🪦 麻木期", 0.2, f"涨停{limit_up}/跌停{limit_down} → 深度套牢，地量麻木"

    return None, 0.0, f"无法判定(涨停{limit_up}/炸板{zb_rate}%/连板{max_board})"


PHASE_STRATEGY = {
    "🌱 酝酿期": "轻仓试错（B级10-15%）：跟随赚钱效应初显的板块龙头，盈利即止",
    "⚡ 扩散期": "强势阶段→重仓主流龙头（S级50-60%）：不恐高不恐快，跟随赚钱效应（8月计划主战场）",
    "🚀 高潮期": "只卖不买：板块轮动高潮=兑现窗口，持仓按止盈出，禁止新开仓",
    "🔥 疯狂期": "清仓离场：全民亢奋+龙头加速=出货窗口（热搜三重卖出信号），不恋战",
    "😰 期待期": "减仓：多数人期待再涨时风险已高，落袋为安，禁止追高",
    "📉 消亡期": "空仓休息：情绪退潮资金撤离，等待下一轮酝酿",
    "💭 幻想期": "空仓观察：下跌初期不接刀，等待企稳信号",
    "😐 犹豫期": "轻仓或空仓：纠结期不做决策，等方向明确",
    "🛡️ 抵抗期": "禁开仓：弱反弹=诱多（LEO-012），反弹缩量不追，空仓等崩溃后机会",
    "💥 崩溃期": "空仓保命：恐慌抛售不抄底，等麻木期出现再评估",
    "🪦 麻木期": "空仓等反转：深度套牢地量=底部区域特征，开始扫描反转信号（地量+涨停回升）",
    "🕊️ 解脱期": "试探建仓（B级）：见底修复信号出现，轻仓跟随首波反弹",
}

PHASE_CYCLE = {
    "🌱 酝酿期": "多方", "⚡ 扩散期": "多方", "🚀 高潮期": "多方",
    "🔥 疯狂期": "多方", "😰 期待期": "多方", "📉 消亡期": "多方",
    "💭 幻想期": "空方", "😐 犹豫期": "空方", "🛡️ 抵抗期": "空方",
    "💥 崩溃期": "空方", "🪦 麻木期": "空方", "🕊️ 解脱期": "空方",
}


def judge_cycle(cycle_data, prev_cycle="BLIND", prev_limit_up=None):
    """状态转移周期判定
    prev_cycle: 前一日周期 (从cycle_history.json读取)
    """
    limit_up = cycle_data['limit_up']
    limit_down = cycle_data['limit_down']
    zb_rate = cycle_data['炸板率']
    prev_avg = cycle_data['昨日涨停均涨幅']
    max_board = cycle_data['最高连板']
    hs300_chg = cycle_data.get('hs300_chg')
    zz1000_chg = cycle_data.get('zz1000_chg')
    
    # 缺任一数据 → BLIND（不猜）
    missing = []
    if zb_rate is None: missing.append('炸板率')
    if prev_avg is None: missing.append('昨日涨停均涨幅')
    if limit_up == 0: missing.append('涨停数')
    
    if missing:
        return None, 0.0, f"BLIND：缺{'/'.join(missing)}"
    
    # ── 炸板率新阈值 ──
    zb_strong   = zb_rate < 25        # 强势：封板率高
    zb_normal   = 25 <= zb_rate <= 40 # 正常区间
    zb_failure  = zb_rate > 40        # 衰竭信号
    zb_retreat  = zb_rate > 55        # 退潮
    
    # ── 指数判据 ──
    index_valid = hs300_chg is not None
    index_bad   = index_valid and hs300_chg < -1.0
    index_good  = index_valid and hs300_chg > 0
    
    # ── 指数+涨停交叉判定 ──
    if limit_up > 40 and index_bad:
        # 涨停多但指数差 → 分化
        pass  # 不直接return，让状态机判断是否转入分化
    
    # ── 强制退出：高潮→涨停回落>40%→退潮 ──
    if prev_cycle == "🚀 高潮" and prev_limit_up is not None and prev_limit_up > 0:
        drop_ratio = (prev_limit_up - limit_up) / prev_limit_up
        if drop_ratio > 0.4:
            return "📉 退潮", 0.15, f"强制退潮：涨停从{prev_limit_up}降至{limit_up}(-{drop_ratio*100:.0f}%)"
    
    # ── 炸板率退潮红线 ──
    if zb_retreat:
        return "📉 退潮", 0.1, f"炸板率{zb_rate}%>55% → 退潮"
    
    # ── 截面判定（无历史时） ──
    if prev_cycle == "BLIND":
        is_ice = (limit_down > 10) or (limit_up < 30 and limit_down > 5)
        if is_ice:
            return "💀 恐慌/冰点", 0.2, f"涨停{limit_up}/跌停{limit_down} 炸板率{zb_rate}%"
        if limit_up > 40 and index_bad:
            return "🟠 分化", 0.5, f"涨停{limit_up}但沪深300{hs300_chg}%< -1% → 分化"
        if limit_up > 40 and index_good:
            return "🟢 回暖", 0.65, f"涨停{limit_up}+沪深300{hs300_chg}% → 回暖"
        if zb_strong and limit_up > 30:
            return "🟢 回暖", 0.55, f"涨停{limit_up} 炸板率{zb_rate}%<25% → 回暖"
        return "🟡 分歧", 0.4, f"涨停{limit_up}/跌停{limit_down} 炸板率{zb_rate}%"
    
    # ── 状态转移（有历史） ──
    
    # 从恐慌/冰点/退潮起步
    if prev_cycle in ("💀 恐慌/冰点", "📉 退潮"):
        if limit_up > 50 and zb_strong:
            return "🟢 回暖", 0.65, f"从{prev_cycle}→涨停{limit_up} 炸板{zb_rate}% 回暖"
        elif limit_up > 30:
            return "🔵 修复期", 0.5, f"从{prev_cycle}→修复 涨停{limit_up}"
        else:
            return "🔵 修复期", 0.4, f"从{prev_cycle}缓慢修复"
    
    # 修复期
    elif prev_cycle == "🔵 修复期":
        if limit_up > 40 and index_bad:
            return "🟠 分化", 0.5, f"修复→分化 涨停{limit_up}但指数-{abs(hs300_chg):.1f}%"
        elif limit_up > 50 and zb_strong:
            return "🟢 回暖", 0.65, f"修复→回暖 涨停{limit_up} 炸板{zb_rate}%"
        elif limit_up > 40:
            return "🟡 分歧", 0.55, f"修复→分歧 涨停{limit_up}"
        else:
            return "🔵 修复期", 0.45, "修复未完成"
    
    # 分歧
    elif prev_cycle == "🟡 分歧":
        # 修复：涨停仍在扩张时，炸板率高≠退潮（普涨分歧日）
        if limit_up > 60 and limit_up >= (prev_limit_up or 0) and not index_bad:
            return "🟡 分歧", 0.55, f"分歧延续（偏强）涨停{limit_up}扩张 炸板{zb_rate}%"
        # 修复：涨停高位(>70)即使微降/炸板率高，只要跌停少仍是分歧不是退潮
        if limit_up > 70 and limit_down <= 5 and not index_bad:
            return "🟡 分歧", 0.5, f"分歧延续 涨停{limit_up}高位 炸板{zb_rate}% 跌停仅{limit_down}"
        if limit_up > 50 and zb_strong and not index_bad:
            return "🟢 回暖", 0.65, f"分歧→回暖 涨停{limit_up} 炸板{zb_rate}%"
        # 🆕 2026-08-04修复：早盘涨停数少但结构强势 → 回暖
        #    根因：原阈值涨停>50为全天口径，早盘30+涨停+炸板<25%+零跌停+连板梯队+指数正
        #    被误判"分歧持续"（系统连续3日告警）
        elif limit_up >= 30 and zb_strong and limit_down <= 2 and max_board >= 4 and index_good:
            return "🟢 回暖", 0.6, f"分歧→回暖 涨停{limit_up} 炸板{zb_rate}% 跌停{limit_down} 连板{max_board}板 沪深300{hs300_chg}%"
        elif limit_up > 40 and index_bad:
            return "🟠 分化", 0.5, f"分歧→分化 涨停{limit_up}但指数{hs300_chg}%"
        elif zb_failure:
            return "📉 退潮", 0.25, f"分歧→退潮 炸板率{zb_rate}%>40%"
        else:
            return "🟡 分歧", 0.45, "分歧持续"
    
    # 回暖
    elif prev_cycle in ("🟢 回暖", "🟢 加速"):
        if limit_up > 40 and index_bad:
            return "🟠 分化", 0.5, f"回暖→分化 涨停{limit_up}但指数{hs300_chg}%"
        elif zb_failure:
            return "📉 退潮", 0.2, f"回暖→退潮 炸板率{zb_rate}%>40%"
        elif zb_strong and limit_up > 50:
            return "🟢 回暖", 0.7, f"回暖延续 涨停{limit_up} 炸板{zb_rate}%"
        elif zb_normal:
            return "🟡 分歧", 0.55, f"回暖→分歧 炸板率{zb_rate}%进入正常区间"
        else:
            return "🟢 回暖", 0.55, "回暖延续（偏弱）"
    
    # 分化
    elif prev_cycle == "🟠 分化":
        if index_good and limit_up > 50:
            return "🟢 回暖", 0.6, f"分化→回暖 指数转正+涨停{limit_up}"
        elif zb_failure:
            return "📉 退潮", 0.2, f"分化→退潮 炸板率{zb_rate}%>40%"
        elif limit_up < 20:
            return "📉 退潮", 0.2, f"分化→退潮 涨停降至{limit_up}"
        elif limit_up < 40 and not index_bad:
            return "🟡 分歧", 0.45, f"分化→分歧 涨停回落"
        else:
            return "🟠 分化", 0.45, "分化持续"
    
    # 高潮 — 强制退出条件已在顶部检查drop>40%
    elif prev_cycle == "🚀 高潮":
        if zb_failure:
            return "📉 退潮", 0.25, f"高潮→退潮 炸板率{zb_rate}%>40%"
        elif limit_up < 20:
            return "📉 退潮", 0.2, f"高潮→退潮 涨停跌至{limit_up}"
        else:
            return "🚀 高潮", 0.65, f"高潮延续 涨停{limit_up} 炸板{zb_rate}%"
            # 高潮延续不主动搞退潮，强制退出靠drop>40%检测
    
    return None, 0.0, "BLIND：未知状态转换"


# ============================================================
# 五维评分（独立计算）
# ============================================================

def score_wuwei_v3(sector_rank, stock, sentiment, etf_list, sector_band=None):
    """
    V3五维评分 + 透支扣分
    ①板块分改为相对排名 | ②地位分改为梯队时间 | ⑥新增透支扣分
    """
    s = 0
    detail = {}
    vr = stock.get('vol_ratio', 0)
    amount = stock.get('amount', 0)
    pct = stock.get('pct', 0)
    
    # ① 板块分 30分（相对排名）— 2026-08-02修复：rank=None(板块未知)不给分，杜绝虚高分
    if sector_rank == 1:
        sector_score = 28
    elif sector_rank and sector_rank <= 3:
        sector_score = 22
    elif sector_rank and sector_rank <= 6:
        sector_score = 12
    else:
        sector_score = 0
    detail['板块分'] = f"{sector_score}/30"
    s += sector_score
    
    # ② 地位分 25分（梯队位置，非涨幅）
    # 2026-07-31用户确认：非涨停票地位分上调，让次龙头能达标
    if sector_rank == 1 and pct > 5 and vr >= 1.5:
        status_score = 22  # 板块第1+放量+涨幅领先=假定龙头
    elif sector_rank and sector_rank <= 3 and pct > 3:
        status_score = 18  # 板块前排+跟随（原15→18）
    elif sector_rank is None:
        status_score = 8   # 2026-08-02修复：板块未知不给板块加成，仅保底
    elif pct > 0:
        status_score = 15  # 板块内正涨幅（原8→15）
    else:
        status_score = 8
    detail['地位分'] = f"{status_score}/25"
    s += status_score
    
    # ③ 量能分 20分
    if 1.5 <= vr <= 3.0:
        energy_score = 18
    elif 3.0 < vr <= 5.0:
        energy_score = 12
    elif vr > 5.0:
        energy_score = 8  # 单日爆量，警惕
    elif 1.0 <= vr < 1.5:
        energy_score = 8
    else:
        energy_score = 0  # 缩量
    detail['量能分'] = f"{energy_score}/20"
    s += energy_score
    
    # ④ 形态分 15分
    if stock.get('open') and stock.get('prev'):
        open_px = stock['open']
        prev_px = stock['prev']
        close_px = stock['price']
        if open_px < prev_px and close_px > prev_px:
            form_score = 13  # 低开高走
        elif open_px < prev_px and close_px > open_px:
            form_score = 10  # 低开回升
        elif close_px >= open_px:
            form_score = 8   # 平开高走
        elif close_px >= prev_px * 0.98:
            form_score = 4   # 平开微跌
        else:
            form_score = 2   # 高开低走
    else:
        form_score = 0
    detail['形态分'] = f"{form_score}/15"
    s += form_score
    
    # ⑤ 风险分 10分
    risk = 10
    if stock.get('high') and stock.get('low') and stock.get('prev'):
        amp = (stock['high'] - stock['low']) / stock['prev'] * 100
        if amp > 12: risk -= 3
        if amount and amount > 50e8: risk -= 2
        if vr and vr > 5: risk -= 2
    if amount and amount < 5e7: risk -= 2  # 流动性不足
    detail['风险分'] = f"{risk}/10"
    s += risk
    
    # ⑥ 透支扣分 −30分（反向维度）
    overdraft = 0
    consecutive_days = stock.get('consecutive_up', 0)
    cum_5d = stock.get('cum_5d_pct', 0)
    if consecutive_days >= 4:
        overdraft += 8
    if cum_5d > 30:
        overdraft += 15
    elif cum_5d > 20:
        overdraft += 10
    if stock.get('is_top_leader', False):
        overdraft += 8
    if stock.get('near_high', False):
        overdraft += 7
    
    final = s - overdraft
    # 🆕 2026-08-12 连板因子（修复妖股被系统性压分）：
    #   背景：传智教育(9板)/百花医药(7板)等妖股因板块冷门(板块分0)+一字板无量(量能分0)→评分仅18-26分<65门槛
    #   妖股核心信号=连板高度，凌驾板块热度/量能（一字板本身无量是正常特征）
    lianban = stock.get('lianban', 0) or 0
    if lianban >= 7:
        final += 30
        detail['连板因子'] = f"{lianban}板妖股(+30)"
    elif lianban >= 4:
        final += 20
        detail['连板因子'] = f"{lianban}板(+20)"
    elif lianban >= 2:
        final += 10
        detail['连板因子'] = f"{lianban}板(+10)"
    detail['最终分'] = final
    return final, detail


# ============================================================
# 热点板块识别（独立）
# ============================================================

def find_hot_sectors(etf_data, top_n=3):
    """找涨幅TOP板块（独立）"""
    sorted_s = sorted(etf_data.items(), key=lambda x: -x[1])
    return sorted_s[:top_n]


# ============================================================
# 主函数
# ============================================================

def sunquan_scan(extra_codes=None):
    now = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    print("=" * 65)
    print(f"  🐉 孙权 V2.0 · 超短线龙头评估 | {now}")
    print("  📡 独立数据系统（不依赖其他模型）")
    print("=" * 65)
    
    # 1. 拉独立数据
    print("\n📡 数据采集...")
    etf_data = get_etf_prices()
    cycle_data = get_cycle_data()
    gainers = get_top_gainers(80)  # 2026-08-03执行性修复：拉80条，确保5-9.9%准涨停不被涨停截断
    
    hs300_str = f"{cycle_data['hs300_chg']:+.2f}%" if cycle_data['hs300_chg'] is not None else 'N/A'
    zz1000_str = f"{cycle_data['zz1000_chg']:+.2f}%" if cycle_data['zz1000_chg'] is not None else 'N/A'
    print(f"   ETF: {len(etf_data)}个 | 涨停: {cycle_data['limit_up']} | 跌停: {cycle_data['limit_down']}")
    print(f"   炸板率: {cycle_data['炸板率']}% | 最高连板: {cycle_data['最高连板']}板({cycle_data['最高连板股']}) | 昨涨停均涨: {cycle_data['昨日涨停均涨幅']}")
    print(f"   沪深300: {hs300_str} | 中证1000: {zz1000_str}")
    
    # 2. 读历史周期 → 状态转移判定
    history = {"cycle": "BLIND", "date": "", "limit_up": 0, "history": [], "phase": "未知"}
    if os.path.exists("cycle_history.json"):
        with open("cycle_history.json") as f:
            history = json.load(f)
    
    prev_cycle = history.get("cycle", "BLIND")
    prev_limit_up = history.get("limit_up", 0)
    prev_date = history.get("date", "")
    prev_phase = history.get("phase", "未知")  # 🆕 2026-08-08 养家心法情绪时钟：前一日12阶段
    state_history = history.get("history", [])
    # 2026-08-02修复：兼容旧格式(纯字符串列表，无日期，同日多次运行重复append→假连续告警)
    # 旧格式无法还原日期 → 仅保留最后一条作为最近状态，之后按新格式(带date)按日去重
    if state_history and isinstance(state_history[0], str):
        state_history = [{"date": "legacy", "cycle": state_history[-1]}]
    
    cycle_name, cycle_val, cycle_reason = judge_cycle(cycle_data, prev_cycle, prev_limit_up)
    
    # 🆕 2026-08-08 养家心法情绪时钟：12阶段识别（叠加层，不改变现有执行逻辑）
    phase_name, phase_val, phase_reason = judge_emotion_phase(cycle_data, prev_phase)
    if phase_name is not None:
        phase_strategy = PHASE_STRATEGY.get(phase_name, '')
        phase_dir = PHASE_CYCLE.get(phase_name, '')
        print(f"\n🕰️ 情绪时钟（养家心法12阶段）: {phase_name} (val={phase_val})")
        print(f"   依据: {phase_reason}")
        print(f"   循环: {phase_dir}循环 | 前一日: {prev_phase}")
        if phase_strategy:
            print(f"   策略: {phase_strategy}")
        if prev_phase in PHASE_CYCLE and PHASE_CYCLE[prev_phase] == '多方' and phase_dir == '空方':
            print(f"   ⚠️ 多方→空方切换！情绪逆转，按空方策略执行（保命优先）")
        elif prev_phase in PHASE_CYCLE and PHASE_CYCLE[prev_phase] == '空方' and phase_dir == '多方':
            print(f"   ✅ 空方→多方切换！赚钱效应回归，可逐步增加参与度")
    else:
        print(f"\n🕰️ 情绪时钟: ❌ BLIND — {phase_reason}")

    # 🆕 2026-08-08 情绪闸门：养家心法禁止重仓阶段（叠加层，不改变状态机开关，只降级执行建议）
    BLOCK_PHASES = {"🚀 高潮期", "🔥 疯狂期", "😰 期待期", "📉 消亡期",
                    "💭 幻想期", "🛡️ 抵抗期", "💥 崩溃期", "🪦 麻木期"}
    phase_block = phase_name in BLOCK_PHASES
    if phase_block:
        print(f"   🚧 情绪闸门: {phase_name} → 禁止重仓/新开仓从紧，以下候选仅作参考")
    else:
        print(f"   🚧 情绪闸门: {'开放' if phase_name else 'BLIND'} → 按正常分级参与")
    
    if cycle_name is None:
        print(f"\n📊 情绪周期: ❌ BLIND — {cycle_reason}")
        os.makedirs(os.path.dirname(OUT_DIR) if os.path.dirname(OUT_DIR) else '.', exist_ok=True)
    else:
        print(f"\n📊 情绪周期: {cycle_name} (val={cycle_val})")
        print(f"   依据: {cycle_reason}")
        print(f"   前一日周期: {prev_cycle} (前日涨停{prev_limit_up})")
        
        # 3日连续告警（2026-08-02修复：按交易日去重+非交易日不记录，杜绝同日多次运行/周末运行假连续）
        today_state = cycle_name.strip()
        now_dt = dt.datetime.now()
        today_str = now_dt.strftime("%Y-%m-%d")
        is_weekend = now_dt.weekday() >= 5
        if (not is_weekend) and today_str != history.get("date", ""):
            state_history.append({"date": today_str, "cycle": today_state})
        if len(state_history) > 5:
            state_history = state_history[-5:]
        consecutive_count = 0
        for _h in reversed(state_history):
            if _h["cycle"] == today_state:
                consecutive_count += 1
            else:
                break
        if consecutive_count >= 3:
            print(f"   ⚠️ 【告警】{today_state}已连续{consecutive_count}日，请检查转移条件是否失效")
        
        # 保存
        with open("cycle_history.json", "w") as f:
            json.dump({"cycle": cycle_name, "date": today_str,
                      "limit_up": cycle_data['limit_up'], "limit_down": cycle_data['limit_down'],
                      "zb_rate": cycle_data['炸板率'], "max_board": cycle_data['最高连板'],
                      "hs300_chg": cycle_data['hs300_chg'],
                      "phase": phase_name if phase_name else "未知",  # 🆕 2026-08-08 情绪时钟阶段
                      "phase_reason": phase_reason if phase_name else "",
                      "history": state_history}, f)
    
    # 3. 热点板块
    hot = find_hot_sectors(etf_data, 3)
    print(f"\n🔥 热点板块（独立判定）:")
    for name, chg in hot:
        bar = '🚀' if chg > 3 else ('🟢' if chg > 1 else '🟡')
        print(f"   {bar} {name}: {chg:+.1f}%")
    
    # 4. 候选扫描
    print(f"\n📋 候选评估（涨幅TOP{len(gainers)}中筛选）:")
    threshold = None  # 2026-08-03：防恐慌/高潮分支未定义（候选落盘用）
    if cycle_name is None:
        print("   周期BLIND → 候选评估跳过")
    elif cycle_val <= 0.3 or cycle_name.startswith("💀") or cycle_name.startswith("📉"):
        print("   恐慌/退潮期 → 不出手")
    elif cycle_name.startswith("🚀"):
        print("   高潮期 → 只卖不买，候选评估跳过")
    elif cycle_name.startswith("🟠"):
        print("   分化期 → 谨慎参与（局部热点，指数承压）")
    else:
        # 修复/分歧/回暖/加速 → 可参与，按周期调整阈值（2026-07-31用户确认降阈）
        if cycle_name.startswith("🔵"):  # 修复期→低阈值
            threshold = 60
        elif cycle_name.startswith("🟡"):  # 分歧→中阈值（用户确认70）
            threshold = 70
        elif cycle_name.startswith("🟢"):  # 回暖/加速→低阈值（2026-08-04用户确认：回暖=最好参与，从72降至65）
            threshold = 65
        elif cycle_name.startswith("🟠"):  # 分化→高阈值
            threshold = 78
        else:
            threshold = 75
        
        stock_quotes = {}
        # 2026-08-03用户亲授：孙权=潜伏票（找今天没启动、明天可能被游资拉的票），不是追涨停
        # 主源：关羽埋伏板块内未启动股；回退：涨停池→准涨停→热点成分股
        gainer_codes = []
        code2sector = {}
        hot_rank = {n: i+1 for i, (n, _c) in enumerate(hot)}  # 热点板块排名1/2/3
        qianfu_pool, fund_sectors = get_qianfu_pool()
        if qianfu_pool:
            for _q in qianfu_pool:
                if _q['sym']:
                    gainer_codes.append(_q['sym'])
                    code2sector[_q['sym']] = _q['sector']
            gainer_codes = list(dict.fromkeys(gainer_codes))
            print(f"   (候选池: 关羽埋伏板块潜伏票 {len(qianfu_pool)}只 / 资金方向板块{len(fund_sectors)}个)")
        else:
            # 🆕 2026-08-07 用户铁律（LEO-024）：潜伏池空=空仓，禁止回退涨停/准涨停/热点成分股
            # 原因：回退=涨停后才给分=马后炮=推荐买不进的票（锴威特一字板64分案例）
            # 原则：选出来的必须能买，买不进的推荐=零意义
            print("   (候选池: 关羽埋伏板块潜伏票为空 → 今日空仓，不回退涨停池)")
            _empty_quotes = get_stock_quotes([])
            _empty_scored = []
            _empty_big = []
            _empty_hot = []
            _empty_status = {}
            # 走统一输出，但候选为空
            for g in gainers[:15]:
                g['pct'] = g['pct'] / 100 if abs(g.get('pct',0)) > 10 else g.get('pct', 0)
            scored = []
            big_caps = []
            zt_counter = {}
            qf_map = {}
            best = None
            best_score = 0
            print("\n📋 候选评估（潜伏池为空）:")
            print("   ───────────────────────────────────────")
            print("   🚫 今日无潜伏候选（关羽资金方向板块内无未启动小盘股）")
            print("   ✅ 按用户铁律：潜伏池空=空仓，禁止用涨停池凑数")
            print()
            # 保存状态文件
            try:
                _out = {
                    'time': dt.datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'cycle': cycle_name, 'cycle_val': cycle_val, 'cycle_data': cycle_data,
                    'phase': phase_name if phase_name else '未知',
                    'hot_sectors': [{'name': n, 'chg': c} for n, c in hot[:5]],
                    'threshold': threshold,
                    'candidates': [], 'best': None,
                    'note': '潜伏池为空→按LEO-024铁律空仓，未回退涨停池',
                }
                with open(os.path.join(OUT_DIR, 'sunquan_status.json'), 'w') as _f:
                    def _jd(o):
                        import numpy as np
                        if isinstance(o, (np.bool_, np.integer, np.floating)):
                            return o.item()
                        return str(o)
                    json.dump(_out, _f, ensure_ascii=False, indent=2, default=_jd)
            except Exception as _e:
                print(f"   ⚠️ 空仓状态落盘失败: {_e}")
            return
        for g in gainers[:15]:
            g['pct'] = g['pct'] / 100 if abs(g.get('pct',0)) > 10 else g.get('pct', 0)
        
        stock_quotes = get_stock_quotes(gainer_codes)
        
        scored = []
        big_caps = []  # 回退模式：大市值龙头参考（>150亿不入选打板候选）
        zt_counter = {}
        qf_map = {q['sym']: q for q in qianfu_pool} if qianfu_pool else {}
        # 🆕 2026-08-07 双模式（用户指令：潜伏+涨停龙头都出票）
        mode_label = "潜伏票模式" if qf_map else "潜伏票模式(池空)"
        for code in gainer_codes[:80]:
            if qf_map:  # 潜伏模式（2026-08-03用户亲授：找明天可能被拉的票）
                q = qf_map.get(code)
                if not q:
                    continue
                # 🆕 2026-08-10 埋伏标准②：20日分位（低位<40%加分），失败返回None不阻塞
                _p20 = get_pos20(code) if code else None
                score, detail = score_qianfu_v1(q, pos20=_p20)
                # 🆕 2026-08-11 张飞预判接入：板块张飞分<50 → 降级-10并标红
                _zf_delta, _zf_label = zhangfei_panel(q.get('sector', ''))
                if _zf_delta:
                    score += _zf_delta
                    detail['张飞预判'] = _zf_label
                fc = q.get('mcap', 0)
                if fc < 30:
                    score += 8
                    detail['市值档'] = f"妖股档{fc:.0f}亿(+8)"
                elif fc < 50:
                    score += 5
                    detail['市值档'] = f"小盘档{fc:.0f}亿(+5)"
                else:
                    score += 2
                    detail['市值档'] = f"中盘档{fc:.0f}亿(+2)"
                scored.append((score, code, q.get('name', code), q.get('sector', '未知'), None, q.get('chg', 0), detail))
                continue
            sq = stock_quotes.get(code, {})
            if not sq:
                continue
            sq['pct'] = sq.get('pct', 0)
            
            # 回退模式：流通市值>150亿不入打板候选（转参考列表）
            fc = sq.get('float_cap', 0)
            if fc > 150:
                big_caps.append((sq.get('name', code), fc, sq.get('pct', 0)))
                continue
            
            # 找所属板块（2026-08-02修复：用候选池来源记录；未知→BLIND不虚给分）
            sector = code2sector.get(code, "未知")
            if sector != "未知":
                sector_chg = etf_data.get(sector, 0)
                sector_rank = hot_rank.get(sector, 99)  # 热点ETF排名
                # 行业涨停强度补充（打板语境：板块热度=板块内涨停家数）
                _zt_cnt = zt_counter.get(sector, 0)
                if _zt_cnt >= 5:
                    _zt_rank = 1
                elif _zt_cnt >= 3:
                    _zt_rank = 2
                elif _zt_cnt >= 2:
                    _zt_rank = 4
                else:
                    _zt_rank = 99
                if _zt_rank < sector_rank:
                    sector_rank = _zt_rank
                    sector_chg = None  # 行业涨停强度口径下无ETF涨跌数据
            else:
                sector_chg = None
                sector_rank = None
            
            score, detail = score_wuwei_v3(sector_rank, sq, cycle_data, etf_data)
            # 🆕 2026-08-11 张飞预判接入：板块张飞分<50 → 降级-10
            _zf_delta, _zf_label = zhangfei_panel(sector)
            if _zf_delta:
                score += _zf_delta
                detail['张飞预判'] = _zf_label
            # 市值分档加权（<50亿妖股档+8 / 50-150亿中盘档+4）
            if 0 < fc < 50:
                score += 8
                detail['市值档'] = f"妖股档{fc:.0f}亿(+8)"
            elif fc < 150:
                score += 4
                detail['市值档'] = f"中盘档{fc:.0f}亿(+4)"
            else:
                detail['市值档'] = "大盘(不入选)"
            scored.append((score, code, sq.get('name', code), sector, sector_chg, sq.get('pct', 0), detail))
        
        # 🆕 2026-08-07 双模式：潜伏票出完后，再跑【涨停龙头模式】（score_wuwei_v3，准涨停/涨停池）
        # 用户指令：两种模式都出票——潜伏(找明天可能被拉) + 涨停龙头(情绪打板)
        zt_scored = []
        zt_big = []
        try:
            limit_pool = get_limit_up_pool()
            quasi_pool = [g for g in gainers if 5 <= g.get('pct', 0) <= 9.9]
            zt_codes = []
            zt_code2sec = {}
            for _s in limit_pool:
                zt_codes.append(_s['code'])
                zt_code2sec[_s['code']] = _s.get('sector', '未知')
            for _g in quasi_pool:
                if _g['code'] not in zt_code2sec:
                    zt_codes.append(_g['code'])
                    zt_code2sec[_g['code']] = _g.get('sector', '未知')
            zt_codes = list(dict.fromkeys(zt_codes))
            # 🆕 2026-08-12 修复：涨停池按连板高度排序（连板越高=妖股核心=优先评分）
            #   背景：83只涨停只取前40只且按原始顺序（代码/封板时间），百花医药7板/北京文化3板等妖股被截掉
            _zt_lb = {_s['code']: _s.get('lianban', 1) for _s in limit_pool}
            zt_codes.sort(key=lambda c: -_zt_lb.get(c, 0))
            zt_quotes = get_stock_quotes(zt_codes)
            zt_cnt_map = {}
            for _s in limit_pool:
                _sec = _s.get('sector', '未知')
                if _sec != '未知':
                    zt_cnt_map[_sec] = zt_cnt_map.get(_sec, 0) + 1
            for code in zt_codes:
                sq = zt_quotes.get(code, {})
                if not sq:
                    continue
                sq['pct'] = sq.get('pct', 0)
                fc = sq.get('float_cap', 0)
                if fc > 150:
                    zt_big.append((sq.get('name', code), fc, sq.get('pct', 0)))
                    continue
                sector = zt_code2sec.get(code, "未知")
                if sector != "未知":
                    sector_chg = etf_data.get(sector, 0)
                    sector_rank = hot_rank.get(sector, 99)
                    _zt_cnt = zt_cnt_map.get(sector, 0)
                    if _zt_cnt >= 5:
                        _zt_rank = 1
                    elif _zt_cnt >= 3:
                        _zt_rank = 2
                    elif _zt_cnt >= 2:
                        _zt_rank = 4
                    else:
                        _zt_rank = 99
                    if _zt_rank < sector_rank:
                        sector_rank = _zt_rank
                        sector_chg = None
                else:
                    sector_chg = None
                    sector_rank = None
                score, detail = score_wuwei_v3(sector_rank, sq, cycle_data, etf_data)
                # 🆕 2026-08-12 连板因子：涨停池的lianban传入评分（妖股识别）
                _lb = _zt_lb.get(code, 0)
                if _lb >= 2:
                    _sq2 = dict(sq); _sq2['lianban'] = _lb
                    score, detail = score_wuwei_v3(sector_rank, _sq2, cycle_data, etf_data)
                # 🆕 2026-08-11 张飞预判接入：板块张飞分<50 → 降级-10
                _zf_delta, _zf_label = zhangfei_panel(sector)
                if _zf_delta:
                    score += _zf_delta
                    detail['张飞预判'] = _zf_label
                if 0 < fc < 50:
                    score += 8
                    detail['市值档'] = f"妖股档{fc:.0f}亿(+8)"
                elif fc < 150:
                    score += 4
                    detail['市值档'] = f"中盘档{fc:.0f}亿(+4)"
                else:
                    detail['市值档'] = "大盘(不入选)"
                zt_scored.append((score, code, sq.get('name', code), sector, sector_chg, sq.get('pct', 0), detail))
        except Exception as _e:
            print(f"   (涨停龙头模式失败: {_e})")
        
        scored.sort(key=lambda x: -x[0])
        zt_scored.sort(key=lambda x: -x[0])
        
        print(f"   {'名称':<10} {'板块':<8} {'评分':<6} {'阈值':<6} {'市值':<10} {'结论':<8}")
        print(f"   {'-'*55}")
        for score, code, name, sector, sc, pct, detail in scored[:5]:
            concl = '✅ 入池' if score >= threshold else ('👀 观察' if score >= threshold-15 else '❌ 放弃')
            if qf_map:
                fc = qf_map.get(code, {}).get('mcap', 0)
            else:
                fc = stock_quotes.get(code, {}).get('float_cap', 0)
            print(f"   {name:<10} {sector[:4]:<8} {score:<6} {threshold:<6} {fc:>6.0f}亿{'':<3} {concl:<8}")
        if big_caps:
            print(f"   (大市值参考不入选: {'、'.join(f'{n}({f:.0f}亿)' for n, f, _ in big_caps[:3])})")
        
        # 🆕 2026-08-07 双模式：输出【涨停龙头模式】榜（用户指令：两种都出票）
        print(f"\n{'='*65}")
        print(f"  ⚡ 涨停龙头模式（score_wuwei_v3·情绪打板）")
        print(f"{'='*65}")
        if zt_scored:
            print(f"   {'名称':<10} {'板块':<8} {'评分':<6} {'阈值':<6} {'今日%':<8} {'市值':<10} {'结论':<8}")
            print(f"   {'-'*62}")
            for score, code, name, sector, sc, pct, detail in zt_scored[:6]:
                concl = '✅ 入池' if score >= threshold else ('👀 观察' if score >= threshold-15 else '❌ 放弃')
                fc = zt_quotes.get(code, {}).get('float_cap', 0) if 'zt_quotes' in dir() else 0
                seal = '🔴' if pct >= 9.8 else ''
                print(f"   {seal}{name:<9} {sector[:4]:<8} {score:<6} {threshold:<6} {pct:>+6.1f}%{'':<2} {fc:>5.0f}亿{'':<2} {concl:<8}")
            if zt_big:
                print(f"   (大市值参考不入选: {'、'.join(f'{n}({f:.0f}亿)' for n, f, _ in zt_big[:3])})")
            if zt_scored and zt_scored[0][0] >= threshold:
                _zt = zt_scored[0]
                _ztp = zt_quotes.get(_zt[1], {})
                _ztchg = _ztp.get('pct', 0) or 0
                print(f"   🏆 涨停龙头最佳: {_zt[2]}({_zt[1]}) 评分{_zt[0]}≥{threshold} 今日{_ztchg:+.1f}%")
                for k, v in _zt[6].items():
                    print(f"      {k}: {v}")
                if _ztchg >= 9.8:
                    print(f"      买点: 已涨停(今日进不去)→明日9:25竞价观察，低开>3%放弃，回封/开板再评估")
                elif _ztchg >= 5:
                    print(f"      买点: 准涨停(+{_ztchg:.1f}%)：今日14:30-14:55尾盘或明日回踩不破今日均价买")
                else:
                    print(f"      买点: 今日尾盘/明日竞价按买点区间执行")
                if phase_block:
                    print(f"      结论: ⚠️ 情绪闸门={phase_name}·纪律从紧（仅超短快进快出，禁重仓，8月计划S/A级暂停）")
                else:
                    print(f"      结论: ✅ 可买入（周期={cycle_name}，阈值={threshold}）")
            else:
                _ztmax = zt_scored[0][0] if zt_scored else 0
                print(f"   无评分≥阈值{threshold}的涨停龙头候选 (最高{_ztmax})")
        else:
            print("   涨停龙头模式无候选（涨停池获取失败或为空）")
        
        if scored and scored[0][0] >= threshold:
            best = scored[0]
            print(f"\n   🏆 最佳候选: {best[2]}({best[1]})  评分{best[0]}≥阈值{threshold}")
            _, _, _, _, sc, pct, detail = best
            _sc = sc if sc is not None else 0.0  # 2026-08-02修复：板块未知时None安全打印
            print(f"      板块{best[3]}{_sc:+.1f}% | 个股{pct:+.1f}%")
            for k, v in detail.items():
                print(f"      {k}: {v}")
            # 买点标注（2026-08-03潜伏模式：埋伏位；回退模式：涨停/准涨停）
            if qf_map:
                _bq = qf_map.get(best[1], {})
                _bchg = _bq.get('chg', 0) or 0
                _bsector = _bq.get('sector', '')
                _binflow = _bq.get('inflow', 0)
                if _bchg <= 0:
                    _buy_hint = f"潜伏位(今日{_bchg:+.1f}%未启动·{_bsector}资金+{_binflow:.0f}亿)：今日14:30-14:55尾盘埋伏，止损-5%，明日冲高兑现"
                else:
                    _buy_hint = f"潜伏位(今日+{_bchg:.1f}%微涨·{_bsector}资金+{_binflow:.0f}亿)：今日尾盘或明日回踩买，止损-5%，明日冲高兑现"
            else:
                _bp = stock_quotes.get(best[1], {})
                _bchg = _bp.get('pct', 0) or 0
                if _bchg >= 9.8:
                    _buy_hint = f"已涨停(+{_bchg:.1f}%)：今日进不去→明日9:25竞价观察，低开>3%放弃，回封/开板再评估"
                elif _bchg >= 5:
                    _buy_hint = f"准涨停(+{_bchg:.1f}%)：今日14:30-14:55尾盘或明日回踩不破今日均价买"
                else:
                    _buy_hint = f"买点({_bchg:+.1f}%)：今日尾盘/明日竞价按买点区间执行"
            print(f"      买点: {_buy_hint}")
            if phase_block:
                print(f"      结论: ⚠️ 情绪闸门={phase_name}·纪律从紧（仅超短快进快出，禁重仓，8月计划S/A级暂停）")
            else:
                print(f"      结论: ✅ 可买入（周期={cycle_name}，阈值={threshold}）")
        else:
            max_score = scored[0][0] if scored else 0
            print(f"\n   无评分≥阈值{threshold}的候选 (最高{max_score})")
    
    # 5. 输出（2026-08-03：候选+最佳落盘，修复候选评分不存档缺陷）
    threshold_out = threshold if threshold else None
    output = {
        "time": now,
        "cycle": cycle_name,
        "cycle_val": cycle_val,
        "phase": phase_name,  # 🆕 2026-08-08 养家心法情绪时钟12阶段
        "phase_val": phase_val,
        "phase_reason": phase_reason,
        "phase_strategy": PHASE_STRATEGY.get(phase_name, '') if phase_name else '',
        "cycle_data": cycle_data,
        "hot_sectors": [{"name": n, "chg": c} for n, c in hot],
        "threshold": threshold_out,
        "candidates": [
            {"name": n, "code": c, "sector": s, "score": sc, "float_cap": round(stock_quotes.get(c, {}).get('float_cap', 0), 1),
             "status": "✅入池" if sc >= threshold_out else ("👀观察" if sc >= threshold_out-15 else "❌放弃")}
            for sc, c, n, s, _, _, _ in scored[:10]
        ],
        # V2.2（2026-08-14）：TOP3全出 + 观察哨——池内未买票次日竞价自动提醒（移远/游族/蓝箭三案例）
        "top3": [
            {"name": scored[i][2], "code": scored[i][1], "score": scored[i][0], "sector": scored[i][3],
             "detail": {k: v for k, v in scored[i][6].items()}} for i in range(min(3, len(scored)))
        ] if scored else [],
        "watch_list": [
            {"name": scored[i][2], "code": scored[i][1], "score": scored[i][0], "sector": scored[i][3]}
            for i in range(3, min(10, len(scored))) if scored[i][0] >= (threshold_out or 0) - 15
        ] if scored else [],
        "best": ({"name": scored[0][2], "code": scored[0][1], "score": scored[0][0], "sector": scored[0][3],
                   "detail": {k: v for k, v in scored[0][6].items()}} if scored else None),
    }
    def _json_default(o):
        import numpy as np
        if isinstance(o, (np.bool_, np.integer, np.floating)):
            return o.item()
        return str(o)
    with open(os.path.join(OUT_DIR, "sunquan_status.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=_json_default)
    print(f"\n💾 已保存: sunquan_status.json")


if __name__ == "__main__":
    # 默认：周日非交易时点
    from datetime import datetime
    now = datetime.now()
    hour = now.hour
    if hour < 15:
        # 交易时段：自动选最近窗口
        if hour < 10:
            t = f"{now.month}月{now.day}日 09:45"
        elif hour < 11:
            t = f"{now.month}月{now.day}日 10:15"
        else:
            t = f"{now.month}月{now.day}日 14:50"
    else:
        t = f"{now.month}月{now.day}日 {now.hour}:{now.minute:02d}"
    
    # 更新头标注
    import builtins
    print(f"\n【孙权扫描 — 快照时点：{t}】")
    sunquan_scan()
