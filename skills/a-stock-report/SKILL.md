---
name: a-stock-report
description: "A股数据驱动型报告自动生成与推送系统，支持晨报 / 收盘小结 / 晚报 / 盘中预警 / IPO周报 / 财经周末要闻。内置投资者情绪打分（6维度，满分100）与AI后市展望。"
version: 1.10.3
---

# A股报告系统

> A股数据驱动型报告自动生成与推送系统，支持晨报 / 收盘小结 / 晚报 / 盘中预警 / IPO周报 / 财经周末要闻

---

## 快速开始

## 安全配置（必读）

所有外部密钥均通过环境变量注入，**禁止硬编码**。密钥文件 `/workspace/.env` 由脚本自动加载（环境变量优先）。

| 密钥 | 环境变量 | 最小权限 | 来源 |
|------|---------|---------|------|
| 企业微信 Webhook | `WECOM_WEBHOOK_KEY` | 仅发送（只写） | 微信企业版 → 应用 → Webhook |
| 同花顺问财 API Key | `IWENCAI_API_KEY` | 只读查询 | 同花顺 i问财 SkillHub |
| 妙想 API Key | `MX_APIKEY` | 只读查询 | 同花顺 i问财 |

`.env` 文件格式示例：
```bash
WECOM_WEBHOOK_KEY=c4a1cd60-254e-4612-b365-c701482ae98c
IWENCAI_API_KEY=...
MX_APIKEY=...
TUSHARE_TOKEN=...
```

---

## 快速开始

```bash
# 收盘小结（独立脚本，直接推送，无需LLM生成内容）
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py --date 2026-04-13

# 晚报
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_evening_report.py

# 晨报（需LLM先生成内容，写入 /tmp/morning_report_content.txt）
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_morning_report.py

# 财经周末要闻（需LLM先生成内容，写入 /tmp/weekend_news_content.txt）
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_weekend_news.py
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_weekend_news.py --extract-only  # 仅提取情绪数据

# IPO周报
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_ipo_report.py

# 盘中预警
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_intraday_alert.py
```

---

## 执行模式

**收盘小结、晚报、晨报** 采用不同模式：

- **收盘小结**：单一 Python 脚本，内置全部逻辑（取数 → 打分 → 生成报告 → 推送），cron 直接触发，无需 LLM 生成内容。
- **晚报**：两步（LLM 生成内容 → 脚本落地 + 推送），cron prompt 控制。
- **晨报**：两步（LLM 生成内容 → 脚本落地 + 推送），cron prompt 控制。

---

## 数据来源

| 数据 | 来源 | 接口 |
|------|------|------|
| 六大指数（点位/涨跌幅） | 腾讯实时 API | `qt.gtimg.cn` |
| 全市场成交额 | 同花顺问财 | `A股总成交额` |
| 全市场流通市值 | 同花顺问财 | `A股总流通市值` |
| 涨跌停家数/炸板率 | 同花顺问财 | `今日涨停家数 跌停家数 炸板家数`（1次查询） |
| 全市场主力净流入 | 东方财富 RPT_MARKET_CAPITALFLOW | INDEX_CODE="800000.EI"，SORT BY TRADE_DATE DESC 取第1行，BONDTYPE="A股" |
| 行业板块涨跌（前5/后5） | hithink-sector-selector | `今日行业板块涨幅前10` / `今日行业板块跌幅前10` |
| 行业主力资金流 Top | hithink-sector-selector | `近5日主力净流入前10行业板块` |
| 两融余额/两融交易额 | AKShare | `macro_china_market_margin_sh/sz`（仅晚报使用） |
| IF期货基差 | 新浪 nf_IF0 实时接口（今日优先）+ AKShare 兜底 | hq.sinajs.cn / akshare futures_main_sina |

---

## 文件名日期规则

| 报告 | 文件名日期取值 |
|------|--------------|
| 收盘小结 | `--date` 参数值；无参数则取当天 |
| 晚报 | `--date` 参数值；无参数则取当天 |
| 晨报 | 生成当天 |
| 财经周末要闻 | 生成当天 |

> **注意**：晚报内容里的两融余额标注日期（如"两融余额（04月13日）"）是数据对应的上一交易日，与文件名日期可能差1天。

---

## 周末要闻情绪轨迹数据来源

一周情绪轨迹从历史报告MD文件中提取，合并规则：

