#!/usr/bin/env python3
"""财经周末要闻推送脚本 - 支持从历史收盘小结提取情绪轨迹数据
第一步（LLM）：搜新闻 + 生成报告，写入 /tmp/weekend_news_content.txt
第二步（Python）：读取文件 → 保存MD → 打印
第三步（Python）：推送
"""
import sys, os, subprocess, json, re
from pathlib import Path
from datetime import datetime, timedelta, timezone

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

# ── 防重复运行锁 ─────────────────────────────────────────────
_LOCK_FILE = "/tmp/a_stock_weekend.lock"

def _acquire_lock():
    if os.path.exists(_LOCK_FILE):
        print(f"[LOCK] 已有实例在运行 ({_LOCK_FILE})，退出。")
        sys.exit(0)
    open(_LOCK_FILE, "w").close()

def _release_lock():
    if os.path.exists(_LOCK_FILE):
        os.remove(_LOCK_FILE)

def get_webhook_url():
    key = os.environ.get("WECOM_WEBHOOK_KEY", "")
    if not key:
        raise RuntimeError("WECOM_WEBHOOK_KEY environment variable not set")
    return f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key.strip()}"

def wx(text: str, max_retries: int = 2) -> int:
    """企业微信推送，curl 风格，带自动重试"""
    payload = json.dumps({"msgtype": "text", "text": {"content": text}}, ensure_ascii=False)
    for attempt in range(max_retries + 1):
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", get_webhook_url(),
             "-H", "Content-Type: application/json", "-d", "@-"],
            input=payload.encode("utf-8"), capture_output=True)
        try:
            errcode = json.loads(r.stdout.decode()).get("errcode", -1)
        except Exception:
            errcode = -1
        if errcode == 0:
            return 0
        if attempt < max_retries:
            print(f"[WX] 发送失败，errcode={errcode}，重试中...")
    return -1

_TZ = timezone(timedelta(hours=8))
TS = datetime.now(_TZ).strftime("%Y%m%d_%H%M")
content_file = '/tmp/weekend_news_content.txt'
REPORTS_DIR = Path("/workspace/projects/A股报告系统/reports")

def parse_evening_report(path: Path) -> dict:
    """从晚报MD文件提取情绪轨迹数据"""
    text = path.read_text(encoding='utf-8')
    data = {}

    # 北向资金：• 北向：净流入XX亿 / 净流出XX亿
    m = re.search(r'北向[：:].*?净([流出入]+)([0-9.]+)亿', text)
    if m:
        sign = 1 if m.group(1) == '流入' else -1
        data['north'] = sign * float(m.group(2))

    # 两融余额：• 两融余额（YYYY年MM月DD日）：XXXXX亿，较前日+/-XXXX亿
    m = re.search(r'两融余额[（(].*?(\d{4})年(\d{2})月(\d{2})日[)）][：:：]*([\d.]+)亿', text)
    if m:
        data['rz_bal'] = float(m.group(4))
        data['rz_bal_date'] = f"{m.group(1)}{m.group(2)}{m.group(3)}"

    # 两融余额/A股流通市值：• 两融余额/A股流通市值（YYYY年MM月DD日）= XXXXX亿 / XXXXXXX亿 = X.XX%
    m = re.search(r'两融余额/A股流通市值.*?[=＝]\s*[\d.]+亿\s*/\s*[\d.]+亿\s*=\s*([\d.]+)%', text)
    data['rz_mkt_ratio'] = float(m.group(1)) / 100 if m else None

    # 两融交易额/A股成交额：• 两融交易额/A股成交额（YYYY年MM月DD日）= XXXX亿 / XXXXX亿 = XX.X%
    m = re.search(r'两融交易额/A股成交额.*?[=＝]\s*[\d.]+亿\s*/\s*([\d.]+)亿\s*=\s*([\d.]+)%', text)
    if m:
        data['rz_ratio'] = float(m.group(2)) / 100  # 比值，已是%
        data['rz_turnover'] = float(m.group(1))      # 两融交易额

    # 涨停/跌停：• 涨停XX家 / • 跌停XX家
    m = re.search(r'涨停\s*(\d+)\s*家', text)
    data['zt'] = int(m.group(1)) if m else None
    m = re.search(r'跌停\s*(\d+)\s*家', text)
    data['dt'] = int(m.group(1)) if m else None

    # 综合打分：• 涨停XX家 → X分 ...
    m = re.search(r'综合[评]?[打]?分[：:：]*\s*(\d+)/100', text)
    data['sentiment'] = int(m.group(1)) if m else None

    # 日期：查找晚报里的日期（如"2026年04月13日"）
    m = re.search(r'(\d{4})年(\d{2})月(\d{2})日', text)
    if m:
        data['date'] = f"{m.group(1)}{m.group(2)}{m.group(3)}"

    return data


