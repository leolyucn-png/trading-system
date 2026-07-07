from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import os

doc = Document()

# Styles
style = doc.styles['Normal']
font = style.font
font.name = 'Arial'
font.size = Pt(10)

# ============ COVER PAGE ============
doc.add_paragraph('')
doc.add_paragraph('')
doc.add_paragraph('')
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('A股四大交易系统')
run.bold = True
run.font.size = Pt(28)
run.font.color.rgb = RGBColor(180, 40, 40)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('汉武帝 · 刘彻 · 诸葛亮 · 秦始皇')
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(100, 100, 100)

doc.add_paragraph('')
version = doc.add_paragraph()
version.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = version.add_run('完整文档 v1.0 | 2026年6月23日')
run.font.size = Pt(12)

doc.add_page_break()

# ============ TABLE OF CONTENTS ============
doc.add_heading('目录', level=1)
toc_items = [
    '🦁 第一章：汉武帝计划 v8.0 — 短线快打系统',
    '🐉 第二章：刘彻计划 v1.0 — 短线轮动埋伏系统', 
    '🏯 第三章：诸葛亮计划 v7.0 — 独立牛股筛选系统',
    '🏛️ 第四章：秦始皇计划 v1.0 — 宏观资金配置系统',
    '📋 第五章：四系统协同工作流',
    '📖 第六章：核心教训与历史复盘'
]
for item in toc_items:
    p = doc.add_paragraph(item, style='List Number')
    p.paragraph_format.space_after = Pt(4)

doc.add_page_break()

# ============================================================
# CHAPTER 1: 汉武帝
# ============================================================
doc.add_heading('🦁 第一章：汉武帝计划 v8.0 — 短线快打系统', level=1)
doc.add_heading('1.1 核心定位', level=2)
doc.add_paragraph('版本：8.0 | 更新：2026-06-23 13:45')
doc.add_paragraph('核心定位：今买明出，最迟后天清仓。禁止任何中线思维。')
doc.add_paragraph('哲学：不打没预判的仗。持仓满2天无条件清仓。')

doc.add_heading('1.2 核心时序变革（v8.0灵魂）', level=2)
doc.add_paragraph('旧v7.x：反应型 — "今天看到涨 → 今天买 → 明天卖" → 结果：滞后1天，买在涨停潮日')
doc.add_paragraph('新v8.0：预判型 — "昨天看到异动 → 今天埋伏 → 明天涨 → 卖"')
p = doc.add_paragraph()
run = p.add_run('核心规则：所有买入信号必须基于昨天或前天的数据，不能基于今天的信号。')
run.bold = True

doc.add_heading('1.3 时序转换表', level=2)
table = doc.add_table(rows=6, cols=3)
table.style = 'Light Grid Accent 1'
headers = ['旧v7.x逻辑', '问题', '新v8.0逻辑']
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h
rows = [
    ['今天板块涨了→追龙二', '买在涨停潮日', '今天板块异动(放量小涨) → 埋伏'],
    ['今天个股放量突破→买入', '第2天涨停买不到', '昨天放量不涨→今天缩量回调→埋伏'],
    ['今天最强板块→明天继续', '第3天分化暴跌', '今天调整板块→明天可能轮动'],
    ['看到涨停了再追', '封板买不进', '昨天异动今天缩量→今天埋伏'],
    ['近5日涨幅前5板块', '已经是强弩之末', '近5日异动过但今天调整的板块'],
]
for i, row in enumerate(rows):
    for j, text in enumerate(row):
        table.rows[i+1].cells[j].text = text

