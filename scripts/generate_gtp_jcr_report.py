#!/usr/bin/env python3
"""Generate GTP→JCR comprehensive review report (.docx)"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import datetime

doc = Document()

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

def rating_bar(score, max_score=10):
    filled = int(score)
    unfilled = max_score - filled
    bar = '█' * filled + '░' * unfilled
    return f'{bar}  {score}/{max_score}'

# ======================
# TITLE
# ======================
title = doc.add_heading('GTP论文 · 李世民+唐太宗+Nature 终审报告', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

bold(f'日期：{datetime.date.today().strftime("%Y-%m-%d")}')
para('论文：Game-Triggered Pilgrimage: Visual Practices at Buddhist Sacred Sites Following the Release of Black Myth: Wukong')
para('目标期刊：Journal of Contemporary Religion (Taylor & Francis, SSCI)')
para('分析框架：李世民五层评估 + 唐太宗技能交叉验证 + Nature写作审核')
para('评估版本：投稿前修订稿（2026-07-07）')

doc.add_page_break()

# ======================
# 1. 李世民五层评估
# ======================
h('第一部分：李世民五层评估', 1)
para('按照李世民科研管理体系的五层框架，从文献管理到投稿策略逐层评估。')

# Layer 1
h('第一层：文献管理 📚 — 评分：9.5/10', 2)
para('参考文献约60条，覆盖完整且学科分布合理：')
tbl(
    ['文献集群', '核心学者', '覆盖度', '评注'],
    [
        ['朝圣研究', 'Turner & Turner, Eade & Sallnow, Coleman, Reader, Pasura', '★★★★★', '从经典到最新de-centring turn全覆盖'],
        ['媒体朝圣', 'Couldry, Reijnders', '★★★★★', '核心对话对象，批判性引述而非罗列'],
        ['内容旅游 (seichi junrei)', 'Yamamura, Seaton, Tan, Matsuyama, Nuradi', '★★★★★', '日语+中文+英文三语覆盖'],
        ['数字宗教', 'Campbell, Campbell & Evolvi, Campbell & Grieve', '★★★★☆', '核心理论来源，可补Campbell & Tsuria 2022'],
        ['媒介化理论', 'Hjarvard, Couldry & Hepp, Lövheim & Hjarvard', '★★★★★', '跟Lövheim & Hjarvard 2019自我修正的对话尤其出色'],
        ['算法平台', 'Bucher, Gillespie, van Dijck et al.', '★★★★☆', '平台研究部分引用到位，非核心故够用'],
        ['中国宗教/数字文化', 'Chau, Goossaert & Palmer, Liu et al., Xie, Zhang, Wang et al.', '★★★★★', '中国语境文献充足，与JCR重视非西方context对齐'],
    ]
)

# Layer 2
h('第二层：理论构建 🏗️ — 评分：9/10', 2)

h('GTP概念的原创性', 3)
para('GTP被明确定义为三个构成要素：trigger（数字游戏发布作为文化事件）、amplification（社交媒体算法分发）、object（真实宗教圣地）。这个概念不是简单"媒体朝圣+数字宗教"的并置——Table 1（五维对比表）清楚展示了GTP与Media Pilgrimage、Contents Tourism、Digital Religion在object/trigger/spatial pattern/practice form/relation to sacredness五个维度的本质差异。')

h('理论对话的三重推进', 3)
bullet('对Couldry/Reijnders媒体朝圣：挑战"secular premise"——当朝圣对象本身就神圣时，媒体中介的工作是negotiation而非creation')
bullet('对contents tourism：挑战"concentration assumption"——游戏不是单文本→单地点，而是多省份网络化触发')
bullet('对Hjarvard媒介化理论：提供"banal religion"命题的视觉边界案例——popular media entry不必然displace宗教意义（40%共现率）')

h('潜在审稿攻击点与防御', 3)
bullet('攻击："GTP只是给已有现象贴了新标签"')
para('→ 防御：§2.2.4和Table 1已系统性展示了GTP在五个维度上均不可被既有概念覆盖。这不是"换个名字"——Contents Tourism不处理游戏触发，Media Pilgrimage不处理既有神圣空间，Digital Religion不处理offline body performance。')
bullet('攻击："为什么不是game-induced tourism而非叫pilgrimage？"')
para('→ 防御：§1已明确——研究的是embodied practices at sacred sites，不是旅游人数。关键证据是palms-joined gesture（宗教身体实践）+ 视觉共现。如果是纯旅游，不会出现40%共现率。')
bullet('攻击："视觉数据不能证明朝圣者的motivation"')
para('→ 防御：你已经在摘要、§4.3、§5.4、§5.5、§6重复声明了5次。防御力足够。')

# Layer 3
h('第三层：方法论 📐 — 评分：8.5/10', 2)

tbl(
    ['维度', '评分', '评注'],
    [
        ['案例选择', '9/10', '两个标准明确：非虚构宗教圣地 + 九个月时间窗口。§3.1理由充分'],
        ['数据收集', '8/10', '616张图片规模合适；hashtag搜索策略合理。减分：缺metadata（时间戳/地理位置/like数）——你已在§1和§5.5诚实声明'],
        ['编码方案', '9/10', '三大类13维度+grounded theory开发+三轮迭代。编码框架清楚'],
        ['信度', '9.5/10', "Cohen's κ = 0.83 (body) / 0.82 (game elements) ——远超0.70阈值。独立双盲编码+预编码训练。方法论教科书级"],
        ['伦理', '9.5/10', '公共数据+双伦理控制（面部模糊+不展示原始图片）——JCR对宗教研究对象的伦理很敏感，你的处理会加分'],
        ['三角验证', '7/10', '只有视觉数据，无访谈/观察。你在§3和§5.5已诚实承认。定性审稿人会接受，量化审稿人可能追问。整体可接受与JCR的定性传统'],
    ]
)

# Layer 4
h('第四层：写作与修改 ✍️ — 评分：9/10', 2)

h('段落控制力', 3)
para('全篇段落都遵循"one paragraph, one message"原则。举例：')
bullet('§2.1.2第一段：定义Media Pilgrimage → 第二段：secular premise → 第三段：这个premise在GTP案例中失效。三段层层递进，没有信息堆砌')
bullet('§2.2.2最后一段："The visual hybridity documented here...provides new empirical evidence for this debate."——用一句话将整节的理论铺垫收束到你的实证贡献上，高效')

h('过渡句质量', 3)
para('全篇几乎每个section结尾都有一条向前推进的过渡，而不是"接下来讨论XX"的机械连接：')
bullet('§2.1.3末 → §2.2："These frameworks...situate pilgrimage within the broader dynamics of digital religion, mediatisation, and algorithmic platforms."')
bullet('§4.2末 → §4.3："Building on the four types, one phenomenon merits dedicated discussion."')

h('Nature写作标准检查', 3)
tbl(
    ['Nature标准', '状态', '说明'],
    [
        ['Claim-evidence对齐', '✅', '每个claim都能在数据中找到对应。4.3共现→5.2 media pilgrimage对话；4.4 site-sensitive→5.4 agency论证'],
        ['边界声明', '✅', '反复声明"visual≠motivation"；§1提前声明metadata缺失的scope限界'],
        ['动词校准', '✅', 'show/demonstrate/suggest/indicate/prove——推测性发现用suggest/indicate，统计证据用demonstrate/show'],
        ['无em dash滥用', '✅', '通篇无过度使用破折号'],
        ['句子长度控制', '✅', '平均句子在15-25词，超过30词的句子极少且必要'],
    ]
)

h('中文→英文质量', 3)
para('英文写作流畅自然，无中式英语（Chinglish）痕迹。Hedging得当。')


# Layer 5
h('第五层：投稿策略 🎯 — 评分：9/10', 2)

h('JCR适配度分析', 3)

tbl(
    ['适配维度', '评分', '证据'],
    [
        ['主题匹配', '★★★★★', '朝圣研究（Turner, Eade & Sallnow, Coleman, Pasura）是JCR的核心领域。GTP是现代朝圣的新形态，直接继承JCR的学术传统'],
        ['理论对话', '★★★★★', 'Campbell, Hjarvard, Couldry都在JCR发表过或与JCR作者群高度重叠'],
        ['非西方语境', '★★★★★', '中国案例+佛教圣地+社交媒体朝圣——JCR近年明显重视非西方/非基督教的当代宗教实践（Pasura 2023刊于JCR就是证据）'],
        ['方法论', '★★★★☆', '视觉内容分析在宗教学期刊中接受度在提高，但仍有审稿人偏好访谈/民族志。你的ethical disclosure和自反性声明会帮助缓解此担忧'],
        ['"published in this journal"', '★★★★★', 'Pasura (2023)确实是JCR发的。你引用它是直接向编辑展示你了解JCR的对话传统'],
    ]
)

h('投稿时机', 3)
bullet('GTP是一个紧跟时事的研究对象（黑神话悟空2024年8月发布），但你的理论贡献不依赖时效性——朝圣研究的de-centring turn和数字宗教的媒介化命题是长期存在的学术对话')
bullet('建议现在投——游戏发布已经一年，有足够的时间距离做学术分析，同时主题仍然新鲜')

doc.add_page_break()

# ======================
# 2. 唐太宗交叉验证
# ======================
h('第二部分：唐太宗技能交叉验证', 1)

h('纸面审查（paper-summarize）→ 投稿读法模拟', 2)
para('如果我是JCR编辑，打开这篇稿子会看到什么：')

h('第一页信号', 3)
bullet('标题Game-Triggered Pilgrimage — 如果我是JCR编辑，朝圣+游戏+数字平台，三个词都在我的期刊scope里')
bullet('摘要开头：发行日期+销售数据→旅游数据→社会学的embodied practice→三特征→GTP定义→四类型→40%共现→三个理论贡献')
bullet('读完摘要已经知道：a) 新概念是原创的 b) 有实证支撑 c) 理论边界清楚')

h('逻辑链完整性', 3)
para('全篇有一条非常清晰的逻辑链：')
para('Secular premise/Concentration assumption的识别（§2.1）→ 数字宗教/媒介化/算法的理论资源（§2.2）→ 整合为GTP的理论位置（§2.2.4+Table 1）→ 三个RQ（§1末）→ 四类型+共现+site-sensitive（§4）→ 三重理论对话（§5.1-5.4）')
para('这条链上没有断裂。每一个结论都能追溯到对应的RQ和对应的数据段。')

h('对抗式审查（paper-review）→ 五个维度', 2)

tbl(
    ['维度', '评估', '风险', '评注'],
    [
        ['贡献充分性', '🟢 PASS', '低', 'GTP概念的原创性已在Table 1中充分展示。对media pilgrimage的secular premise批判和mediatisation的visual boundary case都是独立贡献'],
        ['写作清晰度', '🟢 PASS', '低', '段落控制力强，术语一致，RQ→结果→讨论的对应关系清晰'],
        ['证据强度', '🟢 PASS', '低', '616样本+κ=0.83+四类型+共现+site-sensitive，三重发现各有独立数据段支撑。limitations已诚实声明'],
        ['评估完整性', '🟢 PASS', '极低', '负面案例（Frontal-Pose类型7.5%）、方法论局限、因果推断边界的诚实处理都到位'],
        ['方法合理性', '🟢 PASS', '低', '视觉内容分析对"what types of visual practice"的RQ是合适的方法。不能说没有访谈是缺陷——你的RQ就是关于visual practice的'],

    ]
)

h('Nature写作审核（nature-polishing）', 2)

tbl(
    ['核查项', '状态', '说明'],
    [
        ['Abstract: context→gap→approach→results→implication', '✅', '遵循标准pattern，包含定量细节（40%、616张）'],
        ['Introduction: field scale→bottleneck→gap→present study', '✅', '§1从游戏发布→旅游数据→embodied practice→三特征→理论缺口→GTP定义——完整的漏斗叙事'],
        ['Results narrative in past tense', '✅', '全篇Results用过去时，Discussion用现在时'],
        ['Discussion不重复Results figure-by-figure', '✅', '§5没有figure-by-figure的叙述，而是按三个理论脉络组织'],
        ['Conclusion: contribution→evidence→implication→boundary', '✅', '§6遵循标准结构，没有引入新数据'],
        ['Sentence length ≤30 words', '✅', '全文句子控制良好'],
        ['Hedging恰当', '✅', '"may","suggest","indicate"使用适当，没有unsupported certainty'],
        ['No em dash abuse', '✅', '']
    ]
)

doc.add_page_break()

# ======================
# 3. 识别的弱点和改进建议
# ======================
h('第三部分：识别的弱点 & 可选改进', 1)

h('🟡 微调项（不修不挡中稿）', 2)

bullet('§1末句 roadmap偏平淡 → 可改为更有张力的过渡（已在前面报告中给出建议）')
bullet('§5.5 Limitations可加第五项：编码框架中game-themed attire未区分子类（Hanfu vs cosplay），限制了对两种hybrid mode的精细分析')
bullet('Campbell & Tsuria (2022) 可考虑补到§2.2.1，作为networked religion框架的最新综述——但不补也不影响')

h('🟢 可以放心的地方', 2)

bullet('"published in this journal"——Pasura (2023)确实发表在JCR，这是精准的期刊适配信号，不是bug')
bullet('Table 1——五维对比表是JCR编辑会欣赏的结构化论证')
bullet('Fig 1-3——三张图都有，分辨率检查一下')
bullet('伦理声明——两个控制措施（面部模糊+不展示原始图片）对JCR读者群有说服力')
bullet('自反性——5次"visual≠motivation"声明，不会被审稿人抓到overclaim的把柄')

doc.add_page_break()

# ======================
# 4. 综合判定
# ======================
h('第四部分：综合判定', 1)

h('李世民五层综合', 2)
tbl(
    ['层次', '评分', '状态'],
    [
        ['📚 文献管理', '9.5/10', '🟢 优秀——60条引用，六集群完整覆盖，JCR学术传统精准对接'],
        ['🏗️ 理论构建', '9/10', '🟢 优秀——GTP概念原创，三重理论推进，Table 1防击穿'],
        ['📐 方法论', '8.5/10', '🟢 良好——κ=0.83过硬，伦理优秀。缺访谈是主要boundary（已诚实声明）'],
        ['✍️ 写作修改', '9/10', '🟢 优秀——Nature水准，段落控制力强，逻辑链完整无断裂'],
        ['🎯 投稿策略', '9/10', '🟢 优秀——JCR最优适配，非西方case+朝圣+数字宗教+媒介化四线对齐'],
    ]
)

h('总评分：9.1 / 10 🟢', 2)

para('')
para('五层加权平均：文献0.95 + 理论0.90 + 方法论0.85 + 写作0.90 + 投稿0.90 = 9.0/10')
para('（方法论的-0.15主要来自"只有视觉数据"——但这是研究设计的trade-off而非缺陷，且已充分声明。）')

h('可投性判定：✅ 可以投 — 无阻挡性缺陷', 2)

para('')
para('该论文已经达到Journal of Contemporary Religion的投稿标准。以下为其三个核心竞争力：')

para('')
h('核心竞争力一：GTP概念的系统性辩护', 3)
para('你不仅提出了一个新概念，而且在§2.2.4和Table 1中展示了它为什么不能被Media Pilgrimage、Contents Tourism、Digital Religion中任何一个覆盖。这不是"起个新名字"——五个维度的对比提供了结构化证据。')

h('核心竞争力二：三重发现的实证厚度', 3)
para('一个case study有三个独立发现层层递进——四类型（who）→ 视觉共现（how）→ site-sensitive variation（where）——而不是单个finding撑整篇论文。JCR的审稿人会看到empirical richness。')

h('核心竞争力三：与JCR学术传统的精准对接', 3)
para("Pasura (2023)的'de-centring pilgrimage towards non-Western contexts'直接为你的中国case提供了正当性；Campbell的数字宗教框架和Hjarvard的媒介化理论是你文献综述的核心支柱——而这些学者正是JCR的核心作者群。你的论文读起来就像是写给JCR读者群的。")

para('')
bold('结论：投。三位审稿人的预期：一位会欣赏GTP概念的理论原创性，一位会追问方法论（你的自反性声明已提前防御），一位会验证你对JCR学术传统的对话——你应该能过。')

para('')
p = doc.add_paragraph('— 李世民五层 + 唐太宗技能交叉验证 + Nature写作审核 · ')
p.runs[-1].font.size = Pt(9)
p.runs[-1].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

# Save
output_path = '/Users/lyu/Desktop/GTP_JCR_终审报告.docx'
doc.save(output_path)
print(f'✅ Report saved to: {output_path}')
