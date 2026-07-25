#!/bin/bash
# 龙虾·每日灾备快照
# 每晚23:00自动执行 | 写入 ~/Desktop/龙虾炒股/backup/

DATE=$(date +%F)
DEST="$HOME/Desktop/龙虾炒股/backup"
WS="$HOME/.openclaw/workspace"
MEM="$WS/memory"

mkdir -p "$DEST"

# 核心状态文件
cp "$WS/SESSION-STATE.md" "$DEST/STATE_$DATE.md" 2>/dev/null
cp "$MEM/trades.md" "$DEST/trades_$DATE.md" 2>/dev/null

# 当日日志
if [ -f "$MEM/$DATE.md" ]; then cp "$MEM/$DATE.md" "$DEST/log_$DATE.md"; fi

# 各账册
for f in "$MEM/纸面预选账.md" "$MEM/直觉组账.md" "$MEM/快枪组账.md" "$MEM/孵化箱账.md"; do
    base=$(basename "$f" .md)
    [ -f "$f" ] && cp "$f" "$DEST/${base}_$DATE.md"
done

echo "$(date '+%H:%M') 灾备快照完成 → $DEST"
ls -1 "$DEST"/ | grep "$DATE" | wc -l | xargs echo "  文件数:"
