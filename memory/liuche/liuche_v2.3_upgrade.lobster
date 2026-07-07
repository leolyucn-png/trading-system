name: liuche_v2.3_upgrade
system_id: liuche_v2.3
description: 刘彻 v2.3 短线轮动埋伏系统升级·超预期持有+C型置信度+板块粒度+补仓+归因

# ====== 一、超预期持有机制（核心升级） ======
super_expect:
  trigger_any_one:
    - "买入次日开盘后1小时内涨幅>7%"
    - "买入次日直接涨停（封单稳定）"
    - "买入后连续2日上涨，累计涨幅>10%"
    - "所属板块进入主线持续模式，个股成为板块龙二及以上"
  pre_condition: "核心上涨逻辑未破坏，刘备验证催化仍在"
  
  upgrade_action: "自动从「轮动反弹」升级为「主升浪持有」"
  
  adjustments:
    take_profit:
      original: "+5%"
      upgraded: "+12%~+15%"
    hold_period:
      original: "T+1至T+3"
      upgraded: "T+3至T+7"
    stop_loss:
      original: "-3%硬止损"
      upgraded: "移动止损：从高点回落5%止损"
    sell_rule:
      primary: "移动止盈：从当日高点回落3%卖出50%，回落5%清仓"
      secondary: "触发大乔卖点信号时卖出"
  
  downgrade_trigger_any_one:
    - "单日放量滞涨，收长上影线"
    - "所属板块资金连续2日流出"
    - "张飞触发一致性收割预警"
    - "跌破5日线且当日未收复"
  downgrade_action: "降级回普通轮动标的，按原规则止盈止损，当日内择机卖出"

  today_example: "卧龙电驱7/2→7/3: 浮盈+10%涨停→触发升级条件②→应升级为超预期持有→周二再评估"

# ====== 二、C型置信度分级 ======
c_type_confidence:
  reference: "张飞 v2.2 A/B/C型判定规则"
  definition: "板块内尚未启动、处于轮动后排、资金还未关注的标的"
  
  levels:
    high_confidence:
      conditions_all:
        - "张飞明确判定C型"
        - "落后板块幅度>3%"
        - "近3日无大幅波动"
        - "板块内涨幅排名后20%"
      score_bonus: 5
      label: "C型·高置信"
      today_example: "海特高新: 军工+2.67%→落后4.4%→张飞C型→高置信"
    
    medium_confidence:
      conditions_all:
        - "张飞判定C/B交界型"
        - "落后板块幅度1.5%-3%"
        - "板块内涨幅排名20%-30%"
      score_bonus: 3
      label: "C型·中置信"
      today_example: "隧道股份: 基建+2.04%→落后1.5%→C/B型→中置信"
    
    low_confidence:
      conditions_all:
        - "张飞未明确判定，仅技术形态符合"
        - "落后板块幅度<1.5%"
      score_bonus: 1
      label: "C型·低置信"

  score_integration:
    old: "score = |落后|×3 + (35-位置)/5×2 + C型加分(5/0)"
    new: "score = |落后|×3 + (35-位置)/5×2 + C型置信度加分(5/3/1)"

# ====== 三、板块粒度细化 ======
block_granularity:
  priority_order:
    - "概念板块（最优）"
    - "二级行业（次优）"
    - "一级行业（兜底）"
  
  selection_principle: "优先选择最细分、最贴合当前炒作逻辑的概念板块"
  
  examples:
    AI行情: "用「AI算力」「AI应用」≠「计算机」"
    新能源: "用「光伏设备」「储能」≠「电力设备」"
    军工行情: "用「军工龙头」「商业航天」≠「国防军工」"
  
  guan_yu_input: "关羽输出资金流向时，必须同时提供概念板块、二级行业、一级行业三个维度的数据"
  
  mapping_rules:
    concept_to_stock: "概念板块→直接对应成分股"
    secondary_to_stock: "二级行业→对应成分股"
    primary_to_stock: "一级行业→仅在无更细分板块时使用"
  
  cross_verify: "若多个维度同时出现资金流入，以最细分板块为准"