def parse_close_summary(path: Path) -> dict:
    """从收盘小结MD文件提取情绪轨迹数据"""
    text = path.read_text(encoding='utf-8')
    data = {}

    # 涨停/跌停家数
    m = re.search(r'涨停(\d+)家', text)
    data['zt'] = int(m.group(1)) if m else None
    m = re.search(r'跌停(\d+)家', text)
    data['dt'] = int(m.group(1)) if m else None

    # 北向资金
    m = re.search(r'北向[：:].*?([+-]?\d+\.?\d*)\s*亿', text)
    data['north'] = float(m.group(1)) if m else None

    # 炸板率
    m = re.search(r'炸板率([\d.]+)%', text)
    data['zbr'] = float(m.group(1)) if m else None

    # 综合评分
    m = re.search(r'综合评分[：:]?\s*(\d+|None)/100', text)
    data['sentiment'] = int(m.group(1)) if m and m.group(1) != 'None' else None

    # 沪深300涨跌幅
    m = re.search(r'沪深300[：:].*?([+-]?[\d.]+)%', text)
    data['hs300_pct'] = float(m.group(1)) if m else None

    # 两融余额
    m = re.search(r'融资余额.*?([\d.]+)亿', text)
    data['rz_bal'] = float(m.group(1)) if m else None

    # 成交额
    m = re.search(r'成交额[（(]?\d*月(\d+)日[)）]*[：:]*\s*([\d.]+)\s*万亿元', text)
    if m:
        data['turnover'] = float(m.group(3)) * 10000  # 万亿→亿
    else:
        m = re.search(r'成交额[：:]\s*([\d.]+)\s*万亿元', text)
        data['turnover'] = float(m.group(1)) * 10000 if m else None

    # 融资买入额 / 两融交易额（从收盘小结提取）
    # 两融比例 = 融资买入额 / 成交额
    m = re.search(r'两融比例[＝=].*?([\d.]+)%', text)
    data['rz_ratio'] = float(m.group(1)) / 100 if m else None

    # 日期：从文件名提取（如 收盘小结_20260522.md → 20260522），跳过 收盘小结_最新.md
    m = re.search(r'收盘小结_(\d{8})\.md$', str(path))
    if m:
        data['date'] = m.group(1)

    return data


def extract_weekly_data() -> dict:
    """从收盘小结和晚报提取过去一周的情绪轨迹数据"""
    # 收盘小结：取涨停/情绪打分，按文件名日期倒序，排除 _最新.md
    close_files = sorted(
        [f for f in REPORTS_DIR.glob("收盘小结_*.md")
         if re.search(r'收盘小结_\d{8}\.md$', f.name)],
        reverse=True
    )
    # 晚报：取北向/两融余额/两融比例
    evening_files = sorted(REPORTS_DIR.glob("晚报_*.md"), reverse=True)

    # 收盘小结数据
    close_data = {}
    for f in close_files:
        d = parse_close_summary(f)
        if 'date' in d:
            close_data[d['date']] = d

    # 晚报数据（补充北向/两融）
    evening_data = {}
    for f in evening_files:
        d = parse_evening_report(f)
        if 'date' in d:
            evening_data[d['date']] = d

