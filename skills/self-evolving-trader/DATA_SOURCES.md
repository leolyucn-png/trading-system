#!/usr/bin/env python3
"""
汉武帝 · 数据源状态
=================
✅ 腾讯API(gtimg.cn)        → 个股实时 + 板块指数
✅ Sina API(hq.sinajs.cn)   → 大盘/深证/科创50 
✅ Yahoo Finance            → 美股AMD/NVDA/MRVL
✅ 同花顺(q.10jqka.com.cn)  → 涨幅榜/涨停板 (web_fetch)
✅ 新浪财经                 → 新闻/公告 (web_fetch)

❌ akshare/东财API          → 网络层阻断，502
  替代方案：同花顺web_fetch替代涨停板扫描

工作流：
  1. data_pipeline.py    → 腾讯+Sina = 实时数据 + 板块热力图
  2. web_fetch(同花顺)    → 涨幅榜TOP20 = 涨停板扫描
  3. web_search           → 新闻/政策/事件
  4. prediction_cards.py  → 模式匹配 = 自动预判卡
  5. Yahoo Finance       → 美股盘后数据
"""
