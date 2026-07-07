---
name: guojia-us-stock
description: 美股两周波段量化选股系统。基于yfinance+akshare+yahooquery数据源，四维量化打分，严格风控。独立目录memory/guojia_us_stock/。
---

# 🏛️ 郭嘉计划 V1.0 — 美股波段技能

## 数据源
| 工具 | 用途 |
|:----|:-----|
| yfinance | 行情/成交量/期权/财务 |
| akshare | 美股指数/ETF/VIX |
| yahooquery | 财报日历/做空/机构持仓 |
| pandas-ta | 均线/RSI等技术指标 |

## 输出
每次扫描输出至 `memory/guojia_us_stock/daily_scan_log/`