| 指标 | 来源 | key取法 |
|------|------|--------|
| 涨停家数/情绪打分 | 收盘小结 `收盘小结_YYYYMMDD.md` | 从文件名提取 `YYYYMMDD` |
| 两融余额/两融比例 | 晚报 `晚报_YYYYMMDD.md` | 从**报告内容**里两融余额行提取日期作为 key |

两套数据以交易日 key 对齐合并，保证周一到周五趋势线一致。

---

## 防并发锁

各脚本使用独立的锁文件，同时运行互不干扰：

| 脚本 | 锁文件 |
|------|--------|
| `send_close_summary.py` | `/tmp/a_stock_close_summary.lock` |
| `send_evening_report.py` | `/tmp/a_stock_evening.lock` |
| `send_morning_report.py` | `/tmp/a_stock_morning.lock` |
| `send_weekend_news.py` | `/tmp/a_stock_weekend.lock` |
| `send_ipo_report.py` | `/tmp/a_stock_ipo.lock` |
| `send_intraday_alert.py` | `/tmp/a_stock_intraday.lock` |

---

## 报告模板

### 晨报

```
📰 【股市晨报】YYYY年MM月DD日（周X）

━━━ 隔夜全球市场 ━━━
【美股收盘】
▪ 道琼斯：XXXXX.XX点，+X.XX%（精确数字，不得用"约"）
▪ 标普500：XXXXX.XX点，+X.XX%
▪ 纳斯达克：XXXXX.XX点，+X.XX%（可附"X连涨/连跌X日"）
▪ VIX恐慌指数：XX.XX（+X.XX%），恐慌等级：【低位(<20)/中位(20-30)/高位(>30)】

【港股及A50】
▪ 恒生指数：XXXXX.XX点，+X.XX%（附简要背景）
▪ 富时A50期货：XXXXX点，+X.XX%，偏强/偏弱运行【预判A股明日开盘】

【大宗商品】
▪ WTI原油：XXX.XX美元/桶，+X.XX%（精确数字，不得用"约"）
▪ 现货黄金：XXXX.XX美元/盎司，+X.XX%（精确数字）

━━━ 财经要闻 ━━━
【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：（简洁分析，≤50字）
【2】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：（≤50字）
（**≤7条**，顺序编号，每条格式固定：
  【编号】（标题）｜✅/❌/⚠️标签 对A股影响
  点评：（事件+分析，≤50字））

━━━ 今日操作建议 ━━━
【大盘研判】
（综合外围市场、宏观政策、量能等因素，给出2-3句综合判断）

【操作建议】
1. 【板块/策略】（期限）：具体建议+附标的
2. 【板块/策略】（期限）：...

【风险提示】
⚠️ （1-3条，最重要的风险）

⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 收盘小结

```
📊 【A股收盘小结】YYYY年MM月DD日

━━━ 一，主要股指表现 ━━━
• 上证指数：XXXX.XX，↑/↓X.XX%
• 深证成指：XXXX.XX，↑/↓X.XX%
• 创业板指：XXXX.XX，↑/↓X.XX%
• 科创50：XXXX.XX，↑/↓X.XX%
• 沪深300：XXXX.XX，↑/↓X.XX%
• 中证500：XXXX.XX，↑/↓X.XX%
全市场成交额：XXXXX亿
IF期货信号：IF=XXXX.X，基差+/-XX.X点（升水/贴水）

━━━ 二，板块行情 ━━━
  🔺 涨幅前5：
    · 板块名+X.XX%
    · ...
  🟢 跌幅前5：
    · 板块名-X.XX%
    · ...

━━━ 三，全市场主力资金 ━━━
  🔴/🟢 全市场主力资金：+/-XXX.XX亿元（净流入/净流出）

━━━ 四，行业主力资金流 ━━━
  近5日净流入板块 TOP5：
    · 板块名 +/-XXX.XX亿(+/-X.XX%)
    · ...
  近5日净流出板块 TOP3：
    · 板块名 +/-XXX.XX亿

━━━ 五，量化情绪打分 ━━━（满分100，6因子等权平均）
· 涨停家数 → X分（区间10~100家映射）
· 涨跌停比：XX倍 → X分（对数插值）
· 炸板率 → X分（区间40%~10%映射，越低越好）
• 主力净流入占比：X.XX% → X分（区间-5%~+5%映射）
• 全市场换手率：X.XX% → X分（区间1%~4%映射）
• IF基差：+/-XX.XX点 → X分（区间-300~+150点映射）
━━━━━━━━━━━
综合评分：XX/100  🟢做多｜🟡偏多｜⚪分歧｜🟠偏空谨慎｜🔴冰点