doc.add_heading('1.4 信号分类', level=2)
doc.add_paragraph('🚀 真机会信号（在Day -1或Day -2出现）：')
doc.add_paragraph('  • 放量不涨：量比>3 + 涨幅<2% → 建仓信号', style='List Bullet')
doc.add_paragraph('  • 缩量回调：昨天放量涨→今天缩量跌→洗盘完成', style='List Bullet')
doc.add_paragraph('  • 抗跌企稳：大盘跌2%+ 它跌<0.5% → 有资金护盘', style='List Bullet')
doc.add_paragraph('  • 板块轮动：昨天涨→今天跌2-5% → 明天可能反弹', style='List Bullet')
doc.add_paragraph('')
doc.add_paragraph('💀 假机会信号（在Day 0出现，实际是陷阱）：')
doc.add_paragraph('  • 涨停潮：板块涨停≥3只 → 该卖不该买', style='List Bullet')
doc.add_paragraph('  • 板块涨幅>3% → 高潮信号，明天分化', style='List Bullet')
doc.add_paragraph('  • 连涨第3天 → 第三天的"强"是出货', style='List Bullet')

doc.add_heading('1.5 v8.0新6模式', level=2)
patterns = [
    ('模式A 预埋伏建仓', '昨天量比>3+涨幅<2%+今天缩量回调<1% → 今天尾盘埋伏 → 明天拉升'),
    ('模式B 预判高开', '昨天放量3-7%+今天竞价买盘>卖盘2倍 → 09:25竞价确认→开盘买入'),
    ('模式C 隔夜蓄力', '今天放量3-7%+未涨停+买盘>卖盘 → 今天尾盘埋伏（唯一当天触发）'),
    ('模式D 政策预埋伏', '政策公布前2天+受益板块异动 → 提前两天埋伏 → 公布日卖出'),
    ('模式E 深V确认', '昨天低开>1.5%+放量企稳翻红 → 今天开盘确认→买入'),
    ('模式F 轮动埋伏', '板块昨天涨2-5%→今天回调-2~-5%+缩量 → 今天尾盘埋伏龙三龙四'),
]
for name, desc in patterns:
    p = doc.add_paragraph()
    run = p.add_run(name + ' ：')
    run.bold = True
    p.add_run(desc)

doc.add_heading('1.6 买入五大硬性门槛', level=2)
doc.add_paragraph('① 今天不能是主线 — 今天弱的板块明天可能轮动 ✅')
doc.add_paragraph('② 市值50-300亿主板 — 保留')
doc.add_paragraph('③ 五大死亡逻辑校验 — 保留')
doc.add_paragraph('④ 必须在低位（日内位置<50%+距高点>5%）')
doc.add_paragraph('⑤ 信号必须来自昨天或前天（不是今天）')

doc.add_heading('1.7 卖出规则', level=2)
doc.add_paragraph('止盈：+3%可卖，+5%必须卖')
doc.add_paragraph('卖出时间：次日上午10:30前')
doc.add_paragraph('分级卖出：')
doc.add_paragraph('  高开>3% → 开盘卖50%，剩的冲高卖', style='List Bullet')
doc.add_paragraph('  平开/小涨 → 等冲高，10:00不冲就卖', style='List Bullet')
doc.add_paragraph('  低开<-2% → 开盘直止损', style='List Bullet')
doc.add_paragraph('止损：-2.5%硬止损')

doc.add_heading('1.8 死亡逻辑（v8.0新增）', level=2)
doc.add_paragraph('死亡逻辑七 — 时序滞后：买入信号来自今天（不是昨天/前天）→ 作废推荐')

doc.add_heading('1.9 6/17核心教训', level=2)
doc.add_paragraph('盈利票必须设移动止盈（从最高回落5%卖一半，10%全卖）')
doc.add_paragraph('亏损票-5%减半仓，-10%清仓')
doc.add_paragraph('错过信号：第1天没买到的，第2天还能买；第3天以上不追')

doc.add_page_break()

# ============================================================
# CHAPTER 2: 刘彻
# ============================================================
doc.add_heading('🐉 第二章：刘彻计划 v1.0 — 短线轮动埋伏系统', level=1)
doc.add_heading('2.1 核心定位', level=2)
doc.add_paragraph('版本：v1.0 | 建立：2026-06-23 12:48')
doc.add_paragraph('底层：龙虾量化策略执行指令 v1.0')
doc.add_paragraph('定位：专门选短期新股，T+1快打，埋伏轮动+情绪溢价')

doc.add_heading('2.2 三套核心策略', level=2)

