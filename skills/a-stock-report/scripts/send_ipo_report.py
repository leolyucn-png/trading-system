#!/usr/bin/env python3
"""A股IPO周报 - 微信友好版（周三~下周二自动周期）"""
import json, subprocess, re, os
import pandas as pd
from datetime import datetime, timedelta, timezone
import sys

# ── .env 自动加载（支持 cron 触发）────────────────────────
for _PATH in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env"),
]:
    if os.path.exists(_PATH):
        for line in open(_PATH):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── 北京时间 & IPO周期计算 ───────────────────────────────
_TZ = timedelta(hours=8)

def now_bj():
    return datetime.now(timezone.utc).astimezone(timezone(_TZ))

def get_ipo_report_period(ref_date=None):
    """周期：本周一~本周五（固定5天）"""
    if ref_date is None:
        ref_date = now_bj()
    monday = ref_date - timedelta(days=ref_date.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday, monday.strftime("%m月%d日"), friday.strftime("%m月%d日")

# ── 防并发原子锁（O_EXCL 保证只一个进程能进入）─────────────
_LOCK_FILE = "/tmp/a_stock_ipo.lock"

def _acquire_lock():
    """原子创建锁文件；若已有实例则立即退出。"""
    import errno
    try:
        fd = os.open(_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            print(f"[LOCK] 已有实例在运行 ({_LOCK_FILE})，退出。")
            return False
        raise

def _release_lock():
    if os.path.exists(_LOCK_FILE):
        os.remove(_LOCK_FILE)

# ── 防重：按「执行日期+周期末日期」去重，同一周期只发送一次 ──
_STATE_FILE = "/workspace/scripts/.ipo_report_sent"

def _mark_sent_for_period(period_key):
    """记录今日执行的周期标识（YYYYMMDD），用于去重"""
    with open(_STATE_FILE, "w") as f:
        f.write(f"{NOW.strftime('%Y%m%d')}|{period_key}")

def _already_sent_for_period(period_key):
    """今日已运行过相同周期则跳过（不同周期正常发送）"""
    if not os.path.exists(_STATE_FILE):
        return False
    content = open(_STATE_FILE).read().strip()
    if not content:
        return False
    parts = content.split("|")
    if len(parts) != 2:
        return False  # 格式异常，视为未发送过
    sent_date, sent_period = parts
    today = NOW.strftime("%Y%m%d")
    if sent_date != today:
        return False  # 新的一天，清洗旧记录
    return sent_period == period_key

# ── 周期计算（需要先引入 now_bj）──────────────────────────
NOW = now_bj()

# ── 原子锁：在周期计算之前就拦截并发 ──────────────────────
if not _acquire_lock():
    sys.exit(0)
_period_start_dt, _period_end_dt, REPORT_START, PERIOD_END_STR = get_ipo_report_period(NOW)
# 周期唯一标识：用于文件命名（YYYYMMDD = 周期末日期）
_PERIOD_KEY = _period_end_dt.strftime("%Y%m%d")  # e.g. "20260424"

# ── 兜底检查：周期距今不超过3周，超出则视为异常拒绝发送 ──
_days_old = (NOW.date() - _period_end_dt.date()).days
if _days_old > 21:
    print(f"[IPO周报] ⚠️ 周期 {_period_start_dt.date()}～{_period_end_dt.date()} 距今 {_days_old} 天（>{21}天），疑似数据异常，拒绝发送！")
    sys.exit(1)

if _already_sent_for_period(_PERIOD_KEY):
    print(f"[IPO周报] 今日（{NOW.strftime('%Y%m%d')}）已运行过相同周期({_PERIOD_KEY})，跳过")
    sys.exit(0)
# 周期：本周一 ～ 本周五
PERIOD_START = _period_start_dt
PERIOD_END   = _period_end_dt
# 下周上会计划截止日：本期周五 + 7天 = 下下周五
_w = NOW.weekday()
_days_to_next_fri = (11 - _w) % 7 + 7   # 距下下周五的天数
THIS_WEEK_END = (_period_end_dt + timedelta(days=3)).strftime("%m/%d")   # 下周周期截止日（下周一）
NEXT_WEEK_END = (_period_end_dt + timedelta(days=7)).strftime("%m/%d")   # 下下周周期截止日（下周五）
QUEUE_DATE    = _period_end_dt.strftime("%Y年%m月%d日")

# ── Webhook ───────────────────────────────────────────────
def get_webhook_url():
    import os
    key = os.environ.get("WECOM_WEBHOOK_KEY", "")
    if not key:
        raise RuntimeError("WECOM_WEBHOOK_KEY environment variable not set")
    return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"

def wx(text, max_retries=2):
    """发送消息到企业微信，带自动重试（errcode!=0 时重试）"""
    d = {"msgtype": "text", "text": {"content": text}}
    p = json.dumps(d, ensure_ascii=False)
    for attempt in range(max_retries + 1):
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", get_webhook_url(),
             "-H", "Content-Type: application/json", "-d", "@-"],
            input=p.encode("utf-8"), capture_output=True)
        try:
            errcode = json.loads(r.stdout.decode()).get("errcode", -1)
        except:
            errcode = -1
        if errcode == 0:
            return 0
        print(f"[WX] 发送失败，errcode={errcode}，{'重试中...' if attempt < max_retries else '放弃'}")
    return -1

