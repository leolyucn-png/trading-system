# 🔧 GitHub开源技能→系统分配清单

> 建立：2026-07-02 23:10 | 强制规则：每次启动必须先跑技能再给结论

---

## 📊 GitHub Top项目速览

| 项目 | Stars | 用途 | 分配到 |
|:----|:-----:|:----|:------|
| **TradingAgents-Astock** | 65k+ | 7个AI分析师+双LLM，A股专属 | 🦁汉武帝 |
| **OpenBB** | 57.4k | 全球金融数据+AI Copilot | 🏯诸葛亮+司马懿 |
| **ai-hedge-fund** | 44.9k | 多智能体模拟投资大师策略 | 🗡️张飞 |
| **vnpy** | 38.6k | Python量化交易平台 | 🔧底层 |
| **daily_stock_analysis** | 27.3k | LLM生成每日决策报告 | 🐉刘备 |
| **FinGenius** | 新兴 | A股多智能体博弈分析 | 🐉关羽 |
| **Ashare-stockAnalysis** | — | 免费A股实时数据 | 🔧数据源 |
| **adata** | — | 免费A股量化SDK | 🔧数据源 |

---

## 各系统技能分配

### 🗡️ 张飞 — 反人性博弈
```
核心技能：
  ✅ ai-hedge-fund → 模拟投资大师反人性策略
  ✅ 已有的张飞模型v2.2（主引擎）
  
数据源：
  ✅ akshare/Ashare → 实时行情
  ✅ capital-flow-monitor → 资金流预警
  
强制规则：
  □ 启动时先跑量化触发（五大量化）
  □ 盘中节点(13:00/13:30/14:00)强制查询
```

### 🐉 刘备 — 舆情验证
```
核心技能：
  ✅ daily_stock_analysis → LLM每日决策报告
  ✅ FinGenius → 多智能体博弈
  ✅ stock-news-hunter → 新闻扫描
  ✅ rumor-scanner → 小作文鉴别
  ✅ policy-pulse → 政策前瞻
  
数据源：
  ✅ 八大数据源（冷门信息池优先）
  
强制规则：
  □ 前置预判模式：只用冷门信息池
  □ 事后验证模式：挂红字警告
  □ 短线模式隔离：汉武帝/刘彻不启动刘备
```

### 🐉 关羽 — 资金扫描（第一判定层）
```
核心技能：
  ✅ quant_flow_scan → 细分概念资金流
  ✅ quant_qstock → 板块相对强度
  ✅ sector-analyst → 板块分析
  ✅ leader-stock-identification → 龙头识别
  ✅ capital-flow-monitor → 北向资金
  
数据源：
  ✅ akshare → 概念/行业资金流
  ✅ qstock → 细分板块计算
  
强制规则：
  □ 每次启动前先跑quant_flow_scan
  □ 二级概念独立统计（不汇总到一级行业）
  □ 15分钟短周期判定(09:35-09:50)
```

### 🐉 刘彻 — 轮动埋伏
```
核心技能：
  ✅ 关羽全量输出（资金方向先决）
  ✅ sector-rotation → 轮动判断
  ✅ stock-sector-hunter → 板块扫描
  ✅ hot-news-aggregator → 舆情催化
  ✅ ai-trader → AI交易信号
  
强制规则：
  □ 模式检测器第一优先级
  □ 策略白名单（不在名单=禁用）
  □ 竞价前置校验
  □ 空仓输出宁缺毋滥
```

### 🦁 汉武帝 — 短线执行
```
核心技能：
  ✅ TradingAgents-Astock → 7分析师A股决策
  ✅ akshare-stock → 实时行情
  ✅ trade-signal → 交易信号
  ✅ deepstock → 深度分析
  
数据源：
  ✅ 新浪/腾讯实时API
  ✅ 东方财富竞价格式
  
强制规则：
  □ GATE 0-3四层全过
  □ 卖出前三问（张飞校验）
  □ 板块资金流校验
  □ 龙虾量化指令集
```

### 🏯 诸葛亮 — 长期票DNA
```
核心技能：
  ✅ OpenBB → 全球产业趋势验证
  ✅ fundamental-screening → 基本面筛选
  ✅ financial-report-analysis → 财报分析
  ✅ biga → 大趋势框架验证
  
数据源：
  ✅ akshare/Ashare → 历史K线+财务
  
强制规则：
  □ DNA五维必过
  □ 全球趋势第七条
  □ 龙头判定
  □ 14天持仓上限
```

### 🦞 龙虾 — 未发酵题材
```
核心技能：
  ✅ rumor-scanner → 冷门信息扫描
  ✅ policy-pulse → 政策吹风抓取
  ✅ capital-flow-monitor → 资金先行
  ✅ financial-report-analysis → 财报前瞻
  
强制规则：
  □ 14:00 强制重扫
  □ 预期差判定优先
```

### 🏛️ 司马懿（郭嘉） — 美股波段
```
核心技能：
  ✅ OpenBB → 全球金融数据
  ✅ guojia-us-stock → 自建美股系统
  ✅ biga → 大趋势验证
  
数据源：
  ✅ yfinance → 美股实时行情
  ✅ yahooquery → 机构持仓
```

---

## 🔴 铁律（违反=作废）

```
1. 任何股票分析，必须先调取数据API，禁止凭记忆/聊天记录回答
2. 启动任何系统前，先检查对应技能清单，缺一项不出分析
3. 技能失败的必须标出来（如"❌ akshare超时"），不能装作调用了
4. 不能因为API慢就绕过去——慢也要等，或用备选数据源说明
```
