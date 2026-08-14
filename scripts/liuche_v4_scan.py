#!/usr/bin/env python3
"""
刘彻 V4 · 全市场实时选股
==================================
新逻辑（2026-07-28 14:00）：
  1. 流通市值 50-150亿（硬过滤，无数据=淘汰）
  2. 今日涨幅 > -1% 且 < 所属板块中位数
  3. 成交额 > 1亿
  4. 振幅 < 8%
  5. 排除 ST/XD/DR/N新股
  6. ETF只用来判定"哪个板块今天强"
  7. 输出TOP3，按落后幅度排序

2026-08-02 改进（用户亲授·补涨路线正式固化）：
  8. 量能门槛：当前量比≥1.0 才入池（今日量/前5日均量）
  9. 滞涨性质区分：连涨≥5日且平量(量比<1.3) → 降级为观察(慢涨平量)，非买入
  10. K线数据缺失/量比不可得 → 淘汰（铁律：不编数据）

数据：关羽线1(ETF方向) + 线9(成分股+市值) + 腾讯日K(量比/连涨)
"""

import os, sys, json, datetime as dt, requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "memory", "liuche_output")
os.makedirs(OUT_DIR, exist_ok=True)

# 板块代码→名称（模块级，2026-08-02提升：线2轮动强势需复用）
ETF_MAP = {
    'sh512480':'半导体','sz159995':'芯片','sz159819':'AI','sh515070':'AI人工智能',
    'sh515880':'通信','sh562500':'机器人','sh512660':'军工','sh516160':'新能源',
    'sh515790':'光伏','sh512400':'有色','sh515220':'煤炭','sh516020':'化工',
    'sh512800':'银行','sh512880':'证券','sh512690':'酒','sz159928':'消费',
    'sh512010':'医药','sz159865':'养殖','sz159869':'游戏','sz159766':'旅游',
    'sz159805':'传媒','sh516970':'基建','sh512200':'地产','sh515210':'钢铁',
    'sh516110':'汽车','sz159996':'家电','sh515230':'软件','sh588000':'科创50',
    'sh510050':'上证50','sz159919':'沪深300',
}


def load_data():
    missing = []
    etf_data = {}  # code → {name, sector, pct}
    pool_data = {}  # code → {stocks}
    
    # 【修复】实时拉ETF行情，不依赖过期缓存
    try:
        codes = list(ETF_MAP.keys())
        url = f'http://hq.sinajs.cn/list={",".join(codes)}'
        r = requests.get(url, headers={'Referer':'http://finance.sina.com.cn',
                                       'User-Agent':'Mozilla/5.0'}, timeout=8)
        for line in r.text.strip().split('\n'):
            parts = line.split('=')
            if len(parts) != 2: continue
            code = parts[0].split('_')[-1].strip('"')
            d = parts[1].strip('"').split(',')
            if len(d) >= 32 and d[2]:
                yclose = float(d[2])
                now = float(d[3]) if d[3] else 0
                pct = round((now-yclose)/yclose*100, 2) if yclose else 0
                name = ETF_MAP.get(code, code)
                etf_data[code] = {'name': name, 'pct': pct}
    except Exception as e:
        missing.append(f"实时ETF行情失败: {e}")
        # 降级：用缓存
        try:
            with open(os.path.join(SCRIPT_DIR, "guanyu_status.json")) as f:
                status = json.load(f)
            etf_data = status.get("etf_snapshot", {})
        except Exception as e2:
            missing.append(f"缓存也失效: {e2}")
    
    try:
        with open(os.path.join(SCRIPT_DIR, "guanyu_pool.json")) as f:
            pool = json.load(f)
        pool_data = pool.get("sectors", {})
    except Exception as e:
        missing.append(f"guanyu_pool.json: {e}")
    
    return etf_data, pool_data, missing


st_stop = ['ST','*ST','S*ST','N','XD','DR','退','新股']

def is_st(name):
    return any(kw in name.upper() for kw in st_stop)


def is_limit_up(chg, sym):
    """按代码前缀判断是否涨停（2026-08-02修复：主板10%，创业板300/301、科创板688/689为20%）"""
    code = sym[2:] if sym and sym.startswith(('sh', 'sz', 'bj')) else (sym or '')
    if code.startswith(('300', '301', '688', '689')):
        return chg >= 19.9
    return chg >= 9.9


