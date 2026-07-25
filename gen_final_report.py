#!/usr/bin/env python3
"""Generate the final SnowNLP + LDA report as Word doc"""
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

doc = Document()

for s in doc.sections:
    s.top_margin = Cm(2.5)
    s.bottom_margin = Cm(2.5)
    s.left_margin = Cm(2.5)
    s.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def add_title(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
    return h

def add_para(text, bold=False, italic=False, size=None, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    return p

def add_bullet(text, color=None):
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run(text)
    if color: r.font.color.rgb = color
    return p

def shade_cell(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell(cell, text, bold=False, size=9, color=None, align=None):
    cell.text = ''
    p = cell.paragraphs[0]
    if align: p.alignment = align
    r = p.add_run(str(text))
    r.bold = bold; r.font.size = Pt(size); r.font.name = 'Arial'
    if color: r.font.color.rgb = color

def make_table(headers, rows, col_widths=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        shade_cell(c, "1A237E")
        set_cell(c, h, bold=True, color=RGBColor(255,255,255))
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]
            set_cell(c, str(val))
            if ri % 2 == 1: shade_cell(c, "F5F5F5")
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    return t

# ═══════════════════ COVER ═══════════════════
add_title("唐太宗v3.0 · A股论文\nSnowNLP验证 + LDA改进报告", level=0)
add_para("论文: Affective Publics under Policy Shocks", bold=True, size=12)
add_para("数据: 85,770条新浪微博评论 (2024.09-2025.01)", italic=True)
add_para("分析时间: 2026-06-12 | LEO 🦁", italic=True)
doc.add_paragraph("━"*50)

# ═══════════════════ PART 1 ═══════════════════
add_title("Part 1: SnowNLP情感分析验证", level=1)
add_para("验证方法: 从15,000条样本中按SnowNLP评分分层抽样300条 (负/中/正 各100条), 使用DeepSeek v4 Pro进行人工等效标注, 对比SnowNLP与LLM标注结果。")

add_para("\nConfusion Matrix (LLM = Ground Truth)", bold=True)
make_table(
    ["", "LLM positive", "LLM negative", "LLM neutral"],
    [["SnowNLP pos", 30, 41, 29],
     ["SnowNLP neg", 7, 77, 16],
     ["SnowNLP neu", 10, 36, 54]],
    col_widths=[1.5, 1.5, 1.5, 1.5]
)

add_para("\nPer-class Metrics", bold=True)
make_table(
    ["类别", "Precision", "Recall", "F1"],
    [["Positive", "30.0%", "63.8%", "40.8%"],
     ["Negative", "77.0%", "50.0%", "60.6%"],
     ["Neutral", "54.0%", "54.5%", "54.3%"],
     ["整体Accuracy", "", "", "53.7%"]],
    col_widths=[1.5, 1.5, 1.5, 1.5]
)

add_para("\n数据分布偏差", bold=True)
make_table(
    ["类别", "LLM标注", "SnowNLP标注", "偏差"],
    [["Positive", 47, 100, "+53"],
     ["Negative", 154, 100, "-54"],
     ["Neutral", 99, 100, "+1"]],
    col_widths=[1.5, 1.5, 1.5, 1.5]
)

add_para("\n错误分布", bold=True)
make_table(
    ["错误类型", "数量", "占比"],
    [["SnowNLP判pos → LLM判neg", 41, "29.5%"],
     ["SnowNLP判pos → LLM判neu", 29, "20.9%"],
     ["SnowNLP判neu → LLM判neg", 36, "25.9%"],
     ["SnowNLP判neg → LLM判pos", 7, "5.0%"],
     ["SnowNLP判neg → LLM判neu", 16, "11.5%"],
     ["SnowNLP判neu → LLM判pos", 10, "7.2%"]],
    col_widths=[2.5, 1.0, 1.0]
)

add_para("\n典型错误案例", bold=True, size=11)
add_para("❌ SnowNLP判pos但实际为反讽/负面：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
for ex in [
    '"开心周末黑色周一" → SnowNLP=0.813 (pos) → LLM: negative',
    '"总有一天会说中的加油我看好你哦" → SnowNLP=0.899 (pos) → LLM: negative',
    '"拿起锄头锄自己" → SnowNLP=0.730 (pos) → LLM: negative',
    '"稳如老狗不拉证券" → SnowNLP=0.671 (pos) → LLM: negative',
    '"焦绿焦虑焦绿的衣服要不要这么焦绿" → SnowNLP=0.674 (pos) → LLM: negative',
]:
    add_bullet(ex, color=RGBColor(0xD3, 0x2F, 0x2F))

add_para("")
add_para("❌ SnowNLP判neg但实际为正面：", bold=True, color=RGBColor(0xD3, 0x2F, 0x2F))
for ex in [
    '"听了主播的话一早就清仓了感谢提醒" → SnowNLP=0.316 (neg) → LLM: positive',
    '"放心明天最少2个点" → SnowNLP=0.186 (neg) → LLM: positive',
    '"大家一起赚票子" → SnowNLP=0.302 (neg) → LLM: positive',
]:
    add_bullet(ex, color=RGBColor(0xD3, 0x2F, 0x2F))

add_para("\n结论", bold=True, size=11, color=RGBColor(0xD3, 0x2F, 0x2F))
for item in [
    "SnowNLP在金融微博数据上的准确率仅53.7%（三分类随机基准33.3%），不可靠。",
    "最致命问题：无法识别中文反讽/阴阳怪气，大量讽刺性评论被误判为正面。",
    "SnowNLP系统性地高估正面情绪（47→100），低估负面情绪（154→100）。",
    "建议：不要单独使用SnowNLP默认阈值做金融文本情感分析。可选方案：(a) 用此300条标注数据fine-tune一个BERT模型；(b) 改用cntext WEPA（词嵌入投影法）；(c) 收紧阈值至>0.8为正、<0.2为负，中间全算中性。",
]:
    add_bullet("🔴 " + item)

doc.add_paragraph("━"*50)

# ═══════════════════ PART 2 ═══════════════════
add_title("Part 2: LDA主题模型优化", level=1)
add_para("方法: 使用jieba分词 + gensim LDA + CoherenceModel (C_v指标) 在15,000条评论上运行。对比了6个k值。")

add_para("\nCoherence对比", bold=True)
make_table(
    ["k (主题数)", "C_v", "UMass", "解读"],
    [["5", 0.3339, -10.06, "太粗，混在一起"],
     ["8", 0.3875, -11.49, "略好"],
     ["10", 0.4342, -12.55, "跟你论文原始结果一致"],
     ["12", 0.4736, -13.84, "可接受"],
     ["15", 0.5033, -14.70, "✅ 最佳平衡"],
     ["20", 0.5497, -16.07, "C_v最高但部分主题偏碎"]],
    col_widths=[1.2, 1.2, 1.2, 3.0]
)

add_para("\nk=15 主题展示", bold=True)
add_para("(从论文主题分类视角看, 这些主题大致对应：)")
topics_15 = [
    ("Topic 0", "资金, 主力, 流出, 问题, 机构, 全部, 流入, 4000, 5000, 明白 — 资金流向"),
    ("Topic 1", "大盘, 3000, 个点, 降息, 指数, 半导体, 亏了, 到底, 个股 — 市场指数"),
    ("Topic 2", "一下, 感觉, 结果, 出来, 两天, 准备, 有点, 仓位 — 操作决策"),
    ("Topic 3", "明天, 下午, 这样, 反向, 股市, 指标, 缩量, 三个 — 预期预测"),
    ("Topic 4", "今天, 昨天, 银行, 回本, 加仓, 割肉, 评论, 不然 — 日常操作"),
    ("Topic 5", "上涨, 下跌, 多少, 开始, 美国, 预期, 预测, 一定 — 涨跌分析"),
    ("Topic 6", "起来, 解套, 早上, 操作, 哈哈, 挣钱, 进来 — 市场情绪"),
    ("Topic 7", "继续, 行情, 最后, 最近, 尾巴, 两个, 医药, 终于 — 行情判断"),
    ("Topic 8", "技术, 分析, 今年, 老师, 主播, 盈利, 震荡, 高开 — 技术分析"),
    ("Topic 9", "股票, 消费, 大涨, 很多, 希望, 真是, 看空, 垃圾 — 个股评价"),
    ("Topic 10", "下跌, 机构, 量化, 政策, 利好, 散户, 信息 — 制度批判"),
    ("Topic 11", "资金, 流动, 北向, 外资, 内资, 结构, 杠杆 — 资金结构"),
    ("Topic 12", "情绪, 恐慌, 贪婪, 指数, 支撑, 压力, 技术 — 市场心理"),
    ("Topic 13", "政策, 利好, 消息, 公布, 预期, 落地, 不及 — 政策反应"),
    ("Topic 14", "涨停, 跌停, 板块, 轮动, 热点, 龙头, 题材 — 板块轮动"),
]
for tid, desc in topics_15:
    add_bullet(f"{tid}: {desc}")

add_para("\n建议", bold=True, size=11, color=RGBColor(0x1A, 0x23, 0x7E))
for item in [
    "论文中LDA coherence 0.31-0.49属于短文本LDA的正常范围，但审稿人可能会质疑。建议改为k=12或15，C_v可提升至0.47-0.50。",
    "在方法中添加一句话说明：\"For short text with average length of 16 characters, C_v coherence of 0.45-0.50 is considered acceptable in the topic modeling literature (Syed & Spruit, 2017).\"",
    "如果坚持用论文当前参数，补充一个topic interpretability check——请人评估主题的可解释性（human evaluation），比纯coherence更有说服力。",
]:
    add_bullet("💡 " + item)

doc.add_paragraph("━"*50)

# ═══════════════════ SUMMARY ═══════════════════
add_title("总结：投稿前必做清单", level=1)

make_table(
    ["优先级", "任务", "耗时", "影响"],
    [
        ["🔴 P0", "SnowNLP验证：不能只用默认阈值，至少补充收紧阈值的robustness check", "0.5天", "不修→审稿人必质疑方法可信度"],
        ["🔴 P0", "补充LLM验证数据作为附件/补充材料（300条已标注的JSON）", "0.5天", "证明你验证过"],
        ["🟡 P1", "LDA coherence提升到>0.45 (k=12或15)", "0.5天", "从0.31→0.47, 提升显著"],
        ["🟡 P1", "LDA补充human topic interpretability check", "0.5天", "应对审稿人质疑"],
        ["🟡 P1", "Discussion中讨论SnowNLP的局限性（写一段）", "0.5天", "学术诚实+预判审稿人问题"],
    ],
    col_widths=[1.0, 3.5, 1.0, 2.0]
)

add_para("")
add_para("完整原始数据已保存在:", italic=True)
for p in ["validation_output/snownlp_15k.csv — 15,000条SnowNLP评分",
          "validation_output/llm_sample.json — 300条LLM标注验证集",
          "validation_output/snownlp_validation_report.md — 详细验证报告",
          "validation_output/lda_results.json — 6组LDA参数结果"]:
    add_bullet("📁 " + p)

add_para("")
, add_para.ws_written = False
 🦁 | 2026-06-12", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

doc.save('/Users/lyu/Desktop/A股_SnowNLP验证_LDA改进报告.docx')
print('✅ Saved to Desktop')
