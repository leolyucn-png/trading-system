#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盘中预警脚本
触发条件：任一主要股指涨跌幅超 ±2%
去重：每指数每档位每天只推送一次
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
# ── 环境变量 Webhook ─────────────────────────────────────
import os, json, subprocess
from datetime import datetime, timezone, timedelta
from datetime import date as _date

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

def get_webhook_url() -> str:
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

_TZ_OFFSET = timedelta(hours=8)
def now_bj(): return datetime.now(timezone.utc) + _TZ_OFFSET
def ts(): return (datetime.now(timezone.utc) + _TZ_OFFSET).strftime("%Y-%m-%d %H:%M")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
def already_sent(f):
    t = now_bj().strftime("%Y%m%d")
    p = os.path.join(_SCRIPT_DIR, f)
    return os.path.exists(p) and open(p).read().strip() == t
def mark_sent(f):
    with open(os.path.join(_SCRIPT_DIR, f), "w") as fp:
        fp.write(now_bj().strftime("%Y%m%d"))

_TRADE_CACHE = {}
def _get_trade_dates(year: int):
    import time as _t, akshare as _ak
    key = (year,)
    now = _t.time()
    cached, _ts = _TRADE_CACHE.get(key, (None, 0))
    if cached and (now - _ts) < 86400: return cached
    try:
        df = _ak.tool_trade_date_hist_sina()
        dates = set(pd.to_datetime(df['trade_date']).dt.date)
        _TRADE_CACHE[key] = (dates, now)
        return dates
    except: return cached or set()

def is_trading_window():
    bj = now_bj()
    if bj.weekday() >= 5: return False
    today = bj.date()
    td_ = _get_trade_dates(today.year)
    if td_ and today not in td_: return False
    h, m = bj.hour, bj.minute
    return ((h == 9 and m >= 30) or (h == 10) or (h == 11 and m <= 29) or (13 <= h < 15))

# 六大指数配置（名称 → 腾讯代码）
INDICES = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "科创50": "sh000688",
    "沪深300": "sh000300",
    "中证500": "sh000905",
}

ALERT_THRESHOLD = 2.0   # 触发阈值（%）
STATE_FILE = "/workspace/.alert_sent"

def get_index_data():
    """从腾讯财经获取六大指数实时数据"""
    try:
        import requests as _req
        codes = ",".join(INDICES.values())
        url = f"https://qt.gtimg.cn/q={codes}"
        r = _req.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        raw = r.content.decode("gbk", errors="replace")
        lines = raw.strip().split("\n")
        result = {}
        for line in lines:
            if not line.strip():
                continue
            content = line.lstrip("v_")
            parts = content.split("~")
            if len(parts) < 35:
                continue
            code = parts[2].strip().lstrip("sh").lstrip("sz")
            name = parts[1].strip()
            price = float(parts[3]) if parts[3] else 0
            prev_close = float(parts[4]) if parts[4] else price
            change_pct = float(parts[32]) if parts[32] else 0
            high = float(parts[33]) if parts[33] else 0
            low = float(parts[34]) if parts[34] else 0
            result[code] = {
                "name": name,
                "price": price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "change_pct": change_pct,
            }
        return result
    except Exception as e:
        print(f"获取指数数据失败: {e}")
        return {}

def get_threshold_bucket(pct: float) -> int:
    """将涨跌幅映射到档位（0=0-0.5%, 1=0.5-1%, 2=1-1.5%, 3=1.5-2%, 4=2%+）"""
    pct = abs(pct)
    if pct < 0.5:
        return 0
    elif pct < 1.0:
        return 1
    elif pct < 1.5:
        return 2
    elif pct < 2.0:
        return 3
    else:
        return 4

def get_state_file_for_index(idx_code: str) -> str:
    """每个指数有独立状态文件"""
    today = now_bj().strftime("%Y%m%d")
    return f"/workspace/.alert_{idx_code}_{today}.state"

def already_alerted(idx_code: str, bucket: int) -> bool:
    state_file = get_state_file_for_index(idx_code)
    if not os.path.exists(state_file):
        return False
    sent_buckets = set()
    try:
        with open(state_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    sent_buckets.add(int(line))
    except:
        pass
    return bucket in sent_buckets

def mark_alerted(idx_code: str, bucket: int):
    state_file = get_state_file_for_index(idx_code)
    try:
        with open(state_file, "a") as f:
            f.write(f"{bucket}\n")
    except:
        pass

def build_alert_text(idx_info: dict) -> str:
    name = idx_info["name"]
    price = idx_info["price"]
    pct = idx_info["change_pct"]
    high = idx_info["high"]
    low = idx_info["low"]
    direction = "🔺暴涨" if pct > 0 else "🔴暴跌"
    arrow = "▲" if pct > 0 else "▼"
    now_ts = ts()
    return (
        f"🚨 【{direction}预警】{name} | 北京时间 {now_ts}\n\n"
        f"• 最新点位：{price:.2f}（{arrow}{abs(pct):.2f}%）\n"
        f"• 最高/最低：{high:.2f} / {low:.2f}\n"
        f"⚠️ 请关注后续走势，做好风险管理。"
    )

def main():
    if not is_trading_window():
        print("非交易时段，不检查预警")
        return

    print(f"[{ts()}] 检查盘中预警...")
    data = get_index_data()
    if not data:
        return

    pushed = False
    for name, code in INDICES.items():
        code_un = code.lstrip("sh").lstrip("sz")  # 统一去掉sh/sz前缀，与data key一致
        if code_un not in data:
            continue
        info = data[code_un]
        pct = info["change_pct"]
        abs_pct = abs(pct)
        if abs_pct < ALERT_THRESHOLD:
            continue
        bucket = get_threshold_bucket(pct)
        if already_alerted(code_un, bucket):
            print(f"  {name}: {pct:+.2f}%，已推送过，跳过")
            continue
        text = build_alert_text(info)
        err = wx(text)
        if err == 0:
            mark_alerted(code_un, bucket)
            print(f"  ✅ {name}: {pct:+.2f}%，已推送")
        else:
            print(f"  ❌ {name}: 推送失败，errcode={err}")

# ── 防重复运行锁 ─────────────────────────────────────────────
_LOCK_FILE = "/tmp/a_stock_intraday.lock"

def _acquire_lock():
    if os.path.exists(_LOCK_FILE):
        mtime = os.path.getmtime(_LOCK_FILE)
        lock_date = datetime.fromtimestamp(mtime, timezone.utc + _TZ_OFFSET).date()
        today = _date.today()
        if lock_date < today:
            print(f"[LOCK] 过期锁（{lock_date}，今日{today}），清理后继续。")
            os.remove(_LOCK_FILE)
        else:
            print(f"[LOCK] 已有实例在运行 ({_LOCK_FILE})，退出。")
            sys.exit(0)
    open(_LOCK_FILE, "w").close()

def _release_lock():
    if os.path.exists(_LOCK_FILE):
        os.remove(_LOCK_FILE)

if __name__ == "__main__":
    _acquire_lock()
    try:
        main()
    finally:
        _release_lock()