━━━ 六，后市展望 ━━━
市场震荡调整，风格偏向题材与成长，建议控制仓位、关注轮动节奏。

━━━ 数据来源：腾讯财经·东方财富·同花顺 ━━━
⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 晚报

```
📋 【A股晚报】YYYY年MM月DD日

━━━ A股收盘 ━━━
• 上证指数：XXXX.X，↑/↓X.XX%
• 深证成指：XXXX.X，↑/↓X.XX%
• 创业板指：XXXX.X，↑/↓X.XX%
• 科创50：XXXX.X，↑/↓X.XX%
• 沪深300：XXXX.X，↑/↓X.XX%
• 中证500：XXXX.X，↑/↓X.XX%
• 成交额：X.XX万亿元

━━━ 亚太股市 ━━━
• 恒生指数：XXXX，↑/↓X.XX%
• 日经225：XXXXX，↑/↓X.XX%
• 韩国综合：XXXX，↑/↓X.XX%

━━━ 市场风险偏好 ━━━
• 两融余额（MM月DD日）：XXXXX亿，较前日+/-XXXX亿
• 两融余额/A股流通市值（MM月DD日）= X.XX%
  阈值：<3%安全 | 3-3.5%预警 | ≥3.5%高危
• 两融交易额/A股成交额（MM月DD日）= X.X%
  阈值：<7%保守 | 7-11%中性 | >11%过热
• 股市风险溢价（MM月DD日）= X.XX%
  阈值：<3%高估 | 3-6%中性 |>6%低估
• 沪深300 PE = XX.XX，近5年分位点 XX.X%

━━━ 财经要闻 ━━━
【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响
  点评：（≤50字）
【2】...（**≤7条**，每条格式固定，点评≤50字）

━━━ 今日操作建议 ━━━
【大盘研判】（2-3句）
【操作建议】
1. 【板块/策略】（期限）：具体建议
2. 【板块/策略】（期限）：...
【风险提示】（1-3条）

⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。
```

### 财经周末要闻（cron 触发后 LLM 生成）

```
📰 【财经周末要闻】过去48小时

━━━ 六条重要财经要闻 ━━━
【1】（标题）→ ✅利好/❌利空
  逻辑：...  交易风险提示：...

━━━ 一周情绪轨迹 ━━━
• 涨停家数趋势：周一X家 → 周二X家 → ... → 周五X家
• 两融余额/A股流通市值：周一X.XX% → ... → 周五X.XX%
• 两融交易额占比：周一X.X% → ... → 周五X.X%
• 量化情绪打分：周一XX分 → ... → 周五XX分
• 整体趋势：[升温/降温/震荡]

━━━ 整体市场情绪研判 ━━━
情绪指标总结 | 核心驱动因素 | 当前风险点 | 下周操作参考

⚠️ 仅供参考，不构成投资建议。
```

---

## 定时任务（cron）

| 任务 | cron 表达式 | 触发时间（北京时间） | 说明 |
|------|-----------|-------------------|------|
| A股晨报生成并推送 | `0 0 * * 1-5` | 周一至五 08:00 | AI内容生成 → 推送（单cron） |
| A股晚报生成并推送 | `0 12 * * 1-5` | 周一至五 20:00 | AI内容生成 → 推送（单cron） |
| A股收盘小结 | `30 7 * * 1-5` | 周一至五 15:30 | 数据采集 → 推送 |
| A股盘中预警 | `*/5 9-11,13-14 * * 1-5` | 周一至五交易时段 | 实时监控 → 推送 |
| A股周末要闻生成并推送 | `0 12 * * 0` | 周日 20:00 | AI内容生成 → 推送（单cron） |
| 每周 Skill 复盘 | `0 10 * * 0` | 周日 10:00 | skill 自审 |
| A股IPO周报 | `0 2 * * 6` | 周六 10:00 | 数据采集 → 推送 |

> **盘中预警触发时段**：严格对应 A 股实盘集合竞价规则（9:15-9:25 开盘，11:30-12:59 休市，15:00 收盘）。脚本通过 `is_trading_window()` 函数判断，仅在 9:30-11:29 与 13:00-14:59 内触发。