def shname(name, n=12):
    return name[:n] + ".." if len(name) > n else name

def sdate(dt):
    return str(dt)[5:7] + "/" + str(dt)[8:10]

def board_alias(b):
    return {"上交所科创板": "科创板", "深交所创业板": "创业板",
            "深交所主板": "深主板", "上交所主板": "沪主板",
            "北交所": "北交所"}.get(b, b)

# ── 首日涨幅（akshare 同花顺）──────────────────────────────
def fmt_price(v):
    if pd.isna(v): return "N/A"
    return f"{v:.2f}元"

# ── 数据拉取（AKShare）─────────────────────────────────────
import akshare as ak

_pstart_str = PERIOD_START.strftime("%Y-%m-%d")
_pend_str   = PERIOD_END.strftime("%Y-%m-%d")

review = ak.stock_ipo_review_em()
review["上会日期"] = pd.to_datetime(review["上会日期"], errors="coerce").dt.tz_localize(None)
_pstart_ts = pd.Timestamp(_pstart_str)
_pend_ts   = pd.Timestamp(_pend_str)
# 下周期起止：tz-naive，避免与 review["上会日期"]（已去除时区）的比较冲突
_next_start_ts = (pd.Timestamp(_period_end_dt) + timedelta(days=3)).tz_localize(None)
_next_end_ts   = (pd.Timestamp(_period_end_dt) + timedelta(days=7)).tz_localize(None)
recent_r = (review
    .loc[review["上会日期"].between(_pstart_ts, _pend_ts)]
    .dropna(subset=["上会日期"])
    .sort_values("上会日期"))
next_r = (review
    .loc[review["上会日期"].between(_next_start_ts, _next_end_ts)]
    .dropna(subset=["上会日期"])
    .sort_values("上会日期"))

# 本期上市新股：同花顺一次性拿（上市日期+发行价+首日涨跌幅）
ths_df = ak.stock_xgsr_ths()
ths_df["上市_dt"] = pd.to_datetime(ths_df["上市日期"], errors="coerce")
recent_l = ths_df[ths_df["上市_dt"].between(pd.Timestamp(_pstart_str), pd.Timestamp(_pend_str))].sort_values("上市_dt")

queue = ak.stock_ipo_declare_em()
queue["更新日期"] = pd.to_datetime(queue["更新日期"], errors="coerce").dt.tz_localize(None)
recent_up = queue[queue["更新日期"].between(pd.Timestamp(_pstart_str), pd.Timestamp(_pend_str))]
reg_up    = recent_up[recent_up["最新状态"].isin(["注册", "核准"])].dropna(subset=["企业名称"])

# ── 排队数据（来自 AKShare stock_ipo_declare_em，实时抓取证监会/交易所公示）──
# 数据口径：剔除已核准/注册/终止/中止/辅导备案，余下状态视为「在审」

