#!/bin/bash
# 自动清理OpenClaw stale lock files
# 条件：锁文件 >30分钟 且 持有进程已死
find /Users/lyu/.openclaw/agents/main/sessions/ -name "*.lock" -mmin +30 2>/dev/null | while read f; do
    pid=$(cat "$f" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('pid',''))" 2>/dev/null)
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
        echo "[$(date)] Removing stale lock: $(basename $f) (pid=$pid, age=$(($(date +%s)-$(stat -f %m "$f")))s)"
        rm -f "$f"
    fi
done