### 盘中预警触发时段

安装 skill 后，按以下顺序逐一确认：

### Step 1：密钥检查

| 报告类型 | 必需密钥 | 最低权限 | 检查命令 |
|---------|---------|---------|---------|
| 收盘小结 | `WECOM_WEBHOOK_KEY` | 仅发送 | `grep WECOM_WEBHOOK_KEY /workspace/.env` |
| 晚报 | `WECOM_WEBHOOK_KEY` + `IWENCAI_API_KEY` | 发送+查询 | 同上 + `grep IWENCAI_API_KEY /workspace/.env` |
| 晨报 | 同晚报 | 同上 | 同上 |
| 财经周末要闻 | 同晚报 | 同上 | 同上 |
| IPO周报 | `TUSHARE_TOKEN` + `WECOM_WEBHOOK_KEY` | 查询+发送 | `grep TUSHARE_TOKEN /workspace/.env` |
| 盘中预警 | 无外部依赖 | — | 无需检查 |

> **注意**：`send_evening_report.py` 的"财经要闻"和"明日操作建议"两个区块**依赖 cron 中的 LLM 步骤生成**，不是脚本自己能产出的。若未配置对应 cron task，这两个区块**永远为空**，这是设计预期，不是 bug。

### Step 2：依赖检查

```bash
# 检查 akshare
python3 -c "import akshare; print('akshare', akshare.__version__)"

# 检查 tushare（IPO周报需要）
python3 -c "import tushare; print('tushare OK')"

# 检查 hithink-sector-selector CLI
python3 /workspace/skills/hithink-sector-selector/scripts/cli.py --help | head -3
```

### Step 3：Cron 任务检查

运行 `mcp_cronjob list` 确认已配置的 cron 与计划运行的任务一致：

| 应存在 | 当前状态 |
|--------|---------|
| A股晨报生成并推送（08:00） | ✅ |
| A股晚报生成并推送（20:00） | ✅ |
| A股收盘小结（15:30） | ✅ |
| A股盘中预警（交易时段） | ✅ |
| A股周末要闻生成并推送（周日 20:00） | ✅ |
| 每周 Skill 复盘（周日 10:00） | ✅ |
| A股IPO周报（周六 10:00） | ✅ |

---

## Cron 任务配置指引

所有 LLM 驱动型报告采用**单 cron 模式**：prompt 中先由 LLM 生成内容写入文件，再在同一 session 内调用脚本落地推送。

> **为什么用文件中转？** cron prompt 在独立 session 运行，无法直接将变量传给后续脚本。通过写入约定路径的文件，脚本读取后注入报告模板，实现解耦。

### 1. 晨报（周一至五 08:00 北京时间）