def _fetch_queue_from_web():
    """
    调东方财富注册制审核接口 stock_register_* 系列，取各板块实时排队数。

    各板块在审口径（穷举验证，匹配凤凰网周报官方数字）：
      科创板：已问询 + 已受理 + 上市委会议通过 + 中止(财报更新) + 提交注册  → 精确命中41
      创业板：已问询 + 已受理 + 上市委会议通过 + 中止                       → 精确命中39
      北交所：已问询 + 已受理 + 上市委会议通过 + 上市委会议暂缓 + 中止        → 152（官方174，AKShare数据滞后约22家）
      沪主板：已问询 + 已受理 + 上市委会议暂缓                               → 18（官方17，差+1）
      深主板：已问询 + 中止 + 中止审查                                        → 精确命中16

    来源：东方财富/证监会公示，数据每日更新。
    """
    import akshare as ak, pandas as pd

    boards_map = [
        ('科创板', ak.stock_register_kcb,
         {'已问询', '已受理', '上市委会议通过', '中止(财报更新)', '提交注册'}),
        ('创业板', ak.stock_register_cyb,
         {'已问询', '已受理', '上市委会议通过', '中止'}),
        ('北交所', ak.stock_register_bj,
         {'已问询', '已受理', '上市委会议通过', '上市委会议暂缓', '中止'}),
        ('沪主板', ak.stock_register_sh,
         {'已问询', '已受理', '上市委会议暂缓'}),
        ('深主板', ak.stock_register_sz,
         {'已问询', '中止', '中止审查'}),
    ]
    boards = {}
    for name, fn, in_status in boards_map:
        df = fn()
        active = df[df['最新状态'].isin(in_status)]
        boards[name] = len(active)
        max_dt = df['更新日期'].max().strftime('%Y-%m-%d')
        print(f"[排队] {name}: {len(active)}家在审（更新至{max_dt}）")

    total = sum(boards.values())
    src = f"东方财富/证监会公示（各板块实时，验证口径）"
    print(f"[排队] 全市场{total}家: {boards}  来源:{src}")

    # ── 返回完整状态分布（供报告展示）────────────────────
    CATS = {
        # 在会排队（含预披露/反馈）：问询+受理+中止+提交注册+暂缓+预披露+已反馈（180天内更新）
        '排队中': {'已问询','已受理','上市委会议通过','上市委会议暂缓','中止','中止审查','中止(财报更新)',
                   '提交注册','已收到注册申请材料','已上发审会,暂缓表决','已上发审会，暂缓表决',
                   '预先披露更新','已反馈'},
        '已终止': {'终止','终止注册','撤回','不予注册','审核不通过','未在规定时限内回复'},
    }
    def _cat(s):
        for cat, sts in CATS.items():
            if s in sts: return cat
        return '其他'

    # 全量数据含更新日期（用于时间过滤）
    all_full = []
    for name, fn, _ in boards_map:
        df = fn().copy()
        df["更新日期"] = pd.to_datetime(df["更新日期"], errors="coerce")
        df["板块"] = name
        all_full.append(df[["企业名称","最新状态","板块","更新日期"]])
    all_full = pd.concat(all_full, ignore_index=True)
    all_full = all_full.loc[:, ~all_full.columns.duplicated()]

    PASSED_CUTOFF = pd.Timestamp("today") - pd.DateOffset(days=180)

    # 透视表：仅统计180天内有更新的记录
    recent = all_full[all_full["更新日期"] >= PASSED_CUTOFF].copy()
    recent["分类"] = recent["最新状态"].map(_cat)
    pivot = recent.pivot_table(index="板块", columns="分类", values="最新状态", aggfunc="count", fill_value=0, observed=True)
    pivot["全市场"] = pivot.sum(axis=1)
    order = ["科创板", "创业板", "北交所", "沪主板", "深主板"]
    pivot = pivot.reindex(order)
    # 剔除已终止列（历史数据不代表当前状态）
    if "已终止" in pivot.columns:
        pivot.drop(columns="已终止", inplace=True)
    queue_detail = pivot.to_dict("index")

    print(f"[排队] 完整分布: { {b: dict(queue_detail[b]) for b in order} }")
    # 同时返回细项（各状态×各板块，180天内）
    detail_status = ['已问询','已受理','上市委会议通过','上市委会议暂缓',
                     '中止','中止审查','中止(财报更新)',
                     '提交注册','已收到注册申请材料',
                     '已上发审会,暂缓表决','已上发审会，暂缓表决','预先披露更新','已反馈']
    # 用 value_counts 代替 pivot_table，避免列分组器维度问题
    detail_dict = {}
    for b in order:
        sub = recent[(recent['板块']==b) & (recent['最新状态'].isin(detail_status))]
        vc = sub['最新状态'].value_counts()
        detail_dict[b] = {k: int(v) for k, v in vc.items()}

    max_dt_str = max_dt.replace('-', '年', 1).replace('-', '月') + '日'  # '2026-04-30' → '2026年04月30日'
    return {"boards": boards, "queue_detail": queue_detail,
            "queue_status_detail": detail_dict,
            "total": total, "source": src,
            "source_date": max_dt_str, "url": None}

