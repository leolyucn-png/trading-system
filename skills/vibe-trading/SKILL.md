---
name: vibe-trading
description: 港大HKUDS开源全栈AI交易平台Vibe-Trading的秦始皇集成层。提供68个量化交易工具：Research Autopilot（全自动假设→信号→回测闭环）、多源数据加载（A股/美股/加密货币）、回测归因分析、Swarm多智能体投研委员会、定时策略执行。
---

# Vibe-Trading 秦始皇集成层

> 源项目：https://github.com/HKUDS/Vibe-Trading
> 论文/文档：https://vibetrading.wiki/docs/
> 集成日期：2026-06-22

---

## 一、安装与部署

### 前提条件

| 依赖 | 要求 |
|:----|:----|
| Python | ≥ 3.11（当前环境3.8.6，需升级） |
| pip | 最新版 |
| 操作系统 | macOS/Linux/Windows |
| Docker | 可选（推荐Docker部署） |

### 安装步骤

```bash
# 1. 升级Python（macOS）
brew install python@3.11
# 或使用conda
conda create -n vibe-trading python=3.11
conda activate vibe-trading

# 2. 安装Vibe-Trading
pip install vibe-trading-ai

# 3. （可选）安装技术分析扩展
pip install "vibe-trading-ai[harmonic]"

# 4. （可选）DeepSeek原生适配器
pip install "vibe-trading-ai[deepseek]"

# 5. Docker部署（替代本地安装）
docker pull hkuds/vibe-trading:latest
docker compose up
```

### 环境变量

| 变量 | 必需 | 说明 |
|:----|:---:|:-----|
| `OPENAI_API_KEY` | ✅ | LLM API密钥 |
| `VIBE_TRADING_ENABLE_SCHEDULER` | 可选 | 启用定时策略执行 |
| `VIBE_TRADING_SEARCH_BACKENDS` | 可选 | 搜索后端列表（默认DDG→Google→Bing→Brave→Mojeek→Yahoo） |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS` | 可选 | 启用Shell工具（安全敏感） |
| `VIBE_TRADING_TRUST_DOCKER_LOOPBACK` | 可选 | Docker模式信任本地回环 |
| `OLLAMA_BASE_URL` | 可选 | Ollama本地模型地址 |

---

## 二、核心功能模块（68个工具）

### 模块A：Research Autopilot 🔬（核心创新）

**一句话：全自动量化策略研发流水线。**

```mermaid
Hypothesis → Signal Engine → Backtest → Attribution → Report
   ↑                                                |
   └──────────────── 迭代优化 ───────────────────────┘
```

| 工具 | 功能 | 对应秦始皇模块 |
|:----|:-----|:-------------|
| `run_research_autopilot` | 从假设(hypothesis)出发，自动生成信号引擎、执行回测 | 策略生成器 |
| `generate_backtest_config` | 根据研究目标生成回测配置 | 策略配置器 |
| `scaffold_signal_engine` | 自动编写信号引擎代码 | 信号开发层 |
| `link_autopilot_backtest` | 将回测结果反馈给原假设，形成闭环 | 策略迭代器 |
| `run_swarm` | 启动多智能体投研委员会（13个预设模板） | 投研委员会 |

**接入点：** 用你的"大趋势牛股框架"六条规律作为假设输入 → Research Autopilot自动验证

### 模块B：多源数据加载 📊

| 数据源 | 工具/能力 | 覆盖市场 |
|:------|:---------|:--------|
| yfinance | `get_market_data` | 美股、全球ETF |
| baostock | `get_market_data` | A股（sh/sz代码直入） |
| CCXT | 通过loader层 | 加密货币 |
| 本地文件 | 数据桥接器 | CSV/Parquet/DuckDB |
| 定时调度 | 定时取数cron | 全市场 |

**关键增强：** OHLC数据完整性检查 — 自动检测并过滤异常K线

### 模块C：回测与归因分析 📈

| 工具 | 功能 |
|:----|:-----|
| 标准回测引擎 | 历史数据回测策略表现 |
| **分层归因** | ✅ 交易级赢家/输家分析 |
| **Beta回归** | 市场关联度分析 |
| **市场状态分析** | 区分牛市/熊市/震荡市下的策略表现 |
| **蒙特卡洛排列检验** | 策略收益显著性检验（运气 vs 能力的统计检验） |

### 模块D：Swarm多智能体投研委员会 🐝

| 预设 | 工人数 | 用途 |
|:----|:-----:|:----|
| `equity_research_team` | 21 | 股票研究委员会 |
| 共13个预设模板 | 各3-21 | 覆盖不同投资场景 |

**核心特点：**
- 工人共享统一市场数据工具（不再各自爬取）
- 委员会模式：多Agent辩论 → 综合投资结论
- 严格JSON输出，NaN序列化为null

### 模块E：定时策略执行 ⏰

| 功能 | 说明 |
|:----|:-----|
| 定时研究执行器 | 按interval/cron调度策略运行 |
| 报告库 | 运行记录搜索、过滤、对比 |
| 运行归因 | 每次回测后自动生成归因报告 |

### 模块F：Web搜索 🔍

多引擎容错搜索 — DuckDuckGo被封时自动切换Google→Bing→Brave等
（正好解决我们今晚遇到的DuckDuckGo被封问题！）

### 模块G：影子账户 Paper Trading 💰

模拟交易环境，在不上真金白银的情况下验证策略。

---

## 三、与大趋势牛股框架的集成路径

### 集成架构

```
大趋势牛股框架（六条规律）
        ↓ 转化为可量化假设