# 合并：强制当前周（周一到最新数据日），缺失标注
    available = set(close_data.keys())
    if not available:
        return {}

    latest_date_str = max(available)
    latest_dt = datetime.strptime(latest_date_str, '%Y%m%d')
    # 当前自然周的周一
    current_week_monday = latest_dt - timedelta(days=latest_dt.weekday())

    result = {}
    # 生成当前周全部5天（周一~周五）
    all_week_dates = [(current_week_monday + timedelta(days=i)).strftime('%Y%m%d') for i in range(5)]

    for ds in all_week_dates:
        cd = close_data.get(ds, {})
        ed = next((e for e in evening_data.values()
                   if e.get('rz_bal_date') == ds), {})
        merged = {**cd}
        for k in ['north', 'rz_bal', 'rz_ratio', 'rz_turnover', 'rz_mkt_ratio', 'zt', 'sentiment']:
            if merged.get(k) is None and ed.get(k) is not None:
                merged[k] = ed[k]
        result[ds] = merged

    # 生成趋势文字：用实际星期几，缺失数据标注（未报）
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']
    sorted_dates = sorted(result.keys())  # 升序：周一→...→周五

    def _weekday_label(date_str):
        dt = datetime.strptime(date_str, '%Y%m%d')
        return f"周{weekday_names[dt.weekday()]}"

    def _zt(i, d):
        v = result.get(d, {}).get('zt')
        return f"{_weekday_label(d)}{v if v is not None else '？'}家"

    def _north(i, d):
        v = result.get(d, {}).get('north')
        label = _weekday_label(d)
        if v is None: return f"{label}（未报）"
        return f"{label}{'+' if v >= 0 else ''}{v:.1f}亿"

    def _rz_ratio(i, d):
        v = result.get(d, {}).get('rz_ratio')
        label = _weekday_label(d)
        if v is None: return f"{label}（未报）"
        return f"{label}{v*100:.1f}%"

    def _rz_mkt(i, d):
        v = result.get(d, {}).get('rz_mkt_ratio')
        label = _weekday_label(d)
        if v is None: return f"{label}（未报）"
        return f"{label}{v*100:.2f}%"

    def _sent(i, d):
        v = result.get(d, {}).get('sentiment')
        label = _weekday_label(d)
        return f"{label}{v if v is not None else '？'}分"

    return {
        'zt_line': " → ".join([_zt(i, d) for i, d in enumerate(sorted_dates)]),
        'north_line': " → ".join([_north(i, d) for i, d in enumerate(sorted_dates)]),
        'rz_ratio_line': " → ".join([_rz_ratio(i, d) for i, d in enumerate(sorted_dates)]),
        'rz_mkt_line': " → ".join([_rz_mkt(i, d) for i, d in enumerate(sorted_dates)]),
        'sent_line': " → ".join([_sent(i, d) for i, d in enumerate(sorted_dates)]),
        'files_found': sorted_dates,
        'close_files': [str(f) for f in close_files],
        'evening_files': [str(f) for f in evening_files],
    }


if __name__ == "__main__":
    _acquire_lock()
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--extract-only', action='store_true')
        args = parser.parse_args()

        if args.extract_only:
            # 独立运行：只提取数据，写入JSON，然后退出
            wk = extract_weekly_data()
            json_path = Path('/tmp/weekend_emotion_data.json')
            json_path.write_text(json.dumps(wk, ensure_ascii=False, indent=2))
            print(f"[{TS}] 情绪轨迹数据已写入 {json_path}")
            print(f"  涨停趋势：{wk.get('zt_line','?')}")
            print(f"  北向趋势：{wk.get('north_line','?')}")
            print(f"  两融比例：{wk.get('rz_ratio_line','?')}")
            print(f"  两融/市值：{wk.get('rz_mkt_line','?')}")
            print(f"  情绪打分：{wk.get('sent_line','?')}")
            sys.exit(0)

        print(f"[{TS}] 第二步：读取报告内容...")
        if not os.path.exists(content_file):
            print(f"[{TS}] ❌ {content_file} 不存在，请先由LLM生成报告内容")
            sys.exit(1)

        with open(content_file, encoding='utf-8') as f:
            report = f.read()

        if not report.strip():
            print(f"[{TS}] ❌ 报告内容为空")
            sys.exit(1)

        # ── 修正标题日期（周末区间：上周六 → 本周日）───────────
        sat = (datetime.now(_TZ) - timedelta(days=1)).strftime("%Y年%m月%d日")
        sun = datetime.now(_TZ).strftime("%Y年%m月%d日")
        _correct_title = f"📰 【财经周末要闻】{sat} - {sun}"
        if re.match(r'^📰 【财经周末要闻】', report):
            report = re.sub(r'^📰 【财经周末要闻】.*', _correct_title, report, count=1, flags=re.MULTILINE)

        # 提取历史情绪轨迹数据
        print(f"[{TS}] 提取历史情绪轨迹数据...")
        wk = extract_weekly_data()
        for k, v in wk.items():
            print(f"  {k}: {v}")

        print(f"[{TS}] 第三步：保存Markdown报告...")
        os.makedirs(REPORTS_DIR, exist_ok=True)
        _date_str = datetime.now(_TZ).strftime("%Y%m%d")
        _path = REPORTS_DIR / f"财经周末要闻_{_date_str}.md"
        with open(_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  已保存: {_path}")

        print("\n" + "="*60)
        print(report)
        print("="*60)

        print(f"\n[{TS}] 第四步：推送...")
        errcode = wx(report)
        print("\n" + ("✅ 已推送" if errcode == 0 else f"❌ err={errcode}"))
    finally:
        _release_lock()