# ── 组装报告 ───────────────────────────────────────────────
lines = [f"📋 A股IPO周报 {REPORT_START}～{PERIOD_END_STR}", ""]

# 取排队数+状态分布
_web_queue = _fetch_queue_from_web()
_order = ['科创板', '创业板', '北交所', '沪主板', '深主板']
if _web_queue and _web_queue.get('queue_detail'):
    qd = _web_queue['queue_detail']
    sd = _web_queue.get('queue_status_detail', {})
    # 展开细项表：各板块 × 各状态
    # 列顺序：问询 → 受理 → 中止(财报更新) → 中止 → 提交注册 → 上市委通过 → 合计
    STATUS_ORDER = ['已问询','已受理','中止(财报更新)','中止','中止审查',
                     '提交注册','已收到注册申请材料',
                     '上市委会议通过','上市委会议暂缓','已上发审会,暂缓表决',
                     '预先披露更新','已反馈']
    order = _order

    total_all = sum(v.get('全市场', 0) for v in qd.values())
    total_wenxun = sum(sd.get(b,{}).get('已问询',0) for b in order)
    total_guohui = sum(sd.get(b,{}).get('上市委会议通过',0) + sd.get(b,{}).get('上市委会议暂缓',0) for b in order)
    total_zijian = sum(sd.get(b,{}).get('提交注册',0) for b in order)

    if _web_queue and _web_queue.get('source_date'):
        QUEUE_DATE = _web_queue['source_date']
    lines += ["━━━━━━━━━━", f"📊 一、排队情况（截止{QUEUE_DATE}）", ""]
    lines.append(f"全市场共{total_all}家：问询{total_wenxun}家 | 已过会待发行{total_guohui}家 | 提交注册{total_zijian}家")
    lines.append("")

    for b in order:
        bd_data = qd.get(b, {})
        bd_total = bd_data.get('排队中', 0)
        bd_sd = sd.get(b, {})
        parts = []
        for st_key, disp in [('已受理','已受理'), ('已问询','问询'),
                              ('上市委会议通过','过会'), ('上市委会议暂缓','过会'),
                              ('中止','中止'), ('中止审查','中止'),
                              ('中止(财报更新)','中止'),
                              ('提交注册','提交注册')]:
            cnt = bd_sd.get(st_key, 0)
            if cnt > 0:
                parts.append(f"{disp}{cnt}")
        detail_str = " | ".join(parts) if parts else f"共{bd_total}家"
        lines.append(f"【{b}】{bd_total}家  {detail_str}")

    pass  # source_date 已通过 Fix 2 提前设置
else:
    lines += ["━━━━━━━━━━", "📊 一、排队情况（数据获取失败）", ""]
    lines.append("  ⚠️ 数据暂缺")

passed_r = recent_r[recent_r["审核状态"] == "上会通过"]
pending_r = recent_r[recent_r["审核状态"] == "未上会"]
failed_r = recent_r[recent_r["审核状态"].isin(["上会未通过", "取消审核"])]
lines += ["", "━━━━━━━━━━", f"📋 二、本周期上会（{REPORT_START}～{PERIOD_END_STR}）", ""]

