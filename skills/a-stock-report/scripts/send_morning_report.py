#!/usr/bin/env python3
"""晨报推送脚本 - 三步模式：
第一步（由LLM在cron prompt中完成）：搜索新闻 + 生成报告，写入 /tmp/morning_report_content.txt
第二步（Python）：读取文件 → 检查去重锁 → 保存MD → 推送（失败时发预警）
第三步（由LLM在cron prompt第四步中调用）：检查本脚本退出码，0=成功，非0=失败需预警
"""
from datetime import datetime, timezone, timedelta, timedelta as td
import sys, os, json, subprocess

# ── .env 自动加载（支持 cron 触发）────────────────────────
# 优先：脚本同目录 ../.env → 工作区根目录 .env
for _PATH in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env"),
]:
    if os.path.exists(_PATH):
        for line in open(_PATH):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

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

def _now(): return datetime.now(timezone(td(hours=8)))
TS = lambda: _now().strftime("%H:%M:%S")
_date_str = lambda: _now().strftime("%Y%m%d")
content_file = "/tmp/morning_report_content.txt"
_lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".morning_report_lock.json")

def read_lock():
    if os.path.exists(_lock_file):
        try:
            with open(_lock_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def write_lock(date_str, status):
    with open(_lock_file, 'w') as f:
        json.dump({'date': date_str, 'status': status, 'ts': _now().isoformat()}, f)

def notify_failure(msg: str):
    """推送失败时，通过 message 工具发预警通知"""
    alert = f"⚠️ 【晨报推送失败】\n{msg}\n\n请及时检查 cron 任务状态。"
    err = wx(alert)
    if err == 0:
        print(f"[{TS()}] 失败通知已发送")
    else:
        print(f"[{TS()}] 失败通知发送失败: err={err}")


if __name__ == "__main__":
    _today = _date_str()
    # ---------- 防重复推送：检查当日是否已推送 ----------
    lock = read_lock()
    if lock.get('date') == _today and lock.get('status') == 'ok':
        print(f"[{TS()}] ⏭ 已推送，跳过（date={_today}）")
        sys.exit(0)

    print(f"[{TS()}] 第一步：读取报告内容...")

    # ---------- 检查内容文件 ----------
    if not os.path.exists(content_file):
        msg = f"报告文件不存在: {content_file}"
        print(f"[{TS()}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)

    with open(content_file, encoding='utf-8') as f:
        report = f.read()

    if not report.strip():
        msg = "报告内容为空"
        print(f"[{TS()}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)

    # ---------- 保存 Markdown ----------
    print(f"[{TS()}] 第二步：保存Markdown报告...")
    _dir = "/workspace/projects/A股报告系统/reports"
    os.makedirs(_dir, exist_ok=True)
    _path = os.path.join(_dir, f"晨报_{_today}.md")
    with open(_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  已保存: {_path}")

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # ---------- 推送 ----------
    print(f"\n[{TS()}] 第三步：推送...")
    err = wx(report)
    if err == 0:
        write_lock(_today, 'ok')
        print(f"\n[{TS()}] ✅ 已推送")
        sys.exit(0)
    else:
        msg = f"webhook 返回错误: err={err}"
        print(f"\n[{TS()}] ❌ {msg}")
        notify_failure(msg)
        sys.exit(1)
