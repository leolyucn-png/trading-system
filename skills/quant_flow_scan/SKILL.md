---
name: quant-flow-scan
description: 细分概念资金流扫描器。基于AKShare概念/行业资金流API，按二级概念独立提取分时资金，拆分机器人/军工/光伏等大类下各细分方向的资金异动，适配刘备V2.1+轮动先知V1.1的二级概念资金统计需求。
---

# 细分概念资金流扫描器 StockFundFlow 配套

## 概述
替代原stock-fund-flow技能的一级行业资金流统计。  
**升级点：** 将资金统计粒度从「一级行业」下沉到「二级概念板块」，独立提取军工细分（人形机器人、减速器、航天复合材料）、光伏细分（组件、逆变器、设备）等资金流向，不被大类板块数据稀释。

## 数据源
| 接口 | 来源 | 用途 |
|:----|:----|:-----|
| `ak.stock_fund_flow_concept(symbol='即时')` | AKShare | 概念板块分时资金净流入/流出 |
| `ak.stock_fund_flow_concept(symbol='3日排行')` | AKShare | 3日累计概念资金流 |
| `ak.stock_fund_flow_concept(symbol='5日排行')` | AKShare | 5日累计概念资金流 |
| `ak.stock_fund_flow_industry(symbol='即时')` | AKShare | 行业板块资金流（备选） |

## 二级概念拆解清单

### 军工→拆分为
```
├── 人形机器人
├── 减速器/谐波减速器
├── 航天复合材料/商业航天
├── 低空经济/无人机
├── 军工电子/信息化
└── 导弹/弹药
```

### 光伏→拆分为
```
├── 光伏组件
├── 光伏逆变器
├── 光伏设备/电池片设备
├── 光伏玻璃/辅材
└── 分布式光伏/光伏建筑
```

### 半导体→拆分为
```
├── 半导体设备
├── 封装测试
├── IC设计
├── 半导体材料
└── 第三代半导体
```

### 医药→拆分为
```
├── 创新药
├── CXO
├── 中药
├── 化学制药
├── 生物制品
└── 医疗器械
```

## 每日输出格式

```
💰 【细分资金流扫描】YYYY-MM-DD

🔥 今日主力净流入TOP5细分概念：
  1. XXX概念: +X.XX亿（3日累计+X.XX亿）
  2. XXX概念: +X.XX亿

🔴 今日主力净流出TOP5细分概念：
  1. XXX概念: -X.XX亿

📊 连续流入≥3日（蓄力中）：
  · XXX概念：连续X日净流入，累计+X.XX亿

🔍 早盘15分钟异动（09:35-09:50）：
  · XXX概念：15分钟净流入+X.XX亿（大盘跌该细分逆势）
  → 标记【启动前置信号】

⚙️ 数据源：akshare stock_fund_flow_concept
```

## 调用方法
```python
import akshare as ak

# 即时概念资金流
df_now = ak.stock_fund_flow_concept(symbol='即时')
# 3日排行
df_3d = ak.stock_fund_flow_concept(symbol='3日排行')
# 5日排行
df_5d = ak.stock_fund_flow_concept(symbol='5日排行')
# 行业资金流（备选）
df_ind = ak.stock_fund_flow_industry(symbol='即时')
```