doc.add_heading('策略A：提前埋伏轮动法 ⭐⭐⭐（最高优先级）', level=3)
doc.add_paragraph('预期胜率：60-70% | 盈亏比：1:2 | 每日推荐：2-3只')
doc.add_paragraph('')
p = doc.add_paragraph()
run = p.add_run('板块筛选四维度（全部通过）：')
run.bold = True
doc.add_paragraph('维度1 — 轮动规律法：近5日曾涨幅前5 + 最近1-2天连续调整 + 调整幅度-3%~-8% + 板块内部分化')
doc.add_paragraph('维度2 — 资金暗流法：近3-5天资金小碎步净流入 + 价格没涨但资金在进 + 成交量放大但价格在底部')
doc.add_paragraph('维度3 — 消息催化法：政策预期 + 行业事件 + 美股异动 + 研报提升')
doc.add_paragraph('维度4 — 技术趋势法：周线多头 + 日线支撑 + 量能放大30%+')
doc.add_paragraph('')
p = doc.add_paragraph()
run = p.add_run('个股筛选标准：')
run.bold = True
doc.add_paragraph('板块地位：龙二~龙五 | 流通市值：50-150亿 | 股性评分：≥7分')
doc.add_paragraph('相对位置：距前期高点>20% | 换手率：日常3-8%，异动10-20%')
doc.add_paragraph('排除项：ST/退市风险/连续亏损/高位放量滞涨')
doc.add_paragraph('')
p = doc.add_paragraph()
run = p.add_run('买卖规则：')
run.bold = True
doc.add_paragraph('买入：14:25-14:35 | 分2-3批 | 均价附近不追高+1% | 单只15-20%')
doc.add_paragraph('卖出：次日上午10:30前止盈+3%/+5% | 止损-2.5%')

doc.add_heading('策略B：情绪溢价追涨法 ⭐⭐', level=3)
doc.add_paragraph('预期胜率：50-60% | 每日推荐：1-2只')
doc.add_paragraph('板块条件：当日涨幅前3+板块涨幅>2%+资金净流入>5亿+涨停≥3')
doc.add_paragraph('个股条件：首板或二板+封板早+换手15-35%')
doc.add_paragraph('买入：14:40-14:50尾盘 | 选龙二/龙三')
doc.add_paragraph('止损：-3%硬止损')

doc.add_heading('策略C：隔夜消息竞价法 🎲', level=3)
doc.add_paragraph('每日推荐：0-1只（没有就空着）')
doc.add_paragraph('有效利好：国家政策/行业重磅/重大技术突破/美股相关涨>5%')
doc.add_paragraph('竞价高开<5%→买入 | 5-8%→看承接 | >8%→放弃')
doc.add_paragraph('止损：-4%硬止损')

doc.add_heading('2.3 每日执行时间线', level=2)
table = doc.add_table(rows=10, cols=2)
table.style = 'Light Grid Accent 1'
table.rows[0].cells[0].text = '时间'; table.rows[0].cells[1].text = '动作'
timeline = [
    ('09:20', '竞价扫描 + 策略C检查'),
    ('10:00', '大盘环境定调 + GATE 0'),
    ('11:30', '上午盘面复盘'),
    ('13:30', '轮动板块初筛（策略A）'),
    ('14:00', '消息面扫描'),
    ('14:15', '技术面验证'),
    ('14:20', '个股筛选（策略A+B）'),
    ('14:25-14:35', '策略A执行窗口 ⭐'),
    ('14:40-14:50', '策略B执行窗口'),
]
for i, (t, a) in enumerate(timeline):
    table.rows[i+1].cells[0].text = t
    table.rows[i+1].cells[1].text = a

doc.add_heading('2.4 硬性风控规则', level=2)
doc.add_paragraph('最长持有2天，第2天14:45强制清仓')
doc.add_paragraph('单只≤25%，单板块≤40%，同时持仓≤3只')
doc.add_paragraph('到止损价必须卖，不补仓摊平')
doc.add_paragraph('GATE 0>80时总仓位≤20%')
doc.add_paragraph('综合评分<5禁止推荐')