Vibe-Trading Research Autopilot
        ↓ 自动生成信号引擎
Backtest（历史验证）
        ↓ 归因分析
结果反馈 → 优化假设 → 形成策略
        ↓
秦始皇执行层 → 对接汉武帝/诸葛亮
```

### 第一步：将六条规律转化为假设

```python
# 示例：大趋势牛股规律 → Research Autopilot 输入
hypothesis = {
    "name": "双轮驱动突破策略",
    "description": "旧主业稳定盈利+新业务稀缺性=双重估值切换机会",
    "conditions": {
        "pe_range": [10, 150],           # 规律①：PE合理
        "market_cap_range": [100, 400],   # 规律④：黄金市值
        "shareholder_decreasing": True,   # 规律②：股东人数下降
        "volume_breakout": True,          # 规律⑤：放量突破
    },
    "target_min_return": 0.5,            # 目标50%+收益
    "hold_period_days": 180              # 半年大趋势
}
```

### 第二步：Swarm委员会验证候选

```
输入候选（如宗申动力/康强电子）
  ↓
秦始皇接收 → 启动Swarm equity_research_team
  ↓
13个预设中的3-5个工人并行分析：
  - 工人1：基本面+双轮驱动验证
  - 工人2：技术面+三阶段走势判断
  - 工人3：资金面+机构游资结构
  - 工人4：赛道催化+新闻扫描
  - 工人5：风险检查（减持/冻结/业绩）
  ↓
综合报告 → 买入/观望/剔除
```

### 第三步：回测验证

```
对候选执行Research Autopilot：
  Phase 1: 用两年历史数据回测策略
  Phase 2: 分层归因（什么行情下赚钱/亏钱）
  Phase 3: 蒙特卡洛检验（收益是否显著）
  
通过 → 进候选池
不通过 → 剔除或调整参数
```

---

## 四、技能对接映射表

| Vibe-Trading能力 | 对接的秦始皇模块 | 优先级 |
|:----------------|:--------------|:-----:|
| Research Autopilot（假设→回测） | 策略研发引擎 | P0 |
| 多源数据加载（A股+美股） | 数据管道 | P0 |
| Swarm投研委员会 | 投研决策层 | P1 |
| 回测归因分析 | 策略评估模块 | P1 |
| 影子账户 | 模拟交易环境 | P1 |
| 定时策略执行 | 自动化执行层 | P2 |
| Web搜索容错 | 情报层补充 | P2 |

---

## 五、首批验证计划

### 验证1：康强电子 002119（用Vibe-Trading跑全流程）

```yaml
候选: 康强电子 002119
假设: 传统引线框架龙头+先进封装新业务=双轮驱动
输入数据: 2年日K线 + 财务数据
Swarm验证: 启动5人投研委员会
回测: 验证"横盘突破买入"信号的收益显著性
```

### 验证2：宗申动力 001696

```yaml
候选: 宗申动力 001696
假设: 传统发动机盈利+低空经济新业务=第二增长曲线
Swarm验证: 重点评估低空经济赛道持续性
回测: 验证"连板回调二波"模式的统计胜率
```

---

## 六、风险与控制

| 风险 | 控制措施 |
|:----|:--------|
| Python版本不兼容 | 使用Docker隔离环境 |
| API密钥泄露 | 环境变量管理，不硬编码 |
| 回测过拟合 | 蒙特卡洛排列检验+样本外验证 |
| 实盘风险 | 先用影子账户跑1-3个月 |

---

## 七、快速启动命令

```bash
# 启动Vibe-Trading服务
vibe-trading start

# 启动Web UI（默认localhost:3000）
vibe-trading web

# 启动交互式CLI
vibe-trading chat

# 恢复前次会话
vibe-trading resume <session-id>

# 诊断环境问题
vibe-trading provider doctor

# Docker部署
docker compose up
```

---

*关联系统：秦始皇 | 对接：汉武帝(执行) + 诸葛亮(情报) + 大趋势牛股框架(逻辑)*
*更新日期：2026-06-22 | 当前状态：✅ SKILL.md完成，待安装部署*
