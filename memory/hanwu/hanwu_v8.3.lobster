name: hanwu_v8.3_lobster
system_id: hanwu_v8.3
description: 汉武帝预判型短线系统·龙虾量化指令集

# ====== 一、四层门控量化配置 ======
gates:
  gate0_dapan:
    scoring:
      green_zone: 6
      yellow_zone: 4
      red_zone: 2
      system_risk: 0
    conditions:
      green: [szzs_20d_up, north_inflow>20e, limit_down<10]
      yellow: [main_board_shock, north_flow_balance, limit_up<50]
      red: [szzs_20d_down, north_outflow>2d, limit_up<30]
      system_risk: [szzs_drop>2%, limit_down>50, north_outflow>50e]

  gate0_5_block:
    conditions:
      main_inflow_top5: true
      block_rise<3%: true
    scoring: {full: 10, half: 5, fail: 0}

  gate1_stock:
    hard_threshold:
      market_cap: [100e8, 400e8]
      turnover_rate: [3, 8]
      death_logic: false
    bonus:
      longhu_institution: 2
      block_activity_top30: 2
    scoring: {pass: 6, minimum: 5, fail: 0}

  gate2_catalyst:
    types: [policy_exp, earnings_forecast, us_stock_map, industry_event]
    scoring: {has_catalyst: 4, strong_catalyst: 6, no_catalyst: 0}

  gate_final:
    required: [gate0>system_risk, gate0.5>0, gate1>=5, gate2>0]

# ====== 二、模式量化触发 ======
patterns:
  A_pre_ambush:
    day_minus_1:
      volume_ratio>3: true
      rise<2%: true
      buy_ratio>55%: true
    day_0:
      volume_ratio<0.7: true
      drop: [1, 3]
      no_break_low: true
    time_window: "14:30-14:55"

  B_open_break:
    day_minus_1:
      rise: [3, 7]
      volume_ratio>2: true
      no_limit_up: true
    day_0_auction:
      buy_sell_ratio>2: true
      rise: [0.5, 2]
    time_window: "09:25-09:30"

  C_overnight:
    day_0:
      rise: [3, 7]
      volume_ratio>2.5: true
      no_limit_up: true
      buy_dominant: true
      no_late_dump: true
    block_condition:
      block_rise<2%: true
    time_window: "14:30-14:55"

  D_policy_pre:
    policy_days_before: 2
    block_inflow: true
    no_hype: true

  E_deep_v:
    day_minus_1:
      open_drop>1.5%: true
      volume_up_red: true
      long_lower_shadow: true
    day_0_auction:
      flat_or_small_up: true

  F_rotation:
    day_minus_1:
      block_rise: [2, 5]
      stock_rise: [2, 5]
      not_block_leader: true
    day_0:
      drop: [2, 5]
      volume_ratio<0.8: true

# ====== 三、模式→仓位映射 ======
mode_position:
  green_mode:
    total_cap: 80%
    single_max: 25%
    patterns: [A, C, E, D]
  yellow_mode:
    total_cap: 60%
    single_max: 15%
    patterns: [D, F]
  red_mode:
    total_cap: 30%
    single_max: 10%
    patterns: [C_narrow]
  system_risk:
    total_cap: 0%
    patterns: []

# ====== 四、持仓管理 ======
position:
  check_points: ["09:30", "10:00", "11:00", "11:30", "13:00", "13:30", "14:00"]
  status_rules:
    normal: [rise>=-2.5%, rise<=3%, volume_stable]
    over_perform: [rise>5%, early_take_profit]
    abnormal_drop: [drop>2%, volume_up, early_stop_loss_check]
    block_risk: [block_drop>2%, priority_up]
  sell_rules:
    high_open: {condition: [open_rise>3%, turnover>10%], action: sell_50%}
    mid_rise: {condition: [rise>=5%], action: sell_all}
    low_rise: {condition: [rise>=3%, rise<5%], action: sell_50%_before_1030}
    low_open: {condition: [open_drop<-2%], action: stop_50%}
    hard_stop: {condition: [drop<=-2.5%], action: stop_all}
    morning_clear: {condition: [no_profit_by_1030], action: clear_before_1030}
  priority:
    - stop_loss_triggered
    - block_outflow
    - near_take_profit_5%
    - low_confidence
    - keep_pattern_A_strong
  abnormal:
    suspended_bad_news: stop_after_resume
    one_limit_up: hold_to_next_open
    trading_halt: sell_if_rise<3%_after_resume

# ====== 五、刘彻对接 ======
liuche:
  schedule:
    daily_1440: push_t1_candidates
    daily_0925: push_open_operate_list
  rating:
    S: {gate>=9, pattern_A, strong_catalyst, block_inflow, position: 20-25%}
    A: {gate: [7,8], pattern_AF, has_catalyst, position: 10-15%}
    B: {gate: [5,6], pattern_BCE, normal_catalyst, position: <=10%}
  output: code|name|pattern|rating|block|buy_range|stop|take_profit|position|catalyst
  constraint: {max_per_day: 3, max_per_block: 2, gate_pass: true, death_reject: true}

# ====== 六、铁律量化 ======
rules:
  sell_three:
    q1: {query: is_rumor, official_bad: stop, rumor: watch}
    q2: {query: stock_vs_block, stock_worse_2x: prioritize_stop, block_down: watch}
    q3: {query: catalyst_valid, invalid: sell, valid: hold}
  block_outflow:
    period: 2d
    threshold: rank_top3
    action: no_new_position
  death_logic:
    lag_buy: [rise>3%, public_news_today]
    ignore_score: [gate1<5]
    safety_trap: [late_volume_rise>2%, 14:30-15:00]
    position_imbalance: [single>25%, block>40%]
    late_no_execute: [no_order_after_14:35, force_order]