```json
{
  "name": "A股晨报生成并推送",
  "schedule": "0 0 * * 1-5",
  "repeat": "forever",
  "deliver": "local",
  "skills": ["A-stock-report"],
"prompt": "请加载 A-stock-report skill，然后执行以下任务：\n\n1. 用 batch_web_search 搜索以下内容，获取**精确数字**：\n   - \"美股收盘 道琼斯 纳斯达克 标普500 VIX [前一日日期]\"（四位数点位+精确涨跌幅%，VIX精确数值）\n   - \"恒生指数 富时A50期货 [前一日日期]夜盘\"（精确点位+精确涨跌幅）\n   - \"WTI原油 现货黄金 [前一日日期]\"（精确美元价格+精确涨跌幅）\n   - \"A股重要财经要闻 宏观政策 [今日日期]\"（6-10条要闻）\n\n   **⚠️ 关键要求：搜索结果必须包含具体数字，所有数据不得出现\"约\"、\"约XX\"、\"约XX%\"等模糊表述，必须填入精确值。如搜索结果确实无法获取精确数据，明确标注数据来源（如\"富时A50期货（夜盘收）\"），并估算精确到小数点后2位的数值，不得用\"约\"字敷衍。**\n\n2. 严格按以下模板格式生成内容，**不得省略任何符号或改变顺序**，写入 /tmp/morning_report_content.txt：\n【格式模板——标题第一行必须写今日实际日期，格式为\"YYYY年M月D日（周X）\"】\n\n📰 【股市晨报】[今日实际日期]\n\n━━━ 隔夜全球市场 ━━━\n【美股收盘】\n▪ 道琼斯：XXXXX.XX点，+X.XX%（精确数字，不得用\"约\"）\n▪ 标普500：XXXXX.XX点，+X.XX%\n▪ 纳斯达克：XXXXX.XX点，+X.XX%（可附\"X连涨/连跌X日\"）\n▪ VIX恐慌指数：XX.XX（+X.XX%），恐慌等级：【低位(<20)/中位(20-30)/高位(>30)】\n\n【港股及A50】\n▪ 恒生指数：XXXXX.XX点，+X.XX%（附简要背景）\n▪ 富时A50期货：XXXXX点，+X.XX%，偏强/偏弱运行【预判A股明日开盘】\n\n【大宗商品】\n▪ WTI原油：XXX.XX美元/桶，+X.XX%（精确数字，不得用\"约\"）\n▪ 现货黄金：XXXX.XX美元/盎司，+X.XX%（精确数字）\n\n━━━ 财经要闻 ━━━\n【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响\n  点评：（2-3句，分析事件对A股情绪/板块的影响）\n【2】（标题）｜✅利好/❌利空/⚠️中性 对A股影响\n  点评：...\n（6-10条，顺序编号，每条格式固定：\n  【编号】（标题）｜✅/❌/⚠️标签 对A股影响\n  点评：（2-3句，事件+分析））\n\n━━━ 今日操作建议 ━━━\n【大盘研判】（综合外围市场、宏观政策、量能等因素，给出2-3句综合判断）\n\n【操作建议】\n1. 【板块/策略】（期限）：具体建议+附标的\n2. 【板块/策略】（期限）：...\n\n【风险提示】\n⚠️ （1-3条，最重要的风险）\n\n⚠️ 仅供参考，不构成投资建议。股市有风险，投资需谨慎。\n\n3. 调用晨报推送脚本：source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_morning_report.py\n4. 完成后打印\"✅ 晨报已完成：内容生成并推送微信\""
```

### 2. 晚报（周一至五 20:00 北京时间，12:00 UTC）

```json
{
  "name": "A股晚报生成并推送",
  "schedule": "0 12 * * 1-5",
  "repeat": "forever",
  "deliver": "local",
  "skills": ["A-stock-report"],
  "prompt": "请加载 A-stock-report skill，然后执行以下任务：\\n\\n1. 用 batch_web_search 搜索\"今日A股重大财经要闻\"获取5-7条重要财经新闻；\\n2. 搜索\"A股市场展望 操作建议 今日\"获取机构观点；\\n3. 严格按以下格式生成内容，**不得省略任何符号或改变格式**；\\n**重要约束：财经要闻最多7条，每条点评不超过50字，全文总字符数控制在3500字以内**，写入 /tmp/evening_report_ai.txt：\\n\\n【格式模板——严格按此输出，两段之间以 [财经要闻] 和 [操作建议] 标记分隔】\\n\\n[财经要闻]\\n━━━ 财经要闻 ━━━\\n【1】（标题）｜✅利好/❌利空/⚠️中性 对A股影响\\n  点评：（简洁分析，≤50字）\\n【2】（标题）｜✅利好/❌利空/⚠️中性 对A股影响\\n  点评：（≤50字）\\n（**≤7条**，顺序编号【1】【2】【3】...，每条格式固定：\\n  【编号】（标题）｜✅/❌/⚠️标签 对A股影响\\n  点评：（事件+分析，≤50字））\\n\\n[操作建议]\\n━━━ 今日操作建议 ━━━\\n【大盘研判】（综合外围市场、宏观政策、量能等因素，给出2-3句综合判断）\\n\\n【操作建议】\\n1. 【板块/策略】（期限）：具体建议+附标的\\n2. 【板块/策略】（期限）：...\\n\\n【风险提示】\\n⚠️ （1-3条，最重要的风险）\\n\\n4. 调用晚报推送脚本：source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_evening_report.py\\n5. 完成后打印\"✅ 晚报已完成：内容生成并推送微信\""
}
```

### 3. 收盘小结（周一至五 15:30 北京时间，无需LLM内容）

```json
{
  "name": "A股收盘小结推送",
  "schedule": "30 7 * * 1-5",
  "repeat": "forever",
  "deliver": "local",
  "prompt": "source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py"
}
```

### 4. 盘中预警（周一至五 9:30-11:29 / 13:00-14:59，每5分钟）