# ============================================================
# 2026-08-02：量比/连涨天数（腾讯日K补充，pool.json无此字段）
# ============================================================
def name_to_code(name):
    """腾讯智能搜索：股票名称→6位代码(带sh/sz前缀)"""
    import re
    try:
        r = requests.get(f'https://smartbox.gtimg.cn/s3/?v=2&q={name}&t=all',
                        headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        r.encoding = 'gbk'
        # 返回: v_hint="sz~002410~广联达~..."; 精确匹配名称优先
        for m in re.finditer(r'"(s[hz]|bj)~(\d{6})~([^~]+)~', r.text):
            if m.group(3) == name:
                return m.group(1) + m.group(2)
        m = re.search(r'"(s[hz]|bj)~(\d{6})~([^~]+)~', r.text)
        if m:
            return m.group(1) + m.group(2)
    except Exception:
        pass
    return None


def get_kline_metrics(sym):
    """腾讯日K(60日)：返回 (标准量比=今日量/前5日均量, 连涨天数, 中期量能=5日均量/20日均量, 20日分位)"""
    try:
        url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,60,qfq'
        d = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=6).json()
        kl = d['data'][sym].get('qfqday') or d['data'][sym].get('day') or []
        if len(kl) < 21:
            return None, None, None, None
        rows = [{'close': float(k[2]), 'high': float(k[3]), 'low': float(k[4]), 'vol': float(k[5])} for k in kl]
        today_vol = rows[-1]['vol']
        avg5 = sum(r['vol'] for r in rows[-6:-1]) / 5
        vol_ratio = today_vol / avg5 if avg5 > 0 else None
        avg5_all = sum(r['vol'] for r in rows[-5:]) / 5
        avg20 = sum(r['vol'] for r in rows[-20:]) / 20
        mid_ratio = avg5_all / avg20 if avg20 > 0 else None
        hi20 = max(r['high'] for r in rows[-20:])
        lo20 = min(r['low'] for r in rows[-20:])
        px = rows[-1]['close']
        pos20 = (px - lo20) / (hi20 - lo20) * 100 if hi20 > lo20 else 50.0
        streak = 0
        for i in range(len(rows) - 1, 0, -1):
            if rows[i]['close'] > rows[i-1]['close']:
                streak += 1
            else:
                break
        return vol_ratio, streak, mid_ratio, pos20
    except Exception:
        return None, None, None, None