doc.add_heading('2.5 6/17核心教训', level=2)
doc.add_paragraph('发现异动信号后，必须在24小时内决策，超过48小时→放弃该信号')
doc.add_paragraph('每天13:00自动扫一遍全市场放量异动')
doc.add_paragraph('连续错过3天→禁止追高，改为等回调-5%再埋伏')

doc.add_page_break()

# ============================================================
# CHAPTER 3: 诸葛亮
# ============================================================
doc.add_heading('🏯 第三章：诸葛亮计划 v7.0 — 独立牛股筛选系统', level=1)
doc.add_heading('3.1 核心定位', level=2)
doc.add_paragraph('版本：v7.0 | 更新：2026-06-23 12:30')
doc.add_paragraph('定位：从"旭光模仿秀"升级为"可复制的独立牛股筛选模型"')
doc.add_paragraph('核心原则：宁缺毋滥（活跃池最多3只）| 量化优先 | 数据说话')

doc.add_heading('3.2 牛股样本库', level=2)
doc.add_paragraph('正式入库8只，参考入库3只')
doc.add_paragraph('覆盖板块：军工电子、半导体材料、PCB、光通信、新材料')
doc.add_paragraph('平均30日涨幅：+100% | 平均涨停次数：4.9次')

doc.add_heading('3.3 牛股DNA标准（5大量化维度）', level=2)

table = doc.add_table(rows=6, cols=3)
table.style = 'Light Grid Accent 1'
table.rows[0].cells[0].text = '维度'
table.rows[0].cells[1].text = '量化标准'
table.rows[0].cells[2].text = '权重'
dna_rows = [
    ('维度1：逆势强度', '个股N日涨幅 - 板块涨幅 > 30%', '30分（必过）'),
    ('维度2：独立性', '大盘跌日抗跌 + 板块跌不跟 + 领涨 ≥2分', '25分（必过）'),
    ('维度3：资金异常', '启动前5日均量>20日均量2倍+涨幅<5% ≥2分', '20分'),
    ('维度4：筹码集中', '股东人数环比减少>15%', '15分'),
    ('维度5：龙虎榜', '近30日有机构净买入>1000万', '10分'),
]
for i, (d, s, w) in enumerate(dna_rows):
    table.rows[i+1].cells[0].text = d
    table.rows[i+1].cells[1].text = s
    table.rows[i+1].cells[2].text = w

doc.add_paragraph('')
doc.add_paragraph('硬性通过：维度1+维度2同时通过 → 进入候选')
doc.add_paragraph('总分公式：100分制（30+25+20+15+10）')

doc.add_heading('3.4每日3步流程', level=2)
doc.add_paragraph('第1步：全市场量化初筛（15分钟）— 拉取全A股主板数据，按维度1-2批量打分，前20名进入初筛')
doc.add_paragraph('第2步：精选+逻辑验证（20分钟）— 深度分析前10只，验证独立逻辑，基本面排查，反共识检查')
doc.add_paragraph('第3步：候选池更新+交接（5分钟）— 最终选0-3只进入活跃池，不够3只就空着')
doc.add_paragraph('')
doc.add_paragraph('活跃池：3只上限，宁空勿滥 | 验证池：不限，实盘赚钱验证过的')
doc.add_paragraph('持仓周期：最短5个交易日，最长20个交易日')

doc.add_heading('3.5 候选池分层', level=2)
doc.add_paragraph('🟢 活跃池 — 上限3只，全部满足5条DNA标准+逻辑验证通过')
doc.add_paragraph('🟡 验证池 — 不限，汉武帝实盘验证赚钱+逻辑仍存的')
doc.add_paragraph('🔵 观察池 — 不限，初筛通过但未达活跃池标准')

doc.add_heading('3.6 6/17核心教训', level=2)
doc.add_paragraph('有独立走强DNA的票（旭光）→ 多拿，卖飞了+70%')
doc.add_paragraph('无独立走强DNA的票（完美）→ 早砍，死扛了-16.7%')
doc.add_paragraph('核心规则：截断亏损，让利润奔跑')

doc.add_page_break()

