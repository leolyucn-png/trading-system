name: xiaoqiao_v1.0_buy_timing
system_id: xiaoqiao_v1.0
description: 小乔买点精准择时引擎·全量化无主观

# ====== 系统定位 ======
positioning:
  role: "全体系通用执行层买点引擎"
  not_responsible_for: ["选股", "定方向", "定赛道", "宏观判断"]
  responsible_for: ["何时买", "能不能补", "买在哪个价位", "买多少仓位"]
  priority_chain: ["张飞(顶层风控)", "诸葛亮/汉武帝/刘彻(选股定方向)", "小乔(买点执行)", "龙虾(最终执行)"]
  core_rule: "仅在高胜率高赔率位置发买点信号，绝不追高"

# ====== 一、五大评分维度 (总分100) ======
scoring:
  dimension_1_washout:  # 洗盘识别 (30分·核心)
    weight: 30
    description: "A股洗盘频繁，此维度决定能否在洗盘后精准入场"
    items:
      - id: "缩量止跌"
        condition: "连续2日量<50日均量 AND 今日不破昨日最低"
        score: 8
      - id: "探底回升"
        condition: "日内从最低点回升≥2% AND 收盘在日内位置≥30%"
        score: 8
      - id: "不破关键位"
        condition: "价格在关键支撑±1%内企稳(整数关口/前低/20日均线)"
        score: 6
      - id: "恐慌后缩量"
        condition: "前日跌幅>3% AND 今日振幅<2% AND 量比<0.6"
        score: 5
      - id: "尾盘无跳水"
        condition: "14:30-15:00无放量跌破当日均价"
        score: 3

  dimension_2_position:  # 位置评估 (25分)
    weight: 25
    description: "买在低位、卖在高压区，杜绝追高"
    items:
      - id: "日内相对位置"
        condition: "日内位置≤30%"
        score: 10
        fallback: 
          condition: "日内位置30-50%"
          score: 5
      - id: "距近期高点"
        condition: "从5日高点回调≥5%"
        score: 5
      - id: "距板块强度"
        condition: "个股涨幅落后板块≥2% AND 板块在涨"
        score: 5
      - id: "均线位置"
        condition: "价格在20日均线±2%范围内"
        score: 3
      - id: "距涨停板距离"
        condition: "距下一个涨停价≥8% (非追涨停)"
        score: 2

  dimension_3_volume:  # 量价配合 (20分)
    weight: 20
    description: "量在价先，缩量是底，放量是真"
    items:
      - id: "量比健康"
        condition: "量比0.5-1.2 (非异常放量)"
        score: 6
      - id: "缩量企稳"
        condition: "连续3日量能递减但价格不再创新低"
        score: 5
      - id: "尾盘放量但不跌"
        condition: "14:30后量比>1.2 AND 价格不低于14:28价格"
        score: 4
      - id: "大单净比"
        condition: "大单净流入占比>30%"
        score: 3
      - id: "无异常量"
        condition: "当日最高量出现在上涨时段而非下跌时段"
        score: 2

  dimension_4_support:  # 支撑确认 (15分)
    weight: 15
    description: "下有支撑才敢买，无支撑不伸手"
    items:
      - id: "整数关口支撑"
        condition: "价格在整数关口+2%内 AND 当日未跌破整数关口"
        score: 5
      - id: "前低支撑"
        condition: "高于近5日最低点≤3% AND 今日低点抬高"
        score: 4
      - id: "均线支撑"
        condition: "站在5日或10日均线之上"
        score: 3
      - id: "板块支撑"
        condition: "所属板块ETF当日涨幅>0"
        score: 2
      - id: "大盘支撑"
        condition: "上证指数当日涨幅>-0.5%"
        score: 1

  dimension_5_timing:  # 时机窗口 (10分)
    weight: 10
    description: "A股有黄金窗口和死亡窗口"
    items:
      - id: "尾盘窗口"
        condition: "14:30-14:55时间段"
        score: 5
      - id: "竞价确认"
        condition: "09:25竞价高于昨收 AND 竞价量>昨日竞价量"
        score: 3
      - id: "周五谨慎"
        condition: "周五买入 → 自动-2分(周末风险)"
        score: -2
      - id: "盘中不追"
        condition: "10:00-14:00 → 仅允许补仓，不允许新开仓"
        score: 0  # 不扣分但限制行为