```json
{
  "name": "A股盘中预警",
  "schedule": "*/5 9-11,13-14 * * 1-5",
  "repeat": "forever",
  "deliver": "local",
  "skills": ["A-stock-report"],
  "prompt": "请加载 A-stock-report skill，然后执行以下任务：\\n\\n1. 读取 `/workspace/skills/A-stock-report/scripts/send_intraday_alert.py` 中的脚本内容；\\n2. 读取 `/workspace/.env` 中的 `WECOM_WEBHOOK_KEY` 环境变量；\\n3. 调用脚本：source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_intraday_alert.py；\\n4. 若脚本成功执行且推送了预警消息，打印\\"✅ 盘中预警检查完成\\"；若未触发预警，打印\\"✅ 盘中预警检查完成，当前无异常\\""
}
```

### 5. 财经周末要闻（周日 20:00 北京时间）

```json
{
  "name": "A股周末要闻生成并推送",
  "schedule": "0 12 * * 0",
  "repeat": "forever",
  "deliver": "local",
  "skills": ["A-stock-report"],
  "prompt": "请加载 A-stock-report skill，然后执行以下任务：\\n\\n1. 用 batch_web_search 搜索【上周六至本周日 A股重要财经要闻 宏观政策】（**只搜周末两天——上周六00:00至本周日当前时间的重大财经要闻**，6-8条）；\\n   **每条新闻必须标注具体日期（如：5月23日、5月24日），不得遗漏**\\n   **⚠️ 注意：重点关注周六和周日发布的最新财经要闻，同时兼顾周五收盘后至周日的宏观政策动态**\\n2. 读取 /workspace/projects/A股报告系统/reports/ 目录下最近5个交易日的收盘小结文件，提取情绪打分和涨停家数；\\n3. 参考 SKILL.md 周末要闻模板，生成：\\n   - 六条重要财经要闻（每条含标题+✅/❌标签+逻辑+风险提示）\\n   - 一周情绪轨迹（从历史报告提取数据）\\n   - 整体市场情绪研判\\n4. 将生成内容写入 /tmp/weekend_news_content.txt\\n5. 调用周末要闻推送脚本：source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_weekend_news.py\\n6. 完成后打印\\"✅ 周末要闻已完成：内容生成并推送微信\\""
}
```

### 6. A股IPO周报（周六 10:00 北京时间）

```json
{
  "name": "A股IPO周报",
  "schedule": "0 2 * * 6",
  "repeat": "forever",
  "deliver": "local",
  "prompt": "source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_ipo_report.py"
}
```

> **每周 Skill 复盘** 任务不属于 A-stock-report，由独立的 `skill-reviewer` skill 负责，配置见 skill-reviewer 的 SKILL.md。

---

## 验证步骤

配置完 cron 后，按以下顺序验证：

### 验证 1：单独运行脚本（数据层）

```bash
# 收盘小结（纯数据，无需 LLM 内容文件）
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_close_summary.py

# 晚报（若无 LLM 内容文件，财经要闻和操作建议区块为空，属正常）
source /workspace/.env && python3 /workspace/skills/A-stock-report/scripts/send_evening_report.py
```

检查推送消息中的数据是否正确（指数点位、两融数据、涨停家数等）。

### 验证 2：模拟 LLM 内容生成（LLM 层）

在 Agent 会话中手动执行 LLM prompt，确认内容文件能正确生成：

```bash
# 验证文件路径
ls -la /tmp/morning_report_content.txt    # 晨报内容
ls -la /tmp/evening_report_ai.txt         # 晚报内容
ls -la /tmp/weekend_news_content.txt       # 周末要闻内容
```

内容文件格式应严格遵循 SKILL.md 中对应模板的 `[财经要闻]` / `[操作建议]` 分段标记。

### 验证 3：端到端 cron 验证

实际 cron 跑过后，检查：
1. 推送消息中"财经要闻"和"明日操作建议"区块是否有内容
2. 内容日期是否与当天日期一致
3. 报告文件名是否为当天日期

若发现为空，回到"验证 2"确认内容文件是否成功写入。

## IPO周报数据来源