# ============================================================
# CHAPTER 4: 秦始皇
# ============================================================
doc.add_heading('🏛️ 第四章：秦始皇计划 v1.0 — 宏观资金配置系统', level=1)
doc.add_heading('4.1 核心定位', level=2)
doc.add_paragraph('版本：v1.0 | 建立：2026-06-23 15:33')
doc.add_paragraph('定位：三大短线系统管"买什么"（战术），秦始皇管"配多少、什么时候收"（战略）')
doc.add_paragraph('核心职能：宏观判断 | 资金配置 | 仓位管理 | 风险控制')

doc.add_heading('4.2 四大核心原则', level=2)
doc.add_paragraph('原则1：钱要在主线上')
doc.add_paragraph('  市场热点在哪，钱就在哪。不要在冷门票上重仓。')
doc.add_paragraph('  错误案例：完美世界（游戏/冷门）仓位34% → 亏-16.7%，拖累-7,371')
doc.add_paragraph('')
doc.add_paragraph('原则2：不要用赚热点的钱补冷门的窟窿')
doc.add_paragraph('  错：热门赚+5%（仓位小），冷门亏-5%（仓位大）→ 总账亏')
doc.add_paragraph('')
doc.add_paragraph('原则3：大盘环境决定仓位上限')
doc.add_paragraph('  🟢 牛市/主线明确 → 仓位80-100%')
doc.add_paragraph('  🟡 震荡/分化 → 仓位30-50%')
doc.add_paragraph('  🔴 调整/恐慌 → 仓位10-20%')
doc.add_paragraph('')
doc.add_paragraph('原则4：胜率 vs 赔率')
doc.add_paragraph('  正确：高胜率(>60%)+高赔率(>1:2) = 赚钱')
doc.add_paragraph('  错误：低胜率(<40%)+低赔率(<1:1) = 亏钱')

doc.add_heading('4.3 每日收盘检查清单', level=2)
doc.add_paragraph('□ 大盘环境评估（GATE 0级别）')
doc.add_paragraph('□ 当前主线板块是什么')
doc.add_paragraph('□ 主线板块处于什么阶段（启动/主升/高潮/退潮）')
doc.add_paragraph('□ 我的仓位是否符合当前环境')
doc.add_paragraph('□ 我的持仓是否在主线上')

doc.add_heading('4.4 仓位置换规则', level=2)
doc.add_paragraph('冷门票亏损>10% → 检查原因 → 板块问题减50% / 大盘问题减70% / 基本面问题清仓')
doc.add_paragraph('热门票盈利>10% → 设置移动止盈（从最高点回落5%就卖）')

doc.add_heading('4.5 资金配置模板', level=2)
doc.add_paragraph('大盘环境：_____ | 当前仓位：_____% | 建议仓位：_____%')
doc.add_paragraph('主线板块：_____（仓位≥70%） | 次线板块：_____（仓位≤20%） | 冷门板块：_____（仓位≤10%）')

doc.add_heading('4.6 经典案例：6/17分水岭', level=2)
doc.add_paragraph('问题：重仓冷门票（完美34%）+ 轻仓热门票（旭光已卖飞）+ 大盘环境变化未调整仓位')
doc.add_paragraph('结果：从盈利+3,000到亏损-10,000 = -13,000')
doc.add_paragraph('教训："冷门票重仓是亏钱的根源"，"大盘环境变了仓位必须跟着变"')

doc.add_page_break()

# ============================================================
# CHAPTER 5: 协同工作流
# ============================================================
doc.add_heading('📋 第五章：四系统协同工作流', level=1)
doc.add_heading('5.1 系统分工', level=2)

table = doc.add_table(rows=5, cols=3)
table.style = 'Light Grid Accent 1'
table.rows[0].cells[0].text = '系统'
table.rows[0].cells[1].text = '职能'
table.rows[0].cells[2].text = '输出'
coop = [
    ('🦁 汉武帝', '短线快打执行', '每日交易清单'),
    ('🐉 刘彻', '轮动埋伏+情绪溢价', '策略A/B/C推荐'),
    ('🏯 诸葛亮', '独立牛股DNA筛选', '活跃池3只'),
    ('🏛️ 秦始皇', '宏观+资金配置', '仓位+风控建议'),
]
for i, (s, f, o) in enumerate(coop):
    table.rows[i+1].cells[0].text = s
    table.rows[i+1].cells[1].text = f
    table.rows[i+1].cells[2].text = o