# ====== 二、买入信号分级 ======
signal_levels:
  S_strong_buy:
    min_score: 75
    action: "可以买入"
    position: "标准仓位×1.0"
    confidence: "高"

  A_buy:
    min_score: 60
    action: "可以试探性买入"
    position: "标准仓位×0.5"
    confidence: "中"

  B_watch:
    min_score: 45
    action: "仅观察，不买入"
    position: 0
    confidence: "低"

  C_avoid:
    max_score: 44
    action: "不碰"
    position: 0
    confidence: "极低"

# ====== 三、补仓专项规则 ======
add_position_rules:
  # --- 允许补仓场景 ---
  allowed_scenarios:
    - "持仓缩量回踩关键支撑位，核心上涨逻辑未破坏，属正常洗盘"
    - "情绪小作文错杀导致单日大跌，无实质利空，尾盘有资金承接"
    - "横盘后首次放量突破确认，单票仓位未达上限"
  
  # --- 补仓铁律 ---
  iron_rules:
    - "单票补仓不超过2次（第一支撑位首补，第二支撑位次补）"
    - "每次补仓仓位 ≤ 初始建仓的50%（禁止越跌越加、一次性满补）"
    - "补仓后整体仓位 ≤ 该标的单票仓位上限"
    - "补仓价格低于原成本 ≥ 2%（确实降低均价）"
    - "非连续补仓（间隔 ≥ 1个交易日）"
    - "小乔总分 ≥ 60（买点信号确认后补）"
  
  # --- 禁止补仓场景 (任一触发=禁止) ---
  forbidden_scenarios:
    - id: "放量破位"
      condition: "跌破关键支撑 AND 量比>1.5"
      reason: "放量出货非洗盘，主力在逃"
    - id: "高位追补"
      condition: "个股当日涨幅>3% OR 板块处于高潮期(ETF>3%)"
      reason: "高位加仓=自杀"
    - id: "逻辑松动"
      condition: "核心上涨逻辑被破坏（政策/业绩/竞争格局恶化）"
      reason: "逻辑没了还补什么"
    - id: "深度浮亏"
      condition: "持仓亏损>10%"
      reason: "禁止摊平成本，按规则止损"
    - id: "风控触发"
      condition: "张飞发出一致性收割预警 OR 板块风险预警"
      reason: "风控最高优先级"
    - id: "连续下跌"
      condition: "连续3日下跌"
      reason: "重新评估逻辑，不盲目补"
    - id: "盘中追补"
      condition: "10:00-14:00盘中追高补仓"
      reason: "绝对禁止，只等尾盘"

# ====== 四、时间窗口硬规则 ======
time_windows:
  pre_market_0920_0925:
    action: "仅观察竞价，不挂单"
    rule: "竞价虚拟价≠开盘价，09:25才确认"
  
  open_0930_1000:
    action: "禁止新开仓"
    rule: "开盘30分钟不决策，先观察方向"
    exception: "竞价确认+小乔总分≥80 → 可以买入"
  
  mid_1000_1400:
    action: "仅允许补仓(已有仓位)"
    rule: "盘中波动大，不追当日热点"
  
  golden_1430_1455:
    action: "主买入窗口"
    rule: "尾盘确认当日方向，风险最小"
  
  close_1455_1500:
    action: "禁止开仓"
    rule: "最后5分钟不交易，防止尾盘拉高出货"