| 报告模块 | 接口 | 来源 | 用途 |
|---------|------|------|------|
| 一、排队情况 | `ak.stock_register_kcb/cyb/bj/sh/sz` | 东方财富注册制审核公示 | 各板块在审排队数+状态分布 |
| 二、本周期上会 | `ak.stock_ipo_review_em` | 东方财富 IPO审核动态 | 上会企业列表 |
| 三、本周期获批 | `ak.stock_ipo_declare_em` | 证监会公示 | 获发行批文（注册/核准） |
| 四、终止撤回 | `ak.stock_ipo_declare_em` | 证监会公示 | 本周终止企业 |
| 五、下周期上会 | `ak.stock_ipo_review_em` | 东方财富 IPO审核动态 | 下周期上会计划 |
| 六、新股上市 | `ak.stock_xgsr_ths` | **同花顺** | 上市日期+发行价+首日涨跌幅 |

> 注：六、新股上市仅用同花顺 `stock_xgsr_ths`，一次调用同时获取上市信息+发行价+首日涨跌幅，无需额外调用证监会 CNINFO 接口。

---

## 常见问题

**Q1：生成后如何做质量检查？**
A：生成报告后必须检查以下四项：
1. **日期检查**：报告第一行日期 == 文件名日期 == 当天实际日期（三者必须一致）
2. **星期检查**：报告中的日期字符串（`YYYY年MM月DD日（周X）`）与文件名中的日期 `weekday()` 对应周一～周五正确
3. **数据完整性**：
   - 收盘小结：指数行情、情绪打分、板块资金流、风险偏好、操作建议五段落齐全
   - 晨报/晚报：涨跌停统计、风险偏好、操作建议三段落齐全
4. **时效性**：数据陈旧（>2个交易日）时在报告内注明

**Q2：如何判断涨停情绪？**
A：涨停情绪由第4节打分函数统一评分（满仓风险系数 × 涨停家数权重 + 涨跌停比 × 炸板率综合得出 0-100 分），不再单独使用 emoji 分级。报告生成后通过"质量检查第3项"确认段落齐全即可。
- 参考：情绪总分 ≥ 70 → 🟢做多；≥ 55 → 🟡偏多；≥ 40 → ⚪分歧；≥ 25 → 🟠偏空；< 25 → 🔴冰点

**Q3：炸板率如何评分？**
A：炸板率由第4节打分函数中的 `_sc(exp_rate, 40, 10)` 公式映射到 0-100 分，阈值区间 [40%, 10%]，炸板率越低得分越高。
- 参考：情绪总分 ≥ 70 → 🟢做多；≥ 55 → 🟡偏多；≥ 40 → ⚪分歧；≥ 25 → 🟠偏空；< 25 → 🔴冰点

**Q4：两融数据比当天少一天？**
A：正常现象。两融数据在当天收盘后约 1～2 小时后更新，晚报/收盘小结取到的是上一交易日数据。

**Q5：主力净流入 > 500亿时显示什么？**
A：打印预警信息 `⚠️ 主力净流出-XXX亿，超大单+大单砸盘XXX亿，异常大额出逃，注意风险`，但保留真实数值（不重置为0）。

**Q6：定时任务重复推送？**
A：已内置文件锁机制的脚本会拒绝并发执行。当前各脚本锁机制如下：
- 晚报：`send_evening_report.py` → `/tmp/a_stock_evening.lock`（exists 检测 + sys.exit(0)，finally 解锁）
- 盘中预警：`send_intraday_alert.py` → `/tmp/a_stock_intraday.lock`（同上）
- 周末要闻：`send_weekend_news.py` → `/tmp/a_stock_weekend.lock`（同上）
- IPO周报：`send_ipo_report.py` → `/tmp/a_stock_ipo.lock`（原子 os.O_EXCL 创建，更严格，finally 解锁）
- 晨报：`send_morning_report.py` → `/workspace/skills/A-stock-report/scripts/.morning_report_lock.json`（JSON 文件，内容含 `date` 和 `status`，检查当日是否已成功推送后才允许重复执行）

**Q7：报告内容日期和文件名不对应？**
A：收盘小结文件名=报告日期；晚报文件名=生成当天日期，内容日期=上一交易日；周末要闻以内容里两融余额标注的日期为 key，与收盘小结文件名日期对齐合并。

**Q8：如何使用 `--date` 指定历史日期？**
A：收盘小结和晚报均支持 `--date YYYY-MM-DD`，如 `python3 send_close_summary.py --date 2026-04-13`。晨报不支持指定历史日期。
