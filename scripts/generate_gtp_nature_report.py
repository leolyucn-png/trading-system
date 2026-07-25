#!/usr/bin/env python3
"""Generate Nature final audit report for GTP paper as .docx"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import datetime

doc = Document()
for s in doc.sections:
    s.top_margin = Cm(2.5)
    s.bottom_margin = Cm(2.5)
    s.left_margin = Cm(2.5)
    s.right_margin = Cm(2.5)

sty = doc.styles['Normal']
sty.font.name = 'Calibri'
sty.font.size = Pt(11)
sty.paragraph_format.space_after = Pt(6)
sty.paragraph_format.line_spacing = 1.15

def h(text, level=1):
    hd = doc.add_heading(text, level=level)
    for r in hd.runs:
        r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    return hd

def bold(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    return p

def para(text):
    return doc.add_paragraph(text)

def bullet(text):
    return doc.add_paragraph(text, style='List Bullet')

def tbl(headers, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, hd in enumerate(headers):
        t.rows[0].cells[i].text = hd
        for p in t.rows[0].cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(10)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            t.rows[ri+1].cells[ci].text = str(val)
            for p in t.rows[ri+1].cells[ci].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(10)
    doc.add_paragraph()
    return t

# TITLE
title = doc.add_heading('Nature 技能终审 — GTP论文', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
bold(f'日期：{datetime.date.today().strftime("%Y-%m-%d")}')
para('论文：Game-Triggered Pilgrimage: Visual Practices at Buddhist Sacred Sites Following the Release of Black Myth: Wukong')
para('目标期刊：Journal of Contemporary Religion (SSCI)')
para('审计依据：nature-writing/polishing skill references（style-guardrails / paper-review / paragraph-flow / article-architecture）')

doc.add_page_break()

# ===== 1. STYLE GUARDRAILS =====
h('一、Nature Style Guardrails 逐项审计', 1)
para('依据：style-guardrails.md 全部检查项')

h('1.1 Overclaim 禁词检查', 2)
tbl(
    ['禁词', '出现情况', '位置', '判定'],
    [
        ['prove', 'Abstract: "prove visually co-present in 40%"', 'Abstract/Results', '🟡 边界——非因果声明（是事实观察），但在Nature体例中建议软化以保证安全。建议改为 "are visually co-present"'],
        ['conclusively', '未出现', '—', '✅'],
        ['unprecedented', '未出现', '—', '✅'],
        ['best / superior', '未出现', '—', '✅'],
        ['first', '"China\'s first AAA..." — 非自夸，引用行业事实', '§1', '✅ 事实陈述，非overclaim'],
    ]
)

h('1.2 Academic Register 检查', 2)
tbl(
    ['检查项', '标准', '状态', '注释'],
    [
        ['Contractions', '不使用缩写形式', '✅', '全文零出现（无 don\'t, it\'s 等）'],
        ['Rhetorical questions', '学术论文不使用反问句', '✅', '全文零出现'],
        ['Spoken fillers', '无口语化填充词', '✅', '全文零出现'],
        ['Abbreviations first-use', '首次使用时定义', '✅', 'GTP在§1定义；seichi junrei在§2.1.3标注'],
        ['British spelling', '目标Nature体例用英式拼写', '✅', '全文一致：conceptualising, centred, characterised, organise'],
    ]
)

h('1.3 数字与单位 检查', 2)
tbl(
    ['检查项', '标准', '状态'],
    [
        ['Numerals for measurements', '测量用数字', '✅'],
        ['Space value-unit', '数值和单位间有空格', '✅（156%、≥45°、616 images）'],
        ['En dash for ranges', '范围用en dash', '✅（August 2024–May 2025、30–60 minutes）'],
    ]
)

h('1.4 句长检查', 2)
tbl(
    ['检查项', '标准', '状态'],
    [
        ['Average sentence length', '15-25词', '✅ 全文平均在合理范围'],
        ['Sentences > 30 words', '极为少见', '✅ 偶有但必要（如理论定义段落），无失控'],
        ['One proposition per sentence', '一句一义', '✅'],
    ]
)

para('')
bold('🟡 唯一需修改之处：')
para('§4.1: "...ranked first by a wide margin."')
para('→ "by a wide margin" 偏口语化。建议改为 "was the most frequent pose, appearing in 34.9% of images."')

doc.add_page_break()

# ===== 2. CLAIM-EVIDENCE =====
h('二、Claim-Evidence Alignment 对照', 1)
para('依据：paper-review.md — "Every major claim must be explicitly supported by evidence"')

tbl(
    ['核心 Claim', '证据段', '证据强度', '风险'],
    [
        ['GTP四类型区分（Game-Marker/Back-to-Camera/Palms-Joined/Frontal-Pose）', '§4.2 + Fig 1\n616张图按优先规则独立编码', '🟢 强', '低——互斥规则+robustness check已防御分类任意性'],
        ['palms-joined gesture和game elements视觉共现于40%的双手合十图像中', '§4.3 + Fig 2\n独立计数，不受四类型规则影响', '🟢 强', '低——这是全篇最"硬"的发现，统计事实'],
        ['朝圣者的视觉表现随场所类型系统变化（pagoda 28.9% vs sculpture 5.2% golden-hooped rod差异）', '§4.4 + Fig 3\n场所类型×游戏元素交叉分析', '🟢 强', '低——差异显著，提供了agency论证的核心证据'],
        ['挑战media pilgrimage的secular premise', '§5.2\n基于三个特征（非虚构场所+多省份网络+异质朝圣者）+ Table 1', '🟢 中强', '低——"迄今为止未被考察"的限定使claim有边界'],
        ['补充Hjarvard banal religion命题的视觉边界案例', '§5.4\n基于site-sensitive variation+共现+agency三重证据', '🟡 中', '中——审稿人可能追问：视觉共现≠意义共存？\n你已在摘要+§5.4+§5.5+§6重复防御'],
        ['GTP不能归约为Media Pilgrimage/Contents Tourism/Digital Religion中任何一个', 'Table 1\n五维对比表', '🟢 强', '低——结构化防御'],
    ]
)

doc.add_page_break()

# ===== 3. PARAGRAPH FLOW =====
h('三、Paragraph Flow Reverse Outlining', 1)
para('依据：paragraph-flow.md — "一个段落必须有单一message，第一句宣告message"')

h('3.1 §2.1.2 — Media Pilgrimage and the Secular Premise', 2)
para('[这是理论贡献的核心铺垫段落，审稿人会仔细读]')

tbl(
    ['段落', 'Topic Sentence / Message', '→ 推进', '判定'],
    [
        ['P1', 'Couldry & Reijnders定义media pilgrimage\n→ 粉丝访问影视取景地是一种世俗媒体仪式', '知识定位', '✅'],
        ['P2', '两者共享一个隐含前提：被媒介化的空间原来是secular的\n→ Downton Abbey / Friends 案例', '从描述→分析', '✅ 发现secular premise'],
        ['P3', '这个前提在GTP中失效——当对象本身是佛教圣地时，媒介的工作从creation变为negotiation\n→ 文献中无人考察', '从分析→理论缺口', '✅ → 直接收束§2.1的核心贡献'],
    ]
)
para('判定：三层递进——知识定位→分析→理论缺口。flow无可挑剔。')

h('3.2 §4.2 — Typological Differentiation', 2)
para('[全篇实证核心，四类型定义]')

tbl(
    ['段落', 'Message', '判定'],
    [
        ['开头段', '四类型定义+互斥优先规则+reverse priority robustness check', '✅ 方法论透明——提前防御"类型划分arbitrary"的审稿攻击'],
        ['Type A', 'Game-Marker (51.6%) — 主动角色扮演，"从凝视到cosplay"', '✅ 扣回§1的heterogeneity'],
        ['Type B', 'Back-to-Camera (27.1%) — 含蓄变体，沉浸式构图', '✅ 与Type A形成谱系'],
        ['Type C', 'Palms-Joined (9.9%) — 宗教实践，非游戏表演', '✅ 与Type A形成分析性对比，为§4.3铺垫'],
        ['Type D', 'Frontal-Pose (7.5%) — 传统旅游照，非GTP特有', '✅ 反向证明GTP≠tourist behavior'],
        ['Residual', '3.9%未分类', '✅ 诚实——展示全覆盖而非选择性报告'],
    ]
)
para('判定：每段一个message，四类型逻辑分明。')

h('3.3 §5.4 — Pilgrim Agency and Algorithmic Platform Mediation', 2)
para('[Discussion的关键段落——论证GTP中朝圣者并非被动]')

tbl(
    ['段落', 'Message', '→ 推进', '判定'],
    [
        ['P1', '朝圣者不是算法操控的被动复制者——site-sensitive variation证明agency', '开启argument', '✅'],
        ['P2', 'Xiaohongshu确有同质化激励，但朝圣者按空间属性调整行为——pagoda 28.9% vs sculpture 5.2%', '证据支撑', '✅ 证据→解释'],
        ['P3', '这是对Hjarvard banal religion命题的边界案例补充：popular media entry不必然displace宗教意义', '收束到理论', '✅ 解释→理论贡献'],
        ['P4', '自反性：visual data≠motivation，这部分是基于inference', '诚实边界', '✅ 理论→boundary'],
    ]
)
para('判定：四段从证据→解释→理论→边界，完整闭环。')

doc.add_page_break()

# ===== 4. SECTION ARCHITECTURE =====
h('四、Section Architecture 检查', 1)
para('依据：article-architecture.md — 每个section的标准结构')

tbl(
    ['Section', 'Nature标准结构', '本文', '符合'],
    [
        ['Abstract', 'context → gap → approach → key result → implication → boundary', '✅ 逐项对齐：游戏发布→GTP概念→616编码→四类型+40%→挑战secular premise+banal religion→visual≠motivation', '✅'],
        ['Introduction', 'field scale → bottleneck → prior attempts → unresolved gap → present study', '✅ 游戏发布→旅游数据→embodied practice→三特征→三理论缺口→GTP定义→RQ', '✅'],
        ['Literature Review', '两段式+整合收束', '✅ §2.1 朝圣扩展 + §2.2 数字宗教/媒介化/平台 → §2.2.4 整合为GTP理论位置 + Table 1', '✅'],
        ['Methods', 'case → data → coding → reliability → ethics', '✅ §3.1-3.5', '✅'],
        ['Results', 'desc → typology → key finding → moderator/context', '✅ §4.1 描述→§4.2 类型→§4.3 共现→§4.4 site-sensitive', '✅'],
        ['Discussion', 'empirical → three dialogues → limitations', '✅ §5.1 实证特征→§5.2-5.4 三重对话→§5.5 限制', '✅'],
        ['Conclusion', 'contribution → evidence → implication → boundary', '✅ §6: GTP定义→三发现→核心论证→自反性声明→未来方向', '✅'],
    ]
)

doc.add_page_break()

# ===== 5. REFERENCES =====
h('五、参考文献审计', 1)

tbl(
    ['检查项', '状态', '说明'],
    [
        ['总引用数', '✅ ~60条', '对600样本的视觉分析论文充足'],
        ['DOI覆盖率', '✅ 100%', '所有期刊文章均带DOI——JCR审稿人会欣赏'],
        ['格式一致性', '✅', '统一作者-年份，无混用中英文格式问题'],
        ['JCR期刊引用', '✅', 'Pasura (2023) + Crome (2023) 均刊于JCR——精准对接'],
        ['核心学者覆盖', '✅', 'Turner & Turner / Eade & Sallnow / Campbell / Hjarvard / Couldry / Bucher / Reader / Coleman / Reijnders'],
        ['非西方学者', '✅', 'Yamamura / Tan / Seaton / Liu / Wang / Xie / Zhang / Chau / Geary & Shinde'],
        ['最新文献', '✅', '多篇2024-2026引用（Wright-Ríos 2024, Nuradi 2024, Tan 2024, Liu 2025, Wang 2025, Thelen 2025, Xiao & Zhang 2025, Miao 2026, Luong 2026）'],
        ['学科分布', '✅', '朝圣研究/媒体研究/宗教学/旅游学/平台研究/人类学——跨学科覆盖充分'],
    ]
)

doc.add_page_break()

# ===== 6. FINAL JUDGMENT =====
h('六、终审判定', 1)

h('须修改的：1项', 2)
tbl(
    ['#', '位置', '原文', '建议改为', '严重度', '耗时'],
    [
        ['1', 'Abstract', '"prove visually co-present in 40%"', '"are visually co-present in 40%"', '🟡 轻', '10秒'],
    ]
)

para('理由：Nature style-guardrails 将 "prove" 列为需标记词汇。该处非因果声明而是事实观察，改为 "are" 不影响意义，仅消除审稿人对overclaim的潜在感知。')

h('可忽略的：2项', 2)
tbl(
    ['#', '位置', '原文', '建议改为', '严重度', '耗时'],
    [
        ['2', '§4.1', '"ranked first by a wide margin"', '"was the most frequent pose, appearing in 34.9% of images"', '🟢 极轻', '10秒'],
        ['3', '§5.5', '缺：attire子分类limitation', '加一句："the game-themed attire code did not distinguish Hanfu from video-game cosplay, preventing finer analysis of the two hybrid modes"', '🟢 极轻', '1分钟'],
    ]
)

h('全通过的检查项汇总', 2)
bullet('✅ Overclaim检查：conclusively/unprecedented/best/superior/first 均无问题')
bullet('✅ Academic Register：零contractions、零反问句、零口语、缩写均首定义')
bullet('✅ British Spelling：全文一致')
bullet('✅ 数字与单位：numerals + en dash 100%合规')
bullet('✅ 句长：无失控长句')
bullet('✅ 一句话一义：全篇遵循')
bullet('✅ Claim-Evidence对齐：6个核心claim各有对应数据段，无悬空claim')
bullet('✅ Paragraph Flow反向提纲：3个关键段均通过one-message测试')
bullet('✅ Section Architecture：7个section均按Nature标准结构组织')
bullet('✅ 参考文献：DOI全覆盖+JCR对话+跨学科平衡+最新文献覆盖')

doc.add_page_break()

# ===== SUMMARY =====
h('综合评分与投前清单', 1)

tbl(
    ['维度', '评分', '状态'],
    [
        ['Nature Style Guardrails', '9.5/10', '🟢 仅prove一词可优化'],
        ['Claim-Evidence Alignment', '9.5/10', '🟢 六claim六证据'],
        ['Paragraph Flow', '10/10', '🟢 反向提纲全通过'],
        ['Section Architecture', '10/10', '🟢 七section标准对齐'],
        ['参考文献', '10/10', '🟢 完美'],
        ['综合', '9.8/10', '🟢'],
    ]
)

para('')
bold('投前最终检查：')
bullet('🔴 Abstract: 改 "prove" → "are" （10秒）')
bullet('🟢 £2-3: 可选优化（1-2分钟）')
bullet('🟢 Table 1: 已确认嵌入docx')
bullet('🟢 Figures 1-3: 已确认嵌入docx')
bullet('🟢 "published in this journal": ✅ 特指JCR，加分项')
bullet('🟢 References: DOI全覆盖')

para('')
bold('最终判定：Nature九项标准全过。改完"prove"后可直接投Journal of Contemporary Religion。')

para('')
p = doc.add_paragraph('— Nature auditing completed · nature-writing / nature-polishing skill references')
p.runs[-1].font.size = Pt(9)
p.runs[-1].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

output = '/Users/lyu/Desktop/GTP_Nature终审报告.docx'
doc.save(output)
print(f'✅ Saved: {output}')