# ====== 五、硬性否决规则 (一票否决) ======
hard_reject:
  - id: "追高禁止"
    condition: "个股今日涨幅>3% AND 不是T+0做T"
    reject: true
    message: "🚫 小乔拒绝: 今日已涨>3%，追高被套率>60%"
  
  - id: "板块高潮禁止"
    condition: "板块ETF涨幅>3% OR 板块涨停≥3家"
    reject: true
    message: "🚫 小乔拒绝: 板块高潮日不买，等回调"
  
  - id: "大盘崩溃禁止"
    condition: "上证跌幅>1.5% OR 北向流出>50亿"
    reject: true
    message: "🚫 小乔拒绝: 大盘环境恶劣，等企稳"
  
  - id: "跌停风险禁止"
    condition: "个股跌停 OR 距跌停<1%"
    reject: true
    message: "🚫 小乔拒绝: 跌停不抄底"
  
  - id: "ST禁止"
    condition: "个股为ST/*ST"
    reject: true
    message: "🚫 小乔拒绝: ST股不碰"

# ====== 六、仓位分级 (三档金字塔) ======
position_sizing:
  # 从原"仓位映射"升级为三档分级
  level_1_base:
    name: "底仓级（安全边际最高）"
    scenario: "缩量回踩关键支撑 / 逆势抗跌确认 → 首次建仓"
    position_ratio: "60%（占总预算）"
    max_amount: "¥15,000"
    signal_required: "小乔总分 ≥ 60"
    triggers: ["模式1 缩量回踩", "模式4 逆势抗跌"]
  
  level_2_trend_add:
    name: "趋势加仓级（洗盘结束/小幅突破）"
    scenario: "底仓已建，趋势明朗后加仓"
    position_ratio: "30%（占总预算）"
    max_amount: "¥8,000"
    signal_required: "小乔总分 ≥ 60 AND 底仓已盈利"
    triggers: ["模式3 横盘突破确认", "模式1二次回踩不破"]
  
  level_3_odds:
    name: "博弈级（极端错杀·高赔率）"
    scenario: "情绪错杀挖坑，尾盘有资金承接"
    position_ratio: "10%（占总预算）"
    max_amount: "¥5,000"
    signal_required: "小乔总分 ≥ 60 AND 刘备确认非实质利空"
    triggers: ["模式2 情绪错杀"]
  
  # --- 单票仓位上限 ---
  hard_caps:
    single_stock_max: "总仓位 × 25%"
    single_board_max: "总仓位 × 40%（张飞板块集中度限制）"
    total_position_max: "80%（秦始皇GATE 0=绿时）"
  
  weekend_adjust:
    condition: "周五买入"
    multiplier: 0.7  # 仓位×0.7

# ====== 七、输出模板 ======
output_template:
  format: |
    【小乔 买点评估】
    
    标的: {stock_name} ({stock_code})
    当前价: ¥{price} ({pct_change}%)
    方向来源: {direction_model} 判定 {sector}方向
    
    评分卡 (总分{total}/100):
      洗盘识别: {washout}/30  {washout_detail}
      位置评估: {position}/25  {position_detail}
      量价配合: {volume}/20  {volume_detail}
      支撑确认: {support}/15  {support_detail}
      时机窗口: {timing}/10  {timing_detail}
    
    信号等级: {level}
    操作建议: {action}
    建议价位: ¥{buy_zone_low} - ¥{buy_zone_high}
    建议仓位: {position_size}
    止损: ¥{stop_loss} ({stop_pct}%)
    止盈: ¥{take_profit} ({profit_pct}%)
    
    否决检查: {reject_check}