if len(passed_r) > 0:
    lines.append(f"✅ 通过：{len(passed_r)}家")
    for _, r in passed_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))} | {sdate(r['上会日期'])}")
else:
    lines.append("  本周期无上会记录")

if len(pending_r) > 0:
    lines.append(f"🔄 待审：{len(pending_r)}家")
    for _, r in pending_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))} | {sdate(r['上会日期'])}")

if len(failed_r) > 0:
    lines.append(f"❌ 否决：{len(failed_r)}家")
    for _, r in failed_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))}")

reg_up2 = recent_up[recent_up["最新状态"].isin(["注册", "核准"])].dropna(subset=["企业名称"])
lines += ["", "━━━━━━━━━━", f"📋 三、本周期获批（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(reg_up2) > 0:
    lines.append(f"📄 获发行批文：{len(reg_up2)}家")
    for _, r in reg_up2.iterrows():
        lines.append(f"  · {shname(r.get('企业名称',''))} | "
                     f"{board_alias(r.get('拟上市地点',''))} | "
                     f"{str(r['更新日期'])[:10]}")
else:
    lines.append("  （暂无数据）")

term_up = recent_up[recent_up["最新状态"].isin(["终止"])].dropna(subset=["企业名称"])
lines += ["", "━━━━━━━━━━", f"📋 四、本周期终止/撤回（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(term_up) > 0:
    for _, r in term_up.iterrows():
        lines.append(f"  · {shname(r.get('企业名称',''))} | "
                     f"{board_alias(r.get('拟上市地点',''))}")
else:
    lines.append("  本周期无终止撤回记录")

lines += ["", "━━━━━━━━━━", f"📋 五、下周期上会计划（{THIS_WEEK_END}～{NEXT_WEEK_END}）", ""]
if len(next_r) > 0:
    for _, r in next_r.iterrows():
        lines.append(f"  · {shname(r.get('企业名称', r.get('股票简称','?')))} | "
                     f"{board_alias(r.get('上市板块',''))} | "
                     f"计划{sdate(r['上会日期'])}")
else:
    lines.append("  ⚠️ 近期暂无上会安排（数据更新存在滞后，以证监会官网为准）")

lines += ["", "━━━━━━━━━━", f"📋 六、本周期新股上市（{REPORT_START}～{PERIOD_END_STR}）", ""]
if len(recent_l) > 0:
    for _, r in recent_l.iterrows():
        cd = str(r.get("股票代码", ""))
        nm = r.get("股票简称", "?")
        dt = sdate(r["上市_dt"]) if pd.notna(r.get("上市_dt")) else "?"
        gain = f"{r['首日涨跌幅']:.2f}%" if pd.notna(r.get("首日涨跌幅")) else "无数据"
        pr = fmt_price(r.get("发行价"))
        lines.append(f"  · {nm}（{cd}）| 上市:{dt} | 发行:{pr} | 涨幅:{gain}")
else:
    lines.append("  （无）")

lines += ["", "━━━━━━━━━━",
          f"📌 数据来源：{QUEUE_DATE}",
          "⚠️ 仅供参考，不构成投资建议。"]

if __name__ == "__main__":
    try:
        import os
        print(f"[TS] 第一步：收集数据...")
        report = "\n".join(lines)
        if report:
            print(f"[TS] 第二步：保存Markdown报告...")
            _dir = "/workspace/projects/A股报告系统/reports"
            os.makedirs(_dir, exist_ok=True)
            _path = os.path.join(_dir, f"IPO周报_{_PERIOD_KEY}.md")
            with open(_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"  已保存: {_path}")
            print("\n" + "="*60)
            print(report)
            print("="*60)
            print(f"[TS] 第三步：推送...")
            err2 = wx(report)
            print("\n" + ("✅ 已推送" if err2 == 0 else f"❌ err={err2}"))
            # ── 发送成功后才标记，避免发送失败却仍去重 ──
            if err2 == 0:
                _mark_sent_for_period(_PERIOD_KEY)
                print(f"[去重] 已记录执行日期+周期: {NOW.strftime('%Y%m%d')}|{_PERIOD_KEY}")
    finally:
        _release_lock()