def run_line2(etf_data, pool_data):
    """线2·轮动强势（2026-08-02新增）：张飞预测领涨板块内，明天可能大涨的短线股
    区别于线1(补涨)：线2选板块内涨幅领先+放量+低位的强势启动股
    """
    rot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory", "zhangfei_output", "zhangfei_rotation.json")
    if not os.path.exists(rot_path):
        print("\n⚠️ 无张飞轮动预测(zhangfei_rotation.json) → 线2跳过。先运行: python3 zhangfei_rotation.py")
        return
    with open(rot_path) as f:
        rot = json.load(f)
    pred_names = [p['name'] for p in rot.get('prediction', [])]
    if not pred_names:
        print("\n⚠️ 张飞预测为空 → 线2跳过")
        return

    # 板块名→pool key(6位ETF代码)
    name2code = {v: k[2:] if k.startswith(('sh','sz')) else k for k, v in ETF_MAP.items()}
    # 🆕 2026-08-11 张飞板块名→pool key 补充映射（张飞'医疗'→医药ETF512010）
    name2code['医疗'] = '512010'

    print(f"\n{'='*65}")
    print(f" 🎯 B模式·轮动强势 | 张飞预测领涨板块: {'/'.join(pred_names)}")
    print(f"    选股逻辑: 预测板块内 涨幅领先+放量+低位 的短线启动股（明天可能大涨）")
    print(f"    买入窗口: 14:00后（2026-08-03用户确认）")
    print(f"{'='*65}")

    line2 = []
    missing_sectors = []
    # 2026-08-11修订2：市值上限回收到200亿（用户亲授：小市值易拉板，"买那么大盘子干什么"）
    # 半导体千亿龙头可以进观察，但出票必须小盘优先
    MCAP_LIMIT = {'半导体': 200, '芯片': 200, 'AI': 200, 'AI人工智能': 200,
                  '通信': 200, '机器人': 200, '光伏': 200, '新能源': 200}
    for nm in pred_names:
        ec = name2code.get(nm)
        pd = pool_data.get(ec) if ec else None
        if not pd:
            missing_sectors.append(nm)
            continue
        median = pd.get('median_gain', 0)
        etf_chg = pd.get('etf_chg', 0)
        mcap_limit = MCAP_LIMIT.get(nm, 800)  # 未配置板块保持800亿
        for s in pd.get('stocks', []):
            sym_c = s.get('sym', '') or s.get('code', '')
            # 🆕 2026-08-12 用户铁律：买不了科创板 → 688开头一律排除
            if sym_c.startswith('688'):
                continue
            chg = s.get('chg', 0)
            amount = s.get('amount', 0)
            mcap = s.get('mcap', 0)
            name = s.get('code', '')
            if not mcap or mcap <= 0:
                continue
            mcap_yi = mcap / 1e8
            if mcap_yi < 50 or mcap_yi > mcap_limit:
                continue  # 短线市值下限50亿，上限按板块（半导体3000亿）
            # 2026-08-11修订：埋伏型选股——不追已启动，埋伏未启动/刚启动
            if chg < -1.0 or chg > 2.5:
                continue  # 埋伏窗口：今日-1%~+2.5%（已大涨>2.5%不追=兑现信号）
            if amount < 100000000:
                continue
            if is_st(name):
                continue
            sym = name_to_code(name)
            if sym and is_limit_up(chg, sym):
                continue  # 已涨停不追（主板10%/创科20%）
            # 2026-08-11修复：量比用pool实时vr（东财口径）——get_kline_metrics的
            #   "今日累计量/前5日均量"在午盘跑时只有0.5左右，永远过不了1.5门槛→永久无票
            vr = s.get('vr') or None
            pos20 = None
            streak = 0
            if vr is None or vr <= 0:
                # 回退：腾讯日K（仅当pool无vr时）
                _v, streak, _vr_mid, pos20 = get_kline_metrics(sym) if sym else (None, None, None, None)
                if _v is not None:
                    vr = _v
            else:
                # 分位仍需腾讯K线（pool无此字段），失败不阻塞（pos20=None=不判高位）
                _v, streak, _vr_mid, pos20 = get_kline_metrics(sym) if sym else (None, None, None, None)
            if vr is None or vr <= 0:
                continue  # 量比不可得→淘汰
            # 🔧 2026-08-14修复（刘彻永久空仓根因）：量比门槛1.5→1.0
            #   全市场缩量日量比1.5+的票极少；埋伏型逻辑（分位<50%+未启动）已控风险，1.0足够
            if vr < 1.0:
                continue  # 放量门槛：量比≥1.0（有资金进场迹象）
            if pos20 is not None and pos20 >= 50:
                continue  # 埋伏要求：20日分位<50%（低位才埋伏，LEO-028）；分位不可得不判死
            # 2026-08-11修订综合分：量比(资金进场)×3 + 低位(50-分位)×0.4 + 小涨×2 + 市值加分(小盘优先)
            low_bonus = round((50 - pos20) * 0.4, 1) if pos20 is not None else 0
            # 市值加分（用户亲授：小市值易拉板）：<50亿+10 / <100亿+6 / <150亿+3 / 其他0
            if mcap_yi < 50:
                mcap_bonus = 10
            elif mcap_yi < 100:
                mcap_bonus = 6
            elif mcap_yi < 150:
                mcap_bonus = 3
            else:
                mcap_bonus = 0
            score = round(vr * 3 + low_bonus + max(chg, 0) * 2 + mcap_bonus, 1)
            line2.append({
                'name': name, 'chg': chg, 'mcap': mcap_yi, 'amount': amount,
                'vol_ratio': vr, 'pos20': pos20, 'score': score,
                'sector': nm, 'etf_chg': etf_chg, 'streak': streak,
            })

    line2.sort(key=lambda x: -x['score'])
    if missing_sectors:
        print(f" ⚠️ 预测板块缺成分股数据(pool缺失): {'/'.join(missing_sectors)} → 需关羽线9重建pool覆盖")
    if not line2:
        print("\n 今日无票（预测板块内无 强势+放量+低位 组合）")
        return
    # 2026-08-11修订：pass线校准。新口径(量比×3+低位+小涨×2)分数范围5~45，
    # 旧60分线是“涨幅×6”口径的遗产（新口径永远达不到→永久无票）。
    # 30分=新口径下量比≥6且低位的最佳票档；样本<20前随用随调（龙虾章程）
    # 🔧 2026-08-14修复：量比门槛降为1.0后，分数范围收窄（量比1.0×3=3分），
    #   pass线30→15（量比1.0+低位40%+小涨2%≈13-15分），避免新口径再次永久无票
    ticket = line2[0]
    if ticket['score'] < 15:
        print(f"\n 今日无票：最高综合分{ticket['score']}<15（pass原则），候选: {ticket['name']}（{ticket['sector']} {ticket['chg']:+.2f}% 量比{ticket['vol_ratio']:.2f}）")

    print(f"\n 🎫 今日B模式票: {ticket['name']}（{ticket['sector']}）")
    print(f"    涨幅{ticket['chg']:+.2f}% | 市值{ticket['mcap']:.0f}亿 | 量比{ticket['vol_ratio']:.2f} | 分位{ticket['pos20']:.0f}% | 综合{ticket['score']}")
    print(f"    板块{ticket['sector']} 明日按操作建议买入")
    print(f" 参考观察:")
    for c in line2[1:4]:
        print(f"   {c['name']} {c['chg']:+.2f}% 量比{c['vol_ratio']:.2f} 分位{c['pos20']:.0f}% 综合{c['score']}")

    print(f"\n {'':2s} {'名称':<10s} {'板块':<6s} {'涨幅':>7s} {'市值':>6s} {'量比':>5s} {'分位':>6s} {'综合':>5s}")
    print(f" {'---':2s} {'----------':<10s} {'------':<6s} {'-------':>7s} {'------':>6s} {'-----':>5s} {'------':>6s} {'-----':>5s}")
    for i, c in enumerate(line2[:3], 1):
        amt_yi = c['amount'] / 1e8
        print(f" 🚀{i} {c['name']:<10s} {c['sector']:<6s} {c['chg']:>+7.2f}% {c['mcap']:>5.0f}亿 {c['vol_ratio']:>5.2f} {c['pos20']:>5.0f}% {c['score']:>5.1f}")
        print(f"     板块{c['sector']}今日ETF{c['etf_chg']:+.1f}% | 量比{c['vol_ratio']:.2f}放量 | 分位{c['pos20']:.0f}%低位启动 | 连涨{c.get('streak',0)}日")

    # 保存线2
    out2 = {
        "time": dt.datetime.now().strftime('%Y-%m-%d %H:%M'),
        "mode": "B模式·轮动强势(张飞预测板块)",
        "rule": "出1只票(综合分最高且≥15)，<15不出票（2026-08-14修复：原60分线新口径达不到）",
        "buy_window": "14:00后买入（2026-08-03用户确认）",
        "pred_sectors": pred_names,
        "ticket": ({"name": ticket['name'], "chg": ticket['chg'], "sector": ticket['sector'],
                     "vol_ratio": ticket['vol_ratio'], "pos20": ticket['pos20'], "score": ticket['score']}
                    if ticket['score'] >= 15 else None),
        "watchlist": [{"name": c['name'], "chg": c['chg'], "sector": c['sector'],
                        "vol_ratio": c['vol_ratio'], "pos20": c['pos20'], "score": c['score']}
                       for c in line2[:4]],
    }
    with open(os.path.join(OUT_DIR, "liuche_line2_output.json"), "w") as f:
        json.dump(out2, f, ensure_ascii=False, indent=2)
    print(f"\n 💾 已保存: liuche_line2_output.json")