# ====== 八、四大买点模式 (场景化触发) ======
buy_point_patterns:
  pattern_1_shrink_support:
    name: "缩量回踩支撑型"
    priority: "最高"
    description: "波段首次建仓或持仓正常洗盘加仓的最佳买点"
    trigger_all:
      - "量比<0.7（对比20日均量，缩量确认）"
      - "回踩20日线/前期平台低点，未有效跌破（收盘价不低于支撑位2%）"
      - "日内跌幅1%-3%，刘备验证无实质利空"
      - "尾盘30分钟无放量砸盘"
    scenario:
      - "波段首次建仓"
      - "持仓正常洗盘加仓"
    position_coefficient: 1.0
    bonus_score: 15  # 模式匹配额外加分
    example_trigger:
      - "旭光电子6/8: 大盘-1.8%，个股缩量回踩均线，尾盘确认→买点1触发"
      - "卧龙电驱7/2: 科创-7.70%，个股+2.11%缩量抗跌，回踩确认→次日涨停"

  pattern_2_panic_pit:
    name: "情绪错杀挖坑型"
    priority: "高赔率"
    description: "小作文或情绪恐慌导致的非理性暴跌，优质标的被错杀"
    trigger_all:
      - "单日盘中最大跌幅>7%"
      - "刘备判定为小作文/情绪恐慌，无基本面实质利空"
      - "尾盘出现放量资金承接，收长下影线"
      - "所属板块无系统性风险"
    scenario:
      - "持仓错杀补仓"
      - "超跌标的埋伏"
    position_coefficient: 0.7
    bonus_score: 12
    risk_warning: "⚠️ 高赔率=高风险，必须刘备确认非实质利空"
    example_trigger:
      - "江化微7/3: 异动公告回调-8.89%，非基本面利空，尾盘承接→买点2候选"
      - "晶澳科技7/3: -7.29%，可转债调整非经营问题→买点2候选"

  pattern_3_breakthrough:
    name: "横盘放量突破型"
    priority: "趋势确认"
    description: "长时间横盘后的放量突破，趋势确认后的最佳进场点"
    trigger_all:
      - "前期横盘整理≥15个交易日"
      - "突破当日量比>1.8（放量确认）"
      - "站稳前期平台高点，当日涨幅<5%（不追涨停）"
      - "所属板块同步配合，非个股独立异动"
    scenario:
      - "突破型标的首次建仓"
    position_coefficient: 0.8
    bonus_score: 10
    forbid: "涨停突破→等次日回调再买，绝不涨停板追"
    example_trigger:
      - "15日横盘后放量突破平台，量比2.0+板块配合→买点3"

  pattern_4_antifall:
    name: "逆势抗跌确认型"
    priority: "强庄护盘"
    description: "大盘暴跌时个股逆势抗跌或微涨，主力控盘信号"
    trigger_all:
      - "大盘单日跌幅>1%"
      - "个股收红或微跌<1%，显著强于指数"
      - "量能平稳，主动买盘占比>55%"
      - "处于相对低位，非高位抗跌出货"
    scenario:
      - "逆势独立标的建仓/加仓"
    position_coefficient: 0.9
    bonus_score: 18  # 最高加分：逆势信号最可靠
    distinguish: "必须在低位≠高位抗跌(高位抗跌=出货)"
    example_trigger:
      - "卧龙电驱7/2: 科创-7.70%→卧龙+2.11%，逆势抗跌→模式4触发→次日涨停"
      - "云天化7/2: 科创-7.70%→云天化+1.25%，逆势独走→模式4触发"

