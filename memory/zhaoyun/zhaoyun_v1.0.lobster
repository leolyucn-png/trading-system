name: zhaoyun_v1.0_review
system_id: zhaoyun_v1.0
description: 赵云复盘归因引擎·全系统自我进化闭环

# ====== 系统定位 ======
positioning:
  role: "全系统后置复盘优化中枢"
  run_time: "每日15:45自动启动，收盘后执行"
  not_responsible_for: ["实时交易", "选股", "择时", "风控拦截"]
  responsible_for: ["全模型业绩核算", "错误归因", "参数迭代提案", "经验归档"]
  priority_chain: "所有交易模型→龙虾(执行)→赵云(复盘归因)→优化建议反馈至各模型"
  core_principle: "后置运行不碰实盘，只提建议不改规则，归因到规则，全量归档可追溯"
  cover_models: ["张飞","秦始皇","关羽","刘备","诸葛亮","刘彻","汉武帝","小乔","大乔","龙虾"]

# ====== 一、每日收盘全模型核算 ======
daily_calculate:
  run_at: "15:45"
  
  dimensions:
    - id: "model_win_rate"
      name: "信号胜率"
      calc: "该模型当日发出信号中，次日/持仓周期内正确的占比"
    - id: "profit_contribution"
      name: "盈亏贡献"
      calc: "按信号执行后的实际盈亏，按模型拆分占比"
    - id: "signal_count"
      name: "信号活跃度"
      calc: "有效信号数/执行数/风控拦截数"
    - id: "profit_loss_ratio"
      name: "盈亏比"
      calc: "盈利单平均盈利÷亏损单平均亏损"
    - id: "max_drawdown"
      name: "最大回撤"
      calc: "当日/周期内最大浮亏幅度"
  
  drill_down:
    hanwu_patterns: "A-F六大模式分别胜率/盈亏比/平均收益"
    liuche_strategies: "A/B/C/D/F策略分别表现"
    xiaoqiao_points: "四大买点类型各自胜率/买入后平均涨幅"
    daqiao_points: "四大卖点类型各自逃顶成功率/卖飞率"
  
  risk_control_audit:
    zhangfei_blocked: "张飞预警拦截标的的后续实际跌幅"
    qinshihuang_capped: "秦始皇仓位限制规避的回撤"
    xiaoqiao_trap_filtered: "小乔假买点规则避开的亏损"
    daqiao_stop_saved: "大乔止损规则减少的亏损"

# ====== 二、错误案例自动归因 ======
error_attribution:
  error_types:
    sell_early:
      name: "卖飞"
      judge: "卖出后3个交易日内累计涨幅>10% / 涨停卖出后次日连板"
      attribution_to:
        - "大乔卖点规则是否过于保守"
        - "防卖飞铁律是否未生效"
        - "是否违反持有规则提前卖出"
      today_example: "晶澳科技7/1卖飞→7/2+6.8%"
    
    miss_rise:
      name: "踏空"
      judge: "观察未买入后3日涨幅>8% / 错过补仓机会"
      attribution_to:
        - "小乔买点阈值是否过严"
        - "选股模型筛选条件是否过严"
        - "风控规则是否误拦截"
    
    stop_loss:
      name: "止损/亏损"
      judge: "触发硬止损 / 持仓亏损>5%"
      attribution_to:
        - "选股逻辑是否失效"
        - "买点是否买在高位"
        - "止损阈值是否不合理"
        - "是否有突发利空"
      today_example: "完美世界7/3: -5.4%独立暴跌→选股逻辑可能失效"
    
    chase_high_loss:
      name: "追高被套"
      judge: "买入当日被套 / 次日低开亏损"
      attribution_to:
        - "是否违反追高铁律"
        - "买点判定是否误判假突破"
        - "板块节奏是否踏反"
  
  attribution_levels:
    level_1: "定位模型 — 选股问题/择时问题/风控问题"
    level_2: "定位规则 — 具体哪条阈值/触发条件导致误判"
    level_3: "定性原因 — 参数不合理/市场环境变化/规则有漏洞"