doc.add_heading('5.2 日间协同流程', level=2)
doc.add_paragraph('09:20 — 刘彻策略C（隔夜消息竞价）')
doc.add_paragraph('10:00 — 秦始皇（大盘环境定调）+ 汉武帝（GATE 0）')
doc.add_paragraph('11:30 — 刘彻策略A初筛（上午板块复盘）')
doc.add_paragraph('13:30 — 刘彻策略A（轮动板块四维度）+ 诸葛亮（全市场DNA扫描）')
doc.add_paragraph('14:00-14:15 — 刘彻技术面验证+消息扫描')
doc.add_paragraph('14:25-14:35 — 汉武帝/刘彻策略A（尾盘执行窗口）')
doc.add_paragraph('14:40-14:50 — 刘彻策略B（情绪溢价执行）')
doc.add_paragraph('15:00 — 秦始皇（收盘仓位检查）+ 诸葛亮（候选池更新）')
doc.add_paragraph('20:00 — 刘彻策略C（隔夜消息跟踪）')

doc.add_heading('5.3 周度流程', level=2)
doc.add_paragraph('周一：诸葛亮候选池全量重建')
doc.add_paragraph('周三：诸葛亮候选池半量更新')
doc.add_paragraph('周五：诸葛亮全面评估+秦始皇仓位检查')
doc.add_paragraph('周日：四系统自检+经验教训更新')

doc.add_page_break()

# ============================================================
# CHAPTER 6: 核心教训
# ============================================================
doc.add_heading('📖 第六章：核心教训与历史复盘', level=1)
doc.add_heading('6.1 五大死亡逻辑', level=2)
doc.add_paragraph('💀 死亡一：滞后追新闻 — 当天新闻当天买的票不碰')
doc.add_paragraph('💀 死亡二：评分无视 — 评分<5强制放弃')
doc.add_paragraph('💀 死亡三：安全陷阱 — 选龙头不选跟风杂毛')
doc.add_paragraph('💀 死亡四：仓位失衡 — 单票>25%禁止新开')
doc.add_paragraph('💀 死亡五：尾盘不执行 — 14:30到点就挂单')
doc.add_paragraph('💀 死亡六：短线改长线 — 满2天不走=违反顶层铁律')
doc.add_paragraph('💀 死亡七（v8.0新增）— 时序滞后：买入信号来自今天=作废')

doc.add_heading('6.2 6/17分水岭复盘', level=2)
doc.add_paragraph('核心问题：')
doc.add_paragraph('① 卖飞了最强的（旭光28卖→48涨，少赚+70%）')
doc.add_paragraph('② 死扛了最弱的（完美13.9→11.45，亏-16.7%）')
doc.add_paragraph('③ 追高了最晚的（楚江第4天追→次日跌-9.3%）')
doc.add_paragraph('净亏损：从+3,000到-10,000 = -13,000')

doc.add_heading('6.3 核心操作原则', level=2)
doc.add_paragraph('所有分析必须先拉数据再给结论，禁止凭记忆回答')
doc.add_paragraph('所有系统必须基于预判型架构，解释型思维已废除')
doc.add_paragraph('所有交易分析必须附技能清单，缺技能不出分析')

doc.add_heading('6.4 板块持仓规则（规则F）', level=2)
doc.add_paragraph('每个板块最多持有1只，机器人板块最多3只')
doc.add_paragraph('总账户上限6只')
doc.add_paragraph('机器人3只合计≤总仓位40%')
doc.add_paragraph('单只票≤总仓位25%')

# Save
doc.save('/Users/lyu/Desktop/A股四大交易系统_完整文档_v1.0.docx')
print('✅ 文档已保存到桌面：A股四大交易系统_完整文档_v1.0.docx')