# ====== 九、假买点识别 (六大陷阱·任一触发直接拒) ======
fake_buy_traps:
  description: "看似符合买点条件，实为主力出货/诱多陷阱，直接取消信号"
  
  trap_list:
    - id: "板块高潮后跟风补涨"
      condition: "板块当日涨幅>3% AND 个股尾盘被动跟涨(涨幅<板块但跟随拉升)"
      danger: "次日板块分化，跟风股最先跌"
      
    - id: "尾盘半小时放量拉升"
      condition: "14:30后放量拉>2% AND 无实质利好 AND 非突破平台"
      danger: "纯做收盘价，次日低开概率>60%"
      
    - id: "高开低走假突破"
      condition: "开盘冲高破平台 OR 竞价高开>3% → 全天回落收长上影"
      danger: "典型诱多出货，追入即套"
      example: "亚玛顿7/3 竞价+9.94%→低点-1.3% = 假突破确认"
      
    - id: "连涨3日后回调"
      condition: "连续上涨≥3日 AND 今日回调-2~-5%"
      danger: "连续上涨后的回调=出货中继，非洗盘买点"
      
    - id: "全网一致看多后回调"
      condition: "张飞一致性指数≥70% AND 今日个股回调"
      danger: "一致性预期下的回调=主力借乐观情绪出货"
      
    - id: "问题票低点"
      condition: "ST/退市风险/财务造假/监管问询标的的任何低点"
      danger: "这类票没有买点，只有陷阱"
  
  action: "任一假买点触发 → 直接取消买点信号，不输出任何买入建议"

# ====== 十、输出模板 ======
output:
  fields:
    - "标的名称"
    - "所属体系（诸葛亮波段/汉武帝短线/刘彻轮动）"
    - "买点类型（模式1-4）"
    - "买点等级（S/A/B/C）"
    - "建议买入区间"
    - "对应仓位比例"
    - "止损位"
    - "风险提示"
    - "信号失效条件"
  
  template: |
    ═══ 【小乔 买点判定】 ═══
    标的: {stock_name} ({stock_code})
    体系: {source_model} | 买点: {pattern_type}
    等级: {signal_level} | 仓位: {position_ratio}
    
    买入区间: ¥{buy_low} - ¥{buy_high}
    止损: ¥{stop_loss} ({stop_pct}%) | 止盈: ¥{take_profit}
    风险: {risk_warning}
    失效: {invalidation_condition}
    ═══════════════════════

# ====== 十一、跨系统联动 ======
cross_system:
  upstream:
    trigger_source: "诸葛亮/汉武帝/刘彻确定标的与方向后 → 调用小乔做买点择时"
    top_constraint: "张飞触发风控预警/一致性收割预警时 → 所有买点信号自动失效 → 禁止任何买入/补仓"
    logic_verify: "刘备验证催化真实、逻辑未破坏 → 买点信号生效 | 逻辑证伪 → 取消信号"
  
  share:
    all_models_shared: true
    no_exclusive_limit: true
    auto_match_best_point: true
    description: "小乔为全体系通用执行层，所有模型的选股结果均经过小乔买点择时"
  
  execution_flow: |
    张飞(风控) → 秦始皇(仓位) → 刘彻/汉武帝/诸葛亮(选方向)
    → 关羽(资金确认) → 刘备(逻辑验证) → 小乔(买点择时) → 龙虾(执行)

# ====== 十二、买点模式匹配引擎 =====
pattern_matcher:
  logic: |
    1. 遍历四大买点模式，检查触发条件
    2. 匹配到模式→基础分+bonus_score
    3. 同时匹配多模式→取最高bonus，叠加标志
    4. 最终得分 = 五大维度基础分 + 模式bonus
    5. 最大上限100分
  
  priority_override:
    pattern_4_antifall: "触发模式4时，自动提升一级仓位系数"
    pattern_1_shrink_support: "触发模式1时，可忽略周五-2分(强信号覆盖弱信号)"

# ====== 十、与现有系统联动 ======
integration:
  zhangfei:
    input: "一致性收割预警状态"
    action_if_warned: "小乔自动降一档 (S→A, A→B)"
  
  hanwu:
    input: "GATE 0大盘+选股方向"
    action: "接收汉武帝选股标的，执行买点评估"
  
  liuche:
    input: "刘彻轮动候选"
    action: "接收刘彻埋伏标的，执行买点择时"
  
  zhugeliang:
    input: "诸葛亮长期候选"
    action: "接收长期标的回调信号，评估再入时机"
  
  lobster:
    output: "买点信号+仓位建议"
    action: "龙虾接收小乔信号，执行最终交易指令"
