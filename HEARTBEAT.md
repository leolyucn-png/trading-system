# Heartbeat tasks
# These run on heartbeat polls to maintain memory and check on things.

## 📌 记忆维护（每2天一次）
1. 检查 memory/交易日志/ 最近5个交易日是否有空日志文件
2. 检查 MEMORY.md 是否需要更新持仓信息
3. 检查 memory/经验教训库.md 是否有未整合的教训

## 📈 持仓检查（交易日检查）
如果当前在交易时段（09:30-15:00），检查 memory/trades.md 中的持仓是否有风险信号

## 📋 尾盘执行提醒
如当前时间14:30-14:55且为交易日，提醒用户该执行尾盘操作了