# ====== 四、日内位置标准化 ======
intraday_position:
  formula: "位置 = (当前价-当日最低)/(当日最高-当日最低) × 100%"
  data_time: "14:20尾盘扫描快照"
  thresholds:
    low: "<40%（适合埋伏）"
    mid: "40-60%（中等）"
    high: ">60%（不建议）"
  
  edge_cases:
    high_low_equal: "最高=最低 → 按50%处理"
    new_stock: "上市<30日新股不适用"
    limit_up_down: "涨停/跌停直接排除"

# ====== 五、补仓机制 ======
add_position:
  allowed:
    scenario_1_washout:
      name: "洗盘确认加仓"
      trigger_all:
        - "买入后次日缩量回调，跌幅<3%"
        - "未跌破买入价"
        - "所属板块资金仍在流入"
        - "小乔发出缩量回踩支撑买点信号"
      add_ratio: "原仓位的30%"
      time_window: "买入后第2天尾盘"
    
    scenario_2_breakthrough:
      name: "突破确认加仓"
      trigger_all:
        - "买入后放量突破前期平台"
        - "涨幅<5%（不追高）"
        - "小乔发出横盘突破买点信号"
      add_ratio: "原仓位的20%"
      time_window: "突破当日尾盘"
  
  forbidden_any_one:
    - "持仓已浮亏>3%（禁止越跌越补）"
    - "单票仓位已达上限"
    - "张飞发出预警"
    - "板块资金转流出"
    - "买入后第3天及以后（接近持有期末）"
  
  hard_limits:
    max_add_times: 1
    total_limit: "加仓后总仓位 ≤ 单票仓位上限"

# ====== 六、失败归因系统 ======
failure_attribution:
  failure_definition:
    - "止损出局（亏损>3%）"
    - "持有期内最高涨幅<1%"
    - "买入后连续2日下跌"
    - "卖飞后3日涨幅>10%"
  
  auto_collect: "赵云每日收盘后自动归集刘彻失败案例"
  
  dimensions:
    - "选股问题：是否选错了标的/板块"
    - "择时问题：是否买在高位/卖在低位"
    - "模式问题：是否用错了市场模式"
    - "风控问题：是否触发了风控但未执行"
    - "市场原因：是否为系统性风险/黑天鹅"
  
  output: "标的|失败类型|归因维度|具体原因|改进建议"
  archive: "memory/liuche/failure_cases/"
  
  weekly_review:
    frequency: "每周日自动生成"
    content: ["本周失败案例汇总","高频错误类型统计","规则优化建议","下周注意事项"]

# ====== 七、小乔/大乔联动边界 ======
cross_model:
  xiaoqiao_boundary:
    liuche_duty: "确定标的、方向、交易窗口、总仓位"  
    xiaoqiao_duty: "优化具体买入价位、分批节奏、仓位分配"
    priority: "刘彻的窗口和仓位为硬约束，小乔不得突破"
    veto: "小乔判定假买点→有权否决，刘彻信号作废"
    workflow: "刘彻候选→小乔择时→符合执行/不符合退回"
  
  daqiao_boundary:
    liuche_duty: "确定止盈止损底线、持有期上限"
    daqiao_duty: "优化卖出节奏、持有/做T/止盈判定"
    priority: "刘彻硬止损+持有上限=绝对底线"
    upgrade_right: "大乔可建议延长持有期，需刘彻确认生效"
    workflow: "刘彻持仓→大乔监控卖点→触发卖出/未触发持有"
  
  conflict_resolution:
    case_1: "小乔vs刘彻 → 小乔为准（宁可错过不做错）"
    case_2: "大乔vs刘彻 → 大乔为准（止盈优先）"
    case_3: "张飞vs任何 → 张飞为准（风控一票否决）"