def run():
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("=" * 65)
    print(f" 刘彻 V4 · 全市场实时选股 | {now}")
    print("=" * 65)
    
    # 读数据
    etf_data, pool_data, load_gaps = load_data()
    if load_gaps:
        for g in load_gaps:
            print(f" ⚠️ {g}")
    
    # 1. ETF今日涨幅>0的板块
    pos_etf_codes = []
    for ec, ed in etf_data.items():
        if ed.get('pct', -99) > 0:
            pos_etf_codes.append(ec)
    
    print(f"\n📡 ETF今日涨幅>0: {len(pos_etf_codes)}个板块")
    for ec in pos_etf_codes:
        ed = etf_data.get(ec, {})
        print(f"  🟢 {ed.get('name','')} +{ed.get('pct',0):.2f}%")
    
    # 2026-08-03：关羽资金方向过滤——只允许在主力净流入板块选票（避免追高位AI/软件）
    # 🔧 2026-08-14修复（刘彻永久空仓根因）：改为软过滤——资金方向只做标注，不再排除板块
    #   病根：资金方向是概念级（一带一路/味蕾经济），ETF是板块级（半导体/证券），两套命名体系交集≈0
    #   → ETF涨12个被砍11个只剩通信 → 永久无票。改为：ETF涨+个股放量即可入池，资金方向仅标注。
    fund_dir = {}
    fund_path = os.path.join(SCRIPT_DIR, '..', 'memory', 'guanyu_fund_direction.json')
    if os.path.exists(fund_path):
        try:
            fdir = json.load(open(fund_path))
            for s in fdir.get('sectors', []):
                if (s.get('inflow') or 0) >= 3:  # 净流入≥3亿
                    fund_dir[s['name']] = s['inflow']
        except Exception as e:
            print(f" ⚠️ 资金方向文件读取失败: {e}")
    if fund_dir:
        kept = []
        # 2026-08-03：资金方向概念名 → pool板块名 别名映射（push2delay概念名≠ETF名）
        # 2026-08-10扩充：医药系12个 + 养殖(味蕾经济/猪肉) + 银行(破净) + 钢铁/地产 + 基建(化债) + 煤炭(煤化工) + 上证50(红利/趋势)
        fund_alias = {
            'HJT电池': '光伏', '光伏设备': '光伏', '钙钛矿电池': '光伏',
            '绿色电力': '电力', '智能电网': '电网', '抽水蓄能': '电力',
            '核能核电': '核电', '可控核聚变': '核电', '雅下水电概念': '电力',
            '商业航天': '商业航天', '卫星导航': '卫星', '反内卷概念': '消费',
            # 医药系（12个概念→医药）
            '创新医疗服务': '医药', '医药医疗风格': '医药', 'AI制药': '医药', 'CRO': '医药',
            '精准诊断': '医药', '体外诊断': '医药', '基因测序': '医药', '精准医疗': '医药',
            '合成生物': '医药', 'CAR-T细胞疗法': '医药', '创新药': '医药', '互联医疗': '医药',
            # 消费/养殖/酒
            '消费风格': '消费', '超级品牌': '消费',
            '味蕾经济': '养殖', '猪肉概念': '养殖',
            '酿酒概念': '酒', '白酒': '酒',
            # 低估值破净系（银行/钢铁/地产）
            '破净股': '银行', '长期破净': '钢铁', '低市净率': '地产',
            # 化债/基建
            '化债(AMC)概念': '基建',
            # 周期
            '煤化工概念': '煤炭',
            # 大盘价值
            '红利股': '上证50', '趋势股': '上证50',
            # 半导体链（今日不在上涨板块，预留给轮入日）
            '高带宽内存': '半导体', '中芯概念': '半导体', '光刻机': '半导体',
        }
        for ec in pos_etf_codes:
            ed = etf_data.get(ec, {})
            name = ed.get('name', '')
            # 名称包含匹配：pool板块名 vs 资金方向名（如 电力↔绿色电力）
            hit = any(name in fn or fn in name for fn in fund_dir)
            if not hit:
                # 别名映射匹配：资金方向概念 → pool板块
                for fn, alias in fund_alias.items():
                    if fn in fund_dir and (alias in name or name in alias):
                        hit = True
                        break
            if hit:
                kept.append(ec)
            else:
                # 🔧 2026-08-14：软过滤——不在资金方向也保留（避免永久无票），标注供参考
                kept.append(ec)
                print(f"  🟡 {name} 不在资金净流入方向（软过滤保留·仅标注）")
        print(f"\n📡 资金方向过滤后板块: {len(kept)}个（原{len(pos_etf_codes)}·软过滤全部保留）")
        for ec in kept:
            ed = etf_data.get(ec, {})
            print(f"  🟢 {ed.get('name','')} +{ed.get('pct',0):.2f}%")
        pos_etf_codes = kept
    else:
        print(" ⚠️ 资金方向文件缺失/为空 → 回退：按ETF涨幅选板块（无资金约束）")
    
    # 2. 全市场筛选
    all_candidates = []
    for ec in pos_etf_codes:
        # pool.json的key只有数字部分（无sh/sz前缀），需要strip
        ec_short = ec[2:] if ec.startswith(('sh','sz')) else ec
        pd = pool_data.get(ec) or pool_data.get(ec_short)
        if not pd: continue
        
        stocks = pd.get('stocks', [])
        median_gain = pd.get('median_gain', 0)
        etf_chg = pd.get('etf_chg', 0)
        etf_name = pd.get('name', ec)
        
        for s in stocks:
            sym_c = s.get('sym', '') or s.get('code', '')
            # 🆕 2026-08-12 用户铁律：买不了科创板 → 688开头一律排除
            if sym_c.startswith('688'):
                continue
            chg = s.get('chg', 0)
            amount = s.get('amount', 0)
            amp = s.get('amp', 0)
            mcap = s.get('mcap', 0)
            name = s.get('code', '')
            
            # 硬过滤条件（不通过直接淘汰）
            if not mcap or mcap <= 0:
                continue  # 无市值数据直接淘汰
            mcap_yi = mcap / 1e8
            if mcap_yi < 50 or mcap_yi > 150:
                continue  # 市值不在50-150亿
            if chg <= -1.0:
                continue  # 涨幅>-1%
            # 2026-07-31修复：默认强势模式（板块内涨幅≥中位·未涨停），不再只选落后补涨
            if amount < 100000000:
                continue  # 成交额>1亿
            # 2026-07-31修复：普涨日强票振幅大是特征非风险，振幅过滤移除
            # （改为在风险分里处理，不再硬过滤）
            if is_st(name):
                continue
            
            # 2026-08-02：量能门槛——量比≥1.0 才入池（今日量/前5日均量）
            # K线数据缺失/量比不可得 → 淘汰（铁律：不编数据）
            sym = name_to_code(name)
            # 2026-08-02修复：涨停判断按板块（主板10%/创科20%），避免误杀创业板强势票
            if sym and is_limit_up(chg, sym):
                continue  # 已涨停不追
            # 🆕 2026-08-12修复（LEO-032同根）：量比改用pool实时vr（东财口径），
            #   弃用get_kline_metrics腾讯日K"今日累计量/前5日均量"——午盘跑只有0.5永远过不了1.0门槛→永久无票
            #   （B模式8/11已改，A模式漏改=今天发现）
            vr = s.get('vr') or None
            streak = 0
            vr_mid = None
            pos20 = None
            if vr is None or vr <= 0:
                _v, streak, _vr_mid, pos20 = get_kline_metrics(sym) if sym else (None, None, None, None)
                if _v is not None:
                    vr = _v
            else:
                _v, streak, _vr_mid, pos20 = get_kline_metrics(sym) if sym else (None, None, None, None)
            if vr is None or vr <= 0:
                continue  # 量比不可得 → 不入池
            if vr < 1.0:
                continue  # 量能不足 → 淘汰
            # 2026-08-03用户亲授：刘彻不追高——20日分位>80%（高位）或连涨>5日 直接排除
            if (pos20 or 0) > 80:
                continue  # 高位排除（软件分位96%这类直接毙）
            if (streak or 0) > 5:
                continue  # 连涨>5日排除（追高风险）
            # 滞涨性质区分：连涨≥5日且中期量能平(5日/20日均量<1.3) → 降级为观察（慢涨平量，非买入）
            status = '观察(慢涨平量)' if (streak or 0) >= 5 and (vr_mid or 0) < 1.3 else '买入候选'
            
            lag = round(median_gain - chg, 2)
            strength = round(chg - median_gain, 2)  # 2026-07-31: 强势度=涨幅-中位
            all_candidates.append({
                'name': name, 'chg': chg, 'amount': amount,
                'amp': amp, 'mcap': mcap_yi,
                'lag': lag, 'strength': strength, 'median': median_gain,
                'etf_name': etf_name, 'etf_chg': etf_chg,
                'vol_ratio': vr, 'streak': streak, 'status': status,  # 2026-08-02
                'vr_mid': vr_mid, 'pos20': pos20,  # 🆕 2026-08-10 埋伏标准②：20日分位
            })
    
    # 3. 排序（2026-07-31修复：强势模式按涨幅排序）
    # 2026-08-02固化：A模式出1只票=第一个'买入候选'；观察态/无候选=不出票
    all_candidates.sort(key=lambda x: -x['chg'])
    buy_cands = [c for c in all_candidates if c['status'] == '买入候选']
    ticket = buy_cands[0] if buy_cands else None
    
    print(f"\n{'='*65}")
    print(f" 🏆 A模式·补涨强势（明天机会·晚盘买入）")
    print(f"    买入窗口: 14:30-14:55 尾盘 | 规则: 出一只票，无合格候选不出票")
    print(f"{'='*65}")
    if ticket:
        t = ticket
        _p20 = t.get('pos20')
        _amb = '🟢低位埋伏' if (_p20 is not None and _p20 < 40) else ('🟡中位' if _p20 is not None else '分位未知')
        print(f"\n 🎫 今日A模式票: {t['name']}（{t['etf_name']}）")
        print(f"    涨幅{t['chg']:+.2f}% | 市值{t['mcap']:.0f}亿 | 成交{t['amount']/1e8:.1f}亿 | 量比{t['vol_ratio']:.2f} | 连涨{t.get('streak',0)}日 | 20日分位{_p20 if _p20 is not None else 'N/A'}%")
        print(f"    板块中位{t['median']:+.1f}% → 强势度{t['strength']:+.1f}%")
        print(f"    状态: {t['status']} | {_amb} | 尾盘14:30-14:55买入，明天兑现")
        print(f"\n 参考观察（不买入）:")
        for c in all_candidates[:3]:
            if c['name'] == t['name'] and c['etf_name'] == t['etf_name']:
                continue
            print(f"   {c['name']} {c['chg']:+.2f}% 量比{c['vol_ratio']:.2f} {c['status']}")
    else:
        print("\n 今日无票：无'买入候选'状态（观察态/慢涨平量不买入）")
    
    # 统计
    print(f"\n📊 过滤链: 全市场169只ETF成分股 → 市值50-150亿 {sum(1 for pd in pool_data.values() for s in pd.get('stocks',[]) if s.get('mcap') and 50e8 <= s['mcap'] <= 150e8)}只 → 通过全部条件(含量比≥1.0) {len(all_candidates)}只（买入候选{buy_cands.__len__()}只）")
    
    # 保存
    output = {
        "time": now,
        "mode": "A模式·补涨强势(晚盘买入·明天兑现)",
        "buy_window": "14:30-14:55 尾盘",
        "rule": "出一只票，无买入候选不出票",
        "pos_etfs": len(pos_etf_codes),
        "total_candidates": len(all_candidates),
        "ticket": ({"name": ticket['name'], "chg": ticket['chg'], "mcap": ticket['mcap'],
                     "lag": ticket['lag'], "etf_name": ticket['etf_name'],
                     "vol_ratio": ticket.get('vol_ratio'), "streak": ticket.get('streak'),
                     "status": ticket.get('status')} if ticket else None),
        "watchlist": [{"name": c['name'], "chg": c['chg'], "etf_name": c['etf_name'],
                        "vol_ratio": c.get('vol_ratio'), "status": c.get('status')}
                       for c in all_candidates[:5]],
    }
    with open(os.path.join(OUT_DIR, "liuche_v4_output.json"), "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n 💾 已保存: liuche_v4_output.json")

    # 2026-08-02：线2·轮动强势（张飞预测板块内短线启动股）
    run_line2(etf_data, pool_data)

    print(f"\n{'='*65}")
    print(f" ✅ 刘彻V4完成")
    print(f"{'='*65}")

if __name__ == "__main__":
    run()