# ====== 三、案例库归档 ======
case_library:
  error_cases:
    path: "memory/zhaoyun/case_library/error/"
    fields: ["标的","时间","触发规则","实际走势","归因结论"]
    
  excellent_cases:
    path: "memory/zhaoyun/case_library/excellent/"
    fields: ["标的","时间","操作","盈利%","关键规则"]
    today:
      - "卧龙电驱7/2模式4逆势抗跌→7/3+10%涨停→张飞+刘彻精准选股"
      - "亚玛顿7/3竞价钓鱼→张飞假买点识别→低点反弹→小乔模式4验证"
  
  tag_system:
    tags: ["模型名称","错误类型","市场环境","板块","盈亏幅度"]

# ====== 四、参数迭代优化 ======
optimize:
  cycle:
    daily: "仅记录数据，不做建议"
    weekly: "输出周优化提案，针对胜率下滑/盈亏比异常的规则"
    monthly: "全系统月度评估，输出系统性规则迭代建议"
  
  directions:
    buy_sell_threshold:
      description: "小乔量比/回调阈值 + 大乔止盈/止损比例 回测对比"
      output_format: "当前参数胜率X%→调整为XX后胜率提升至Y%"
    
    strategy_weight:
      description: "不同市场模式下各策略胜率差异→建议调整仓位系数"
    
    rule_supplement:
      description: "高频错误→自动提示新增对应约束规则"
      example: "连续出现尾盘拉升假买点→提示补充否决规则"
  
  approval_flow: "赵云输出提案→人工审核→更新配置→下周验证→赵云复盘效果"

# ====== 五、全量记忆归档 ======
memory_archive:
  daily_log:
    path: "memory/YYYY-MM-DD.md"
    content:
      - "全模型业绩总览"
      - "当日盈/亏Top3标的及归因"
      - "典型错误案例+原因分析"
      - "风控拦截效果统计"
      - "次日操作注意事项"
  
  permanent_sync:
    path: "MEMORY.md"
    rules:
      - "跨模型通用铁律自动同步"
      - "经验验证后更新（如：缩量回踩20日线胜率75%）"
  
  weekly_monthly_report:
    weekly: "策略排行+错误分布+下周优化重点"
    monthly: "收益曲线+模型累计贡献+下月方向建议"

# ====== 六、模型健康度监控 ======
health_monitor:
  dimensions: ["胜率稳定性","盈亏比","回撤控制","信号质量"]
  weekly_score:
    above_80: "✅ 正常运行"
    between_60_80: "🟡 关注观察"
    below_60: "🔴 预警暂停该策略"
  
  conflict_detection:
    description: "定期扫描全模型规则→自动识别冲突"
    examples:
      - "A模型允许补仓+B模型禁止补仓→标记冲突"
      - "仓位规则上下矛盾→提示修正"

# ====== 七、跨系统联动 ======
cross_system:
  data_source: "从龙虾拉成交+从各模型拉信号日志+从行情接口拉实际走势"
  feedback: "优化提案→推送至对应模型配置待更新区→不直接修改运行规则"
  memory_link: "复盘结论→自动对接全局记忆系统"
  
  full_chain:
    description: |
      交易(9模型) → 龙虾(执行) → 赵云(复盘归因)
      → 优化提案 → 人工审核 → 模型更新
      → 下一轮交易验证 → 赵云验证效果
      → 完整自进化闭环

# ====== 今日实测 ======
today_trigger:
  sell_early_cases:
    - "晶澳科技7/1卖飞+10.5%→归因:被小作文吓→大乔防卖飞规则3/4/6应生效"
    - "中国卫星7/1卖飞+6.4%→归因:持仓耐心不足→张飞Day-2时序判定应提醒"
  
  stop_loss_cases:
    - "完美世界7/3 -5.4%→选股逻辑可能过期(分红已过)+大乔卖点4接近触发"
    - "天通股份7/3 -5%→归因:张飞A型判定→选股逻辑有问题"
  
  excellent_cases:
    - "卧龙电驱:模式4S级→+10%涨停→张飞+刘彻+小乔全链条验证"
    - "亚玛顿:假买点识别→低接→+10%→张飞+小乔精准"
    - "海特高新:C型→落后5%→方向全对，等周一验证"
  
  system_evolution:
    - "刘备废弃中文个股搜索→改为中英文双通道"
    - "小乔新建完整lobster配置"
    - "大乔新建完整lobster配置"
    - "赵云新建→自进化闭环完成"
