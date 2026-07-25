#!/usr/bin/env python3
"""Convert the GTP review markdown to a formatted Word document."""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import re

doc = Document()

# ── Page setup ──
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# ── Style helpers ──
style = doc.styles['Normal']
font = style.font
font.name = 'Arial'
font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def add_title(text, level=0):
    """Add a heading at a given level."""
    if level == 0:
        p = doc.add_heading(text, level=0)
    else:
        p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
    return p

def add_para(text, bold=False, italic=False, size=None, color=None, align=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    if align:
        p.alignment = align
    return p

def add_bullet(text, level=0, bold_prefix="", color=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run_b = p.add_run(bold_prefix)
        run_b.bold = True
        if color:
            run_b.font.color.rgb = color
        run = p.add_run(text)
    else:
        run = p.add_run(text)
        if color:
            run.font.color.rgb = color
    return p

def shade_cell(cell, color_hex):
    """Set background shading for a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_text(cell, text, bold=False, size=9, color=None, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = 'Arial'
    if color:
        run.font.color.rgb = color

def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        shade_cell(cell, "1A237E")
        set_cell_text(cell, h, bold=True, size=9, color=RGBColor(0xFF, 0xFF, 0xFF))
    # Data rows
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx+1].cells[c_idx]
            set_cell_text(cell, str(val), size=9)
            if r_idx % 2 == 1:
                shade_cell(cell, "F5F5F5")
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    return table

def add_separator():
    p = doc.add_paragraph()
    run = p.add_run("━" * 50)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    run.font.size = Pt(6)

# ── COVER SHEET ──
add_title("🏯 唐太宗v3.0 + 📚 李世民计划\n完整评审报告", level=0)

doc.add_paragraph()
add_para("Game-Triggered Pilgrimage: Visual Practices at Buddhist Sacred Sites\nFollowing the Release of Black Myth: Wukong", bold=True, size=12)
add_para("")
add_para("目标期刊: Journal of Contemporary Religion (SSCI Q1, Routledge)", italic=True)
add_para("评审时间: 2026-06-12 | 评审员: LEO 🦁", italic=True)
add_separator()

# ── SKILL LIST ──
add_title("🛠️ 技能清单", level=2)
skills = [
    "✅ paper-summarize — 论文骨架提取",
    "✅ paper-review — 五维拒稿风险评估 (7.45/10)",
    "✅ citation-audit — 参考文献审计",
    "✅ research-design — 方法论评估",
    "✅ deep-audit — 深度方法论审计",
    "✅ data-analysis — 数据结果评估",
    "✅ literature-scanner — 文献扫描",
    "✅ hypothesis-generator — 假说链梳理",
    "✅ academic-writing — 写作优化建议",
    "✅ diagram-maker — 图表优化建议",
    "✅ gap-to-topic — 投稿策略分析",
]
for s in skills:
    add_bullet(s)
add_separator()

# ═══════════════════════════════════════════════
# PHASE 1
# ═══════════════════════════════════════════════
add_title("Phase 1: 输入层", level=1)

# ① literature-scanner
add_title("① literature-scanner — 文献扫描评估", level=2)
add_para("评分: 7.5/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
add_para("")

add_para("已覆盖的三支柱：", bold=True)
pillars = [
    "✅ 媒体朝圣：Couldry (2003), Reijnders (2011) — 奠基扎实",
    "✅ 内容旅游：Yamamura (2015), Seaton et al. (2017), Tan (2024) — 充足",
    "✅ 数字宗教+媒介化：Campbell (2012, 2013, 2022), Hjarvard (2008-2013), Lövheim & Hjarvard (2019) — 完整",
    "✅ 中国数字宗教：Liu et al. (2025), Wang et al. (2025), Zhang (2017), Xie (2025) — 良好的在地覆盖",
]
for p in pillars:
    add_bullet(p)

add_para("")
add_para("关键缺失文献（P1级）：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
make_table(
    ["缺失领域", "具体文献", "为何重要"],
    [
        ["游戏-宗教交叉", "Campbell & Grieve (2014); Bainbridge (2013); Šisler et al. (2017)", "GTP核心是\"游戏触发宗教朝圣\"，却不引用该直接相关领域"],
        ["中国宗教社会学", "Goossaert & Palmer (2011); Chau (2006); Yang Fenggang系列", "JCR读者期待对中国佛教遗址制度背景的论述"],
        ["朝圣-数字摄影", "Hill-Smith (2011); Larsen (2005); Sontag (1977)", "强化视觉分析的符号学深度"],
    ],
    col_widths=[1.3, 2.5, 3.2]
)

add_para("与JCR对话评估：已引用Pasura (2023)和Crome (2023)，主动建立对话 ✅。但需警惕JCR审稿人认为论文\"更像媒体研究而非宗教研究\"的风险。", italic=True)
add_separator()

# ② hypothesis-generator
add_title("② hypothesis-generator — 理论假说链梳理", level=2)
add_para("评分: 7/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
add_para("")

add_para("显性假说（论文明确挑战）：", bold=True)
make_table(
    ["假说", "挑战对象", "证据", "清晰度"],
    [
        ["H1: 媒体朝圣对象\n可以是前传媒神圣空间", "Couldry/Reijnders\n世俗前提", "遗址为千年佛教圣地", "⚠️ 解构需更精细"],
        ["H2: 宗教实践与\n流行文化可视觉共存", "Hjarvard\n\"平庸宗教\"论", "40%合十图同时\n含游戏元素", "✅ 清晰"],
        ["H3: GTP非单一模式\n内在分化", "内容旅游\n\"统一实践\"假设", "4种类型+9.9%\n纯合十", "✅ 清晰"],
    ],
    col_widths=[1.8, 1.6, 1.8, 0.8]
)

add_para("")
add_para("隐性假说（可推导但未明确）：", bold=True)
for h in ["H4: 算法平台激励→视觉同质化但非完全决定", "H5: 多义性宗教空间 vs Turner的communitas", "H6: 游戏触发可形成\"网络化圣地\" vs 动漫\"单点模式\""]:
    add_bullet(h)

add_para("")
add_para("问题：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
problems_h = [
    "对Couldry/Reijnders\"世俗前提\"的解构不够精细——需更仔细的文本论证",
    "因果方向含混：数据证明关联而非触发",
    "缺少竞争假说：\"打卡文化\"解释未被系统讨论",
]
for p in problems_h:
    add_bullet(p, color=RGBColor(0xD3, 0x2F, 0x2F))

add_separator()

# ═══════════════════════════════════════════════
# PHASE 2
# ═══════════════════════════════════════════════
add_title("Phase 2: 分析层", level=1)

# ③ paper-summarize
add_title("③ paper-summarize — 论文骨架提取", level=2)
make_table(
    ["维度", "内容"],
    [
        ["核心论题", "提出GTP概念，论证数字游戏可触发宗教圣地朝圣，且视觉上表现为宗教虔敬与流行文化的共存"],
        ["方法", "视觉内容分析，N=616小红书图片，独立双编码(Kappa=0.82)，13维度三类别"],
        ["核心发现", "① 四种类型分化(Game-Marker 51.6%, Back-to-Camera 27.1%, Palms-Joined 9.9%, Frontal-Pose 7.5%)\n② 40%合十+游戏元素共存\n③ 站点敏感：金箍棒在塔/幢28.9% vs 雕塑5.2%"],
        ["核心贡献", "① GTP概念 ② 对\"平庸宗教\"的反向观察 ③ 非西方朝圣去中心化案例"],
        ["局限性", "无元数据(时间/地点/点赞)→无法做跨区域/时序/平台传播分析；视觉数据不能推断动机"],
    ],
    col_widths=[1.3, 5.7]
)
add_separator()

# ④ paper-review
add_title("④ paper-review — 五维拒稿风险评估", level=2)
add_para("综合评分: 7.45/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=12)

add_para("维度一：理论贡献（30%）— 7.5/10", bold=True)
for b in ["GTP概念原创，位于三个理论交叉点", "对Hjarvard\"平庸宗教\"的反向观察是重要贡献", "与中国青年宗教实践的最新趋势一致"]:
    add_bullet("✅ " + b)
for p in ["P1: GTP边界不清晰——可迁移性需论证", "P1: 对\"媒体朝圣=世俗前提\"的解构需更精细文本援引", "P1: 视觉共存到底是宗教性还是审美的？"]:
    add_bullet(p, color=RGBColor(0xE6, 0x5C, 0x00))

add_para("")
add_para("维度二：方法论严谨性（25%）— 7.0/10", bold=True)
for b in ["独立双编码是金标准", "N=616充分", "Kappa=0.82优秀", "伦理处理完整"]:
    add_bullet("✅ " + b)
add_para("P0必须修：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
for p in ["❌ 未报告各维度独立Kappa值 — 13维度信度可能差异巨大", "❌ 分类优先级规则人为抬高了Game-Marker比例(51.6%)"]:
    add_bullet(p, color=RGBColor(0xD3, 0x2F, 0x2F))

add_para("")
add_para("维度三：文献对话（15%）— 7.0/10", bold=True)
add_para("维度四：论证逻辑（15%）— 7.5/10", bold=True)
add_para("维度五：写作质量与投稿适配度（15%）— 8.5/10", bold=True)

add_para("")
add_para("⚠️ 拒稿风险：中等（约35-40%）", bold=True, color=RGBColor(0xE6, 0x5C, 0x00))
risks = [
    "(1) 方法论维度(per-dimension Kappa缺失+分类规则问题)",
    "(2) 理论声明与证据强度不匹配",
    "(3) JCR读者认知距离——太偏媒体研究，宗教核心性不够突出",
]
for r in risks:
    add_bullet(r)
add_separator()

# ⑤ citation-audit
add_title("⑤ citation-audit — 参考文献审计", level=2)
make_table(
    ["项目", "状态"],
    [
        ["总文献数", "~44条"],
        ["格式一致性", "✅ Taylor & Francis格式，基本符合"],
        ["DOI缺失", "⚠️ 部分书籍未提供DOI，建议统一补充"],
        ["访问日期缺失", "❌ P1：SCMP, TechNode, CGTN等新闻来源均未标注访问日期"],
        ["中文作者名不一致", "⚠️ 部分用拼音全名，部分用缩写"],
        ["核心文献缺失", "❌ P1：游戏-宗教交叉文献 + 中国宗教社会学文献"],
    ],
    col_widths=[1.8, 5.2]
)
add_separator()

# ⑥ research-design
add_title("⑥ research-design — 方法论评估", level=2)
add_para("评分: 7.5/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
make_table(
    ["维度", "评估", "评级"],
    [
        ["案例选择", "黑神话→小红书打卡是合理的信息丰富案例", "🟢"],
        ["数据收集", "990→616筛选流程清晰，9个月跨度充足，但未记录元数据是硬伤", "🟡"],
        ["编码方案", "13维度三类别合理，\"地点-身体-媒介\"三分框架清晰", "🟢"],
        ["信度", "双编码+Kappa=0.82优秀，但未报告per-dimension Kappa", "🟡"],
        ["伦理", "面部模糊+IRB+匿名化处理完整", "🟢"],
        ["局限性", "在论文中诚实充分标注", "🟢"],
    ],
    col_widths=[1.5, 4.2, 0.5]
)
add_separator()

# ⑦ deep-audit
add_title("⑦ deep-audit — 深度方法论审计", level=2)
add_para("评分: 7/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
add_para("核心问题：分类优先级规则", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
add_para("Figure 1规则：\"任何含游戏元素的图片优先归入Game-Marker\"。一张图片显示一个人穿着汉服+双手合十+站在游戏场景前→归入Game-Marker。这种规则的人为构造性后果未被充分讨论。")
add_para("P1建议：增加\"类型学稳健性检验\"——用不同的分类优先级重新计算比例。", italic=True)

add_para("")
add_para("其他深度问题：", bold=True)
for item in [
    "选择性报告：Kappa=0.82是总体值，其他11个维度频次未全部报告",
    "替代性解释：\"打卡文化解释\"未被充分讨论",
    "视觉→动机的推断：论文诚实标注局限性，但Discussion中理论声明有时超出证据强度",
]:
    add_bullet("⚠️ " + item)
add_separator()

# ═══════════════════════════════════════════════
# PHASE 3
# ═══════════════════════════════════════════════
add_title("Phase 3: 执行层", level=1)

add_title("⑧ data-analysis — 数据结果评估", level=2)
add_para("评分: 7.5/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
for b in ["结果呈现逻辑清晰：分布→类型→共存→站点敏感性", "百分比和频率报告充分", "Kappa=0.82支撑发现可靠"]:
    add_bullet("✅ " + b)
for p in ["P2: Figure 1/2/3标题需更自明", "P2: 建议补充交叉表(如Game-Marker在不同站点的分布)", "P2: 4.4节的\"站点-游戏元素关联\"缺乏统计检验"]:
    add_bullet("⚠️ " + p)
add_separator()

# ═══════════════════════════════════════════════
# PHASE 4
# ═══════════════════════════════════════════════
add_title("Phase 4: 辩论矩阵", level=1)

add_title("⑨ 矛盾点与修正优先级", level=2)
make_table(
    ["#", "矛盾/张力", "优先级", "修正建议"],
    [
        ["1", "总Kappa=0.82 vs 可能被低分类一致性维度拉低", "P0", "报告per-dimension Kappa"],
        ["2", "分类优先规则的人为构造 vs 类型学\"自然分化\"主张", "P0", "补充稳健性检验"],
        ["3", "理论声明('修正') vs 证据(关联非因果)", "P1", "弱化语言：corrects→extends/refines"],
        ["4", "游戏-宗教交互是核心 vs 不引用游戏-宗教文献", "P1", "补充Campbell & Grieve (2014)等"],
        ["5", "中国宗教遗址为核心 vs 缺失中国宗教社会学", "P1", "补充Goossaert & Palmer (2011)"],
        ["6", "\"站点敏感调整\"声明 vs 缺乏统计检验", "P2", "补充χ²检验"],
        ["7", "JCR是宗教期刊 vs 论文偏媒体/传播学", "P1", "加强宗教理论权重"],
    ],
    col_widths=[0.3, 2.5, 0.5, 2.7]
)
add_separator()

# ═══════════════════════════════════════════════
# PHASE 5
# ═══════════════════════════════════════════════
add_title("Phase 5: 输出层", level=1)

add_title("⑩ academic-writing — 写作优化建议", level=2)
add_para("评分: 8.5/10", bold=True, color=RGBColor(0x1A, 0x23, 0x7E), size=11)
add_para("结构评估：IMRaD结构完整，逻辑链清晰 ★★★★☆")
add_para("语言风格：英文接近母语水平，学术性强 ★★★★☆")

add_para("")
add_para("具体修改建议：", bold=True)
suggestions = [
    "Introduction信息密集段拆为2-3段",
    "Discussion 5.2的\"corrective\"语气改为\"extension/refinement\"",
    "术语统一：全文用\"Game-Marker Type\"而非\"Type A\"",
    "新闻来源补充访问日期",
    "中文作者名统一格式",
]
for s in suggestions:
    add_bullet("✏️ " + s)

add_para("")
add_title("⑪ diagram-maker — 图表优化建议", level=2)
make_table(
    ["现存图表", "建议"],
    [
        ["Figure 1 (类型分布)", "标题需更自明；分类规则从标题注移到正文"],
        ["Figure 2 (合十+游戏元素共存)", "补充子图：\"纯合十 vs 混合合十\"对照"],
        ["Figure 3 (站点-游戏元素关联)", "添加统计显著性标注"],
        ["新增建议", "类型×站点类型的列联表"],
        ["新增建议", "四种类型典型图片视觉对照"],
    ],
    col_widths=[2.5, 4.5]
)

add_para("")
add_title("⑫ reproducibility-stamp — 可复现性评估", level=2)
make_table(
    ["维度", "状态"],
    [
        ["数据可得性", "❌ 小红书图片无法公开分享(伦理+平台政策)"],
        ["编码方案", "✅ 13维度三类别已完整描述，可复现"],
        ["编码流程", "✅ 双编码+一致性比例报告完整"],
        ["分析代码", "N/A (视觉内容分析手工编码)"],
        ["综合", "作为定性-视觉研究，可复现性在合理范围内"],
    ],
    col_widths=[1.8, 5.2]
)
add_separator()

# ═══════════════════════════════════════════════
# 李世民计划
# ═══════════════════════════════════════════════
add_title("📚 李世民计划：投稿策略", level=1)

add_title("⑬ Journal of Contemporary Religion 适配度深度评估", level=2)

add_para("期刊画像", bold=True)
make_table(
    ["维度", "信息"],
    [
        ["出版商", "Routledge (Taylor & Francis)"],
        ["范围", "当代宗教现象、宗教变迁、新兴宗教运动"],
        ["方法偏好", "定性/民族志为主，接受定量/混合方法"],
        ["近3年热点", "数字宗教(↑)、去殖民化朝圣(↑)、中国宗教(↑)"],
        ["接受率", "~20% (估计)"],
        ["审稿周期", "3-6个月(首次决定)"],
        ["影响因子", "Q1 宗教研究"],
    ],
    col_widths=[1.5, 5.5]
)

add_para("")
add_para("适配度评分：7/10 ✅ 良好匹配", bold=True, size=11)
add_para("")
for p in ["论文引用了JCR近3年论文(Pasura 2023; Crome 2023)→主动对话",
          "中国宗教+数字宗教+青年实践 = JCR近年热点",
          "Pasura (2023)的\"de-centring pilgrimage\"号召与论文一致",
          "Crome (2023)的粉丝创作+宗教素养与论文交叉"]:
    add_bullet("✅ " + p)

add_para("")
add_para("风险点：", bold=True, color=RGBColor(0xE6, 0x5C, 0x00))
for r in ["论文理论对话70%在媒体/传播学，仅30%在宗教研究",
          "视觉内容分析在JCR极为罕见",
          "需让\"宗教\"而非\"游戏/媒体\"成为分析核心"]:
    add_bullet("⚠️ " + r)

add_para("")
add_title("封面信（Cover Letter）核心卖点", level=2)
for s in [
    "Original concept (GTP) at the intersection of digital religion, media pilgrimage, and platform studies",
    "First empirical documentation of visual co-presence of devotional gestures and game aesthetics",
    "Responds directly to Pasura's (2023, JCR) call for de-centring pilgrimage studies",
    "Non-Western case extends the 'banal religion' debate (Crome 2023, JCR)",
    "Visual content analysis with strong inter-coder reliability (κ=0.82)",
]:
    add_bullet(s)

add_para("")
add_title("推荐审稿人", level=2)
make_table(
    ["审稿人", "领域", "理由"],
    [
        ["Heidi Campbell (Texas A&M)", "数字宗教", "论文核心理论基础"],
        ["Stig Hjarvard (Copenhagen)", "媒介化+宗教", "论文核心挑战对象"],
        ["Stijn Reijnders (Erasmus)", "媒体朝圣", "论文核心对话对象"],
        ["Dominic Pasura (Aston)", "朝圣去中心化", "JCR已发，论文引用"],
        ["陈纳(香港中文大学)", "中国宗教社会学", "弥补中国宗教视角"],
    ],
    col_widths=[2.5, 1.5, 2.5]
)

add_para("")
add_title("投稿前检查清单（P0）", level=2)
checks = [
    "□ 补充per-dimension Kappa值",
    "□ 补充分类优先规则的稳健性检验",
    "□ 补充游戏-宗教交叉文献(3-5条)",
    "□ 补充中国宗教社会学文献(2-3条)",
    "□ 补充新闻来源的访问日期",
    "□ Discussion弱化\"corrective\"语气为\"extension/refinement\"",
    "□ 统一中文作者名格式",
    "□ 拆分Introduction信息密集段落",
]
for c in checks:
    add_bullet("📋 " + c)

add_separator()

# ═══════════════════════════════════════════════
# FINAL SCORE
# ═══════════════════════════════════════════════
add_title("🎯 综合评分与最终清单", level=1)

make_table(
    ["维度", "评分", "解读"],
    [
        ["理论原创性", "8.0", "GTP概念原创，交叉定位合理"],
        ["方法论", "7.0", "严谨但P0问题需修(per-dimension Kappa+分类规则)"],
        ["文献对话", "7.0", "覆盖广但有P1缺口"],
        ["论证说服力", "7.5", "逻辑链完整但证据强度匹配需微调"],
        ["写作质量", "8.5", "高水平学术英文"],
        ["JCR适配度", "7.0", "好但需更突出宗教核心性"],
    ],
    col_widths=[1.5, 0.8, 4.2]
)

add_para("")
add_para("综合评分: 7.5/10", bold=True, size=14, color=RGBColor(0x1A, 0x23, 0x7E))

# Final lists
add_title("", level=2)
add_para("🔴 P0（必须修，否则致命）", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
p0_items = [
    "1. 报告各编码维度的独立Kappa值 — 13维度信度可能差异巨大",
    "2. 补充分类优先规则的稳健性检验 — 用不同优先级重算类型比例",
    "3. 补充游戏-宗教交叉文献（Campbell & Grieve 2014, Bainbridge 2013等）",
]
for item in p0_items:
    add_bullet(item, color=RGBColor(0xD3, 0x2F, 0x2F))

add_para("")
add_para("🟡 P1（强烈建议修，否则影响接受概率）", bold=True, color=RGBColor(0xE6, 0x5C, 0x00))
p1_items = [
    "4. 补充中国宗教社会学文献(Goossaert & Palmer 2011; Chau 2006)",
    "5. 新闻报道补充访问日期",
    "6. Discussion弱化\"corrective\"语气，改为\"extension/refinement\"",
    "7. 增加竞争假说(\"打卡文化\"解释)的讨论",
    "8. 统一中文作者名格式",
    "9. 在Introduction/Discussion中加强宗教研究理论权重(30%→50%)",
]
for item in p1_items:
    add_bullet(item, color=RGBColor(0xE6, 0x5C, 0x00))

add_para("")
add_para("🟢 P2（可选的未来方向/二次修改）", bold=True, color=RGBColor(0x2E, 0x7D, 0x32))
p2_items = [
    "10. 补充χ²检验验证站点-游戏元素关联",
    "11. 补充交叉表(类型×站点)",
    "12. 拆分高密度段落",
    "13. 统一术语全称/缩写",
]
for item in p2_items:
    add_bullet(item, color=RGBColor(0x2E, 0x7D, 0x32))

add_separator()

# ── FINAL VERDICT ──
add_title("📝 总评", level=1)

add_para("这是一篇高质量的论文。7.5/10意味着在P0+P1修复后可投JCR，接受概率约50-60%。", bold=True, size=11)

add_para("")
add_para("最大优势：", bold=True)
for s in ["GTP概念原创，交叉三个理论框架",
          "对Hjarvard\"平庸宗教\"论的反向观察是扎实的贡献",
          "英文写作水平高，方法论记录完整"]:
    add_bullet("🏆 " + s)

add_para("")
add_para("最大短板：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
for s in ["方法论文档有P0漏洞(per-dimension Kappa缺失+分类规则的人为构造性)",
          "理论声明有时超出证据强度(关联↔因果)",
          "作为JCR投稿，宗教理论权重需从30%提高到50%"]:
    add_bullet("⚠️ " + s)

add_para("")
add_para("一句话建议：补per-dimension Kappa和游戏-宗教文献(2天可完成) → Discussion调语气(1天) → 审稿人推荐完成 → 可投JCR。祝顺利！", bold=True, size=12, color=RGBColor(0x1A, 0x23, 0x7E))

add_para("")
add_para("—— LEO 🦁 | 2026-06-12", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

# ── Save ──
output_path = "/Users/lyu/Desktop/GTP_唐太宗李世民完整评审报告.docx"
doc.save(output_path)
print(f"✅ Saved to: {output_path}")
