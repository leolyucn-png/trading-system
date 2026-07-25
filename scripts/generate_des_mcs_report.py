#!/usr/bin/env python3
"""Generate DES→MCS revision report as a formatted .docx file."""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import datetime

doc = Document()

# --- Page setup ---
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.15

# Helper: heading
def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    return h

def add_bold_para(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    return p

def add_para(text):
    return doc.add_paragraph(text)

def add_bullet(text, level=0):
    p = doc.add_paragraph(text, style='List Bullet')
    if level > 0:
        p.paragraph_format.left_indent = Cm(1.27 * (level + 1))
    return p

def add_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
    doc.add_paragraph()
    return table

# ===== TITLE =====
title = doc.add_heading('DES论文转投 Media, Culture & Society 修订分析报告', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

add_bold_para(f'生成日期：{datetime.date.today().strftime("%Y-%m-%d")}')
add_para('分析框架：唐太宗过程 v3.0（paper-summarize + paper-review + nature-writing + nature-polishing）')
add_para('目标期刊：Media, Culture & Society (Sage, SSCI Q1)')
add_para('上游数据：投稿NMS全英文字稿 / NMS desk reject反馈 / 唐太宗v2终审报告')

doc.add_page_break()

# ===== PART 1 =====
add_heading('第一部分：MCS vs NMS — 为什么MCS可能比NMS更对口', 1)

add_para(
    'NMS的desk reject给出的理由是 "theoretical contributions are not sufficiently developed"。'
    '这个判断需要放在学科语境里理解——NMS的核心审稿群体是平台研究和计算传播学者，'
    '他们期待的是对既有的平台研究/STS理论边界做出攻击性贡献。'
)

add_para('但你的论文实际上是一篇文化研究/媒体人类学论文，只是被包装在了平台研究的语言里。'
         '转投MCS不是"降级投稿"，而是去一个对论文真正属性更敏感的期刊。')

add_heading('两本期刊对同一篇论文的不同读法', 2)

add_table(
    ['维度', 'NMS审稿人会看到', 'MCS审稿人会看到'],
    [
        ['论文属性', '基础设施研究+平台研究的论文', '平台时代的文化分析论文'],
        ['理论对话对象', 'Bucher, Gillespie, Cotter → STS/平台研究', 'Couldry, Appadurai, Massey → 文化研究/媒介化理论'],
        ['核心审稿问题', '"DES和ANT/Assemblage有什么区别？"', '"DES揭示了平台时代文化相遇的什么新形态？"'],
        ['方法论', 'n=13偏少，缺量化验证', '数字民族志+四数据流三角验证=方法论亮点'],
        ['案例价值', '韩国书店作为"极端案例"', '韩国书店作为"文化现象的富矿"'],
        ['竞争优势', '中等：跟纯平台研究论文竞争', '较高：MCS的定性平台文化案例相对稀缺'],
    ]
)

add_heading('结论', 3)
add_para('同样的实证材料，MCS的审稿人会更宽容你的方法论选择（质性小样本），'
         '更欣赏你的叙事（文化意义的物质生产链），更期待你的理论贡献（平台时代文化相遇的新形态）。')

doc.add_page_break()

# ===== PART 2 =====
add_heading('第二部分：P0 — 必须重写的核心问题', 1)

# P0.1
add_heading('P0.1：理论框架从"STS/平台研究"转向"文化研究/媒介化"', 2)

add_para('【最大手术】你现在的§2文献综述用的是STS/平台研究框架。NMS的编辑觉得'
         '"你做平台研究但理论贡献不够深"。对于MCS，需要把框架转向文化分析和媒介化理论。')

add_heading('保留的现有对话', 3)
add_bullet('Cotter的"visibility game" — 保留但降级，从"理论框架核心"变为"分析工具"')
add_bullet('Goffman的互动仪式 — 保留，这是文化分析的经典资源')
add_bullet('Valentine的接触理论 — 保留，这是你的核心对话对象，MCS审稿人会认可')
add_bullet('Star & Ruhleder的基础设施 — 保留但降级，在MCS语境中"基础设施"是隐喻不是核心')

add_heading('必须新增的理论对话', 3)

add_table(
    ['理论', '学者', '对话方式'],
    [
        ['媒介化理论 (Mediatization)', 'Couldry & Hepp (2017)\nThe Mediated Construction of Reality',
         '平台如何"媒介化"线下相遇？DES是媒介化相遇的基础设施形态——不是媒体"再现"现实，而是媒体"生产"现实中的相遇'],
        ['文化流动/全球媒介景观', 'Appadurai (1996)\n"mediascapes"',
         '小红书构成了一个新的"媒介景观"，使韩国乡村进入中国年轻人的文化想象。'
         '这不是简单的"跨境旅游"，而是文化想象的跨国流动'],
        ['空间生产理论', 'Lefebvre (1991) · Massey (2005)\nFor Space',
         '平山书店不是"被消费的非场所"——它被小红书+中国访客+文在寅共同"生产"为一个有意义的文化空间。'
         '这是对Tan的"非场所制造"论的文化修正'],
        ['媒介物质性', 'Miller (2010) Stuff · Larkin\n（已引用）',
         '基础设施的物质性如何塑造文化实践——合影"快门节奏"、排队"装配线"都是物质编排的文化形式'],
    ]
)

add_heading('§2 文献综述的结构重构', 3)

add_table(
    ['现在（并列汇报式）', '建议改为（阶梯推进式）'],
    [
        ['2.1 平台可见性与算法的塑造逻辑', '2.1 算法可见性的文化政治\n→ 平台研究+Cotter+文化视角'],
        ['2.2 基础设施研究', '2.2 媒介化的相遇\n→ 接触社会学+Koch & Miles+媒介化理论'],
        ['2.3 接触社会学', '2.3 平台的物质生活\n→ 基础设施+平台都市主义+Lefebvre/Massey'],
        ['2.4 平台都市主义与景点建构', '2.4 DES：平台时代文化相遇的分析框架\n→ 你的理论贡献'],
    ]
)

add_para(
    '关键变化：新§2.1不再只讨论"平台如何塑造可见性"，而是"算法可见性如何参与文化生产"。'
    '新§2.2不再是Goffman/Valentine的独立汇报，而是追问"当相遇被平台中介后，经典接触理论需要什么修正"。'
    '新§2.3不再并列基础设施和都市主义，而是将它们整合为"平台的物质生活"——'
    '一个对MCS审稿人有天然吸引力的概念。'
)

# P0.2
add_heading('P0.2：DES概念在文化研究意义上重新锚定', 2)

add_para('【NMS拒稿的真正凶手】目前§2.5的DES概念被定性为：')

add_para('"not merely a superposition of the three theoretical trajectories but rather '
         'an analytical framework that transforms how each trajectory is deployed"')

add_para('这是STS/平台研究的逻辑（"整合框架""分析装置"）。对于MCS，DES需要被重新锚定。')

add_heading('修改方向', 3)

add_para('与其说DES是"理论框架的整合"，不如说DES是：')

add_bold_para('平台时代文化相遇的一种特定文化组织形态')

add_para('DES关心的核心问题变为：')

add_bullet('算法平台如何将不可预测的跨文化相遇 → 转化为可复制、可规模化、可持续的日常文化实践？')

add_para('在这个表述之下，四层结构的文化含义完全不同：')

add_table(
    ['DES层级', 'STS/平台研究版本（旧）', '文化研究版本（新）'],
    [
        ['算法分发', '可见性的技术基础设施', '文化想象的物质性生产者——算法不是"推送信息"，而是"建构能见"'],
        ['人类中介\n（留学生）', '系统接合器 (system coupler)', '跨文化调解者 (cultural mediators)——他们不是"传递信息"，而是"翻译文化"'],
        ['线下接待', '基础设施层', '仪式性空间的物质编排——"快门节奏""装配线"是文化表演的舞台装置'],
        ['跨境移动', '自组织协调', '日常化的朝圣实践——不是"通勤"，而是带有文化意义的身体仪式'],
    ]
)

add_para(
    '这个转向不需要改变任何实证材料——只是改变了理论解释的框架。'
    '而这些新的解释对MCS审稿人来说比STS版本天然更有说服力。'
)

# P0.3
add_heading('P0.3：标题和摘要的文化转向', 2)

add_heading('标题建议（三选一）', 3)

add_bullet('选项A（去DES，偏叙事）: Between Algorithm and Handshake: How a South Korean Rural Bookstore Became a Cross-Border Cultural Destination on Xiaohongshu')
add_bullet('选项B（保留DES，锚定文化生产）⭐推荐: The Distributed Encounter System: Algorithmic Mediation and the Cultural Production of Cross-Border Encounters in Rural South Korea')
add_bullet('选项C（偏文化地理）: "South Korea\'s Only 5A-Level Scenic Spot": Platform-Mediated Encounter and the Making of a Rural Cultural Destination')

add_bold_para('推荐选项B，理由：保留了DES概念品牌（不会丢失先前传播），但关键词从produce转向cultural production，锚定在文化研究领域。')

add_heading('摘要修改方向', 3)

add_para('现在的摘要开头是方法论导向（"Drawing on multi-sited digital ethnography..."），这是NMS标准写法。')

add_bold_para('MCS风格的摘要是文化现象导向：')

add_para(
    '"In the algorithmic platform era, what was once nearly impossible — a brief face-to-face encounter '
    'between an ordinary Chinese youth and a former foreign head of state — has become a predictable, '
    'scalable, routine cultural practice. This study examines how Xiaohongshu (Little Red Book), a Chinese '
    'lifestyle platform, transformed Pyeongsan Bookstore — a modest rural bookshop operated by former '
    'South Korean President Moon Jae-in — from an invisible village into a cross-border cultural destination '
    'that young Chinese users collectively dubbed \'South Korea\'s only 5A-level (free) scenic spot.\'..."'
)

doc.add_page_break()

# ===== PART 3 =====
add_heading('第三部分：P1 — 结构性和论证性修改', 1)

add_heading('P1.1：Discussion必须跟文化理论深度对话', 2)

add_para('现在§5.1.1-5.1.3的三条理论贡献对话对象全是平台研究和接触社会学。'
         'MCS审稿人会想知道你的发现对文化理论意味着什么。')

add_heading('需要新增的三段对话', 3)

add_table(
    ['新增对话', '来源', '核心内容', '字数'],
    [
        ['DES与媒介化理论', 'Couldry & Hepp (2017)\nHjarvard (2013)',
         '媒介化理论认为"现实通过媒介被建构"。DES展示了媒介化不仅建构人们对现实的认知，'
         '而且直接生产现实中的相遇——"你被算法推荐→你在小红书上看到平山书店→你飞过去→'
         '你握手→你发帖→你的帖子被别人看到"是一个完整的"媒介化→物质化→再媒介化"循环。'
         '这对媒介化理论是一个经验性拓展：媒介化不只发生在符号层面，它可以"具身化"。',
         '~300'],
        ['DES与空间生产', 'Lefebvre (1991)\nMassey (2005)',
         'Tan认为小红书的打卡制造的是"非场所"（流动的、去社会化的）。但你的案例证明打卡'
         '也可以制造"反-非场所"——一个被中国年轻人命名、投入情感、建立个人关联的乡村空间。'
         '这是Lefebvre式的"空间生产"在平台时代的变体：不是建筑师生产空间，是算法+身体+'
         '仪式共同生产空间。',
         '~250'],
        ['DES与文化流动', 'Appadurai (1996)\nHannerz (1996)',
         '小红书不是一个"中国的社交平台"，它是一个"跨国的媒介景观"。DES揭示了文化流动的'
         '一个新路径——不通过移民/贸易/旅游产业，而是通过平台的算法推荐→个体的短视频/笔记→'
         '身体的跨境移动→再生产的文化内容。这是一个"草根化"的文化全球化微观路径。',
         '~200'],
    ]
)

add_heading('P1.2：强化已有实证材料的文化分析深度', 2)

add_para('你的实证材料里有很多可以被文化理论强化的内容，目前处于"描述"而非"理论化"的状态：')

add_table(
    ['实证材料', '现在是什么', '可以成为什么\n（新增的文化理论解读）'],
    [
        ['"5A级景区"\n民间命名', '民间命名\n(folk naming)',
         '文化挪用与再语境化\n中国访客将中国官方旅游评级话语（5A）重新嵌入到韩国乡村空间——'
         '这不是玩笑，是文化分类体系（cultural taxonomy）的跨语境移植'],
        ['礼物经济', '仪式性注意力\n延长术',
         '微型文化外交\n茶/书法/熊猫文创不是"策略"——它们是中国文化身份的微型物质性输出。'
         '这是一个"礼物-回礼"的文化交换系统：总统的签名/握手是回礼，共同构成了一个完整的'
         '文化交换仪式'],
        ['合影构图\n的标准化', '基础设施输出\n标准内容',
         '视觉文化的物质决定性\n相机角度/站立位置/光线方向不是技术安排——'
         '它们是"视觉相遇"的文化语法。每张合影都是一次"文化可读性"的生产'],
        ['称呼光谱\n（总统/爷爷/kaka）', '访客类型差异',
         '去政治化的文化策略\n称呼不仅是类型学分类，是政治人物的"去威胁化/亲昵化"文化操作。'
         '"爷爷"将文在寅从政治人物重新分类为家庭角色，"kaka"将他纳入韩流文化语汇'],
    ]
)

doc.add_page_break()

# ===== PART 4 =====
add_heading('第四部分：P2 — 加分但不紧急', 1)

add_bullet('加入DES系统结构图（四层嵌套+四条文化轨迹）——之前唐太宗报告已有设计草稿')
add_bullet('加入方法论流程图（五场景→四数据流→四步骤）')
add_bullet('强化韩方视角缺失的limitation声明（已在之前唐太宗报告提出）')
add_bullet('补充3-5篇MCS近三年发表的相关论文作为引用——展示你了解这本期刊的学术传统')
add_bullet('Consider adding a short paragraph on researcher reflexivity in the cultural studies tradition (following Pink and sensory ethnography)')

doc.add_page_break()

# ===== PART 5 =====
add_heading('第五部分：NMS版 vs MCS版 逐项对比', 1)

add_table(
    ['维度', 'NMS版本（被拒稿的）', 'MCS版本（建议改后）'],
    [
        ['理论锚定', 'STS / 平台研究', '媒介化理论 / 文化研究'],
        ['理论贡献表述', '"整合三条脉络的分析装置"', '"平台时代文化相遇的特定组织形态"'],
        ['§2文献综述', '四节并列汇报', '三阶梯推进 → DES'],
        ['叙事逻辑', '四层基础设施协同运作', '意义的物质生产链：\n算法→想象→身体→仪式→再生产'],
        ['Discussion对话', '平台可见性/接触社会学/\n景点建构', '同上 +\n媒介化理论+空间生产+文化流动'],
        ['核心审稿问题', '"DES跟ANT有什么区别？"', '"算法平台如何重塑了\n跨文化相遇的文化逻辑？"'],
        ['方法论位置', '可能被视为弱点（小样本）', '可能被视为亮点（多数据流三角验证）'],
        ['竞争优势', '中等（挤在纯平台研究里）', '较高（MCS的定性文化案例稀缺）'],
    ]
)

doc.add_page_break()

# ===== SUMMARY =====
add_heading('执行优先级与预估时间', 1)

add_table(
    ['优先级', '任务', '位置', '预估耗时', '关键程度'],
    [
        ['🔴 P0.1', '理论框架 STS→文化研究转向\n重写§2文献综述', '§2全文', '~4-6小时', '不修=再次desk reject'],
        ['🔴 P0.2', 'DES概念文化重新锚定\n修改§2.5', '§2.5', '~2小时', '同上'],
        ['🔴 P0.3', '标题+摘要文化转向', 'Title+Abstract', '~1.5小时', '第一页即信号'],
        ['🟡 P1.1', 'Discussion增加三段文化理论对话\n（媒介化/空间/文化流动）', '§5', '~3小时', '大幅提升理论贡献厚度'],
        ['🟡 P1.2', '强化已有实证材料的文化分析深度\n（第4.2-4.4节）', '§4', '~2小时', '让实证材料的理论化更充分'],
        ['🟢 P2.1', '加入DES系统结构图', '§2.5或§4', '~1.5小时', '可视化提升可读性'],
        ['🟢 P2.2', '补充MCS相关文献引用', '§2 + §5', '~1小时', '展示期刊适配性'],
        ['🟢 P2.3', '韩方视角limitation声明', '§5.2或§6', '~20分钟', '已有设计草稿'],
    ]
)

add_para('')
add_bold_para('总预估工作量：P0约7.5-9.5小时 + P1约5小时 + P2约3小时 ≈ 15-18小时')

doc.add_page_break()

# ===== FINAL =====
add_heading('结语：一句话', 1)

add_para(
    'NMS的desk reject不是对论文质量的否定——它是对论文定位的否定：'
    '你写了一篇文化研究论文，但穿了一件平台研究的外衣，让平台研究的编辑觉得"理论贡献不够"。'
    '转投MCS不是退而求其次，而是让论文的本质身份找到对的主人。'
)

add_para('')
add_para(
    '同一个案例、同一批数据、同一个DES概念——只需要把理论锚点从"基础设施如何协同运作"'
    '转向"文化意义如何通过平台被物质化地生产"，NMS的"理论贡献不够"就变成了MCS的'
    '"有趣的文化分析案例"。这不是修辞游戏——这是学科对话对象的转换。'
)

add_para('')
p = add_para('— 唐太宗过程 v3.0 / nature-writing · ')
p.runs[-1].font.size = Pt(9)

# Save
output_path = '/Users/lyu/Desktop/DES_MCS_修订分析报告.docx'
doc.save(output_path)
print(f'✅ Report saved to: {output_path}')
