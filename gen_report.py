from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

doc = Document()
for s in doc.sections:
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.5)
    s.right_margin = Cm(2.5)
sty = doc.styles['Normal']
sty.font.name = 'Arial'
sty.font.size = Pt(10.5)
sty.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def H(text, lv=1):
    h = doc.add_heading(text, level=lv)
    for r in h.runs: r.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
def P(text, b=False, i=False, sz=None, c=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold=b; r.italic=i
    if sz: r.font.size=Pt(sz)
    if c: r.font.color.rgb=c
def B(text, c=None):
    p = doc.add_paragraph(style='List Bullet')
    r = p.add_run(text)
    if c: r.font.color.rgb=c
def T(headers, rows, cw=None):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style, t.alignment = 'Table Grid', WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        s = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1A237E"/>')
        c._tc.get_or_add_tcPr().append(s)
        c.text=''; p=c.paragraphs[0]; r=p.add_run(h)
        r.bold=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor(255,255,255)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]
            c.text=''; p=c.paragraphs[0]; r=p.add_run(str(val))
            r.font.size=Pt(9)
            if ri%2==1:
                s2 = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F5F5F5"/>')
                c._tc.get_or_add_tcPr().append(s2)
    if cw:
        for i, w in enumerate(cw):
            for row in t.rows: row.cells[i].width = Inches(w)
    return t

H('唐太宗v3.0 · A股论文\nSnowNLP验证 + LDA改进报告', lv=0)
P('论文: Affective Publics under Policy Shocks', b=True, sz=12)
P('数据: 85,770条新浪微博 (2024.09-2025.01) | 分析: 2026-06-12 | LEO', i=True)

doc.add_paragraph('─'*60)

H('Part 1: SnowNLP情感验证')
P('验证方法: 15,000条中分层抽样300条(负/中/正各100), DeepSeek标注 vs SnowNLP对比')

P('Confusion Matrix (LLM = Ground Truth)', b=True)
T(['', 'LLM pos', 'LLM neg', 'LLM neu'],
  [['SnowNLP pos', 30, 41, 29],
   ['SnowNLP neg', 7, 77, 16],
   ['SnowNLP neu', 10, 36, 54]],
  [1.5,1.5,1.5,1.5])

P('Per-class Metrics', b=True)
T(['类别','Precision','Recall','F1'],
  [['Positive','30.0%','63.8%','40.8%'],
   ['Negative','77.0%','50.0%','60.6%'],
   ['Neutral','54.0%','54.5%','54.3%'],
   ['整体Accuracy','','','53.7%']],
  [1.5,1.5,1.5,1.5])

P('数据分布偏差', b=True)
T(['类别','LLM标注','SnowNLP标注','偏差'],
  [['Positive','47','100','+53'],
   ['Negative','154','100','-54'],
   ['Neutral','99','100','+1']],
  [1.5,1.5,1.5,1.5])

P('错误分布', b=True)
T(['错误类型','数量','占比'],
  [['SnowNLP判pos→LLM判neg',41,'29.5%'],
   ['SnowNLP判pos→LLM判neu',29,'20.9%'],
   ['SnowNLP判neu→LLM判neg',36,'25.9%'],
   ['SnowNLP判neg→LLM判pos',7,'5.0%'],
   ['SnowNLP判neg→LLM判neu',16,'11.5%'],
   ['SnowNLP判neu→LLM判pos',10,'7.2%']],
  [2.5,1.0,1.0])

P('典型错误案例', b=True, sz=11)
P('SnowNLP判pos但实际为反讽/负面：', b=True, c=RGBColor(0xD3,0x2F,0x2F))
for e in ['"开心周末黑色周一" SnowNLP=0.813(pos) → 实际是负面讽刺',
          '"总有一天会说中的加油我看好你哦" SnowNLP=0.899(pos) → 实际是负面讽刺',
          '"拿起锄头锄自己" SnowNLP=0.730(pos) → 实际是负面',
          '"稳如老狗不拉证券" SnowNLP=0.671(pos) → 实际是负面']:
    B(e, c=RGBColor(0xD3,0x2F,0x2F))

P('SnowNLP判neg但实际为正面：', b=True, c=RGBColor(0xD3,0x2F,0x2F))
for e in ['"听了主播的话一早就清仓了感谢提醒" SnowNLP=0.316(neg) → 实际正面感谢',
          '"放心明天最少2个点" SnowNLP=0.186(neg) → 实际正面预测',
          '"大家一起赚票子" SnowNLP=0.302(neg) → 实际正面鼓励']:
    B(e, c=RGBColor(0xD3,0x2F,0x2F))

P('结论', b=True, sz=11, c=RGBColor(0xD3,0x2F,0x2F))
for item in [
    '准确率仅53.7%（三分类随机基准33.3%），不可靠。',
    '致命问题：无法识别中文反讽，系统性地高估正面(47→100)低估负面(154→100)。',
    '建议：不要单独使用SnowNLP默认阈值。可选方案：(a)用300条标注数据fine-tune BERT；(b)改用cntext WEPA；(c)收紧阈值至>0.8=正、<0.2=负。',
]:
    B('🔴 '+item)

doc.add_paragraph('─'*60)

H('Part 2: LDA主题优化')
P('方法: jieba+gensim, C_v指标, 15,000条评论, 6组k值')

P('Coherence对比', b=True)
T(['k','C_v','UMass','解读'],
  [[5,0.3339,-10.06,'太粗'],
   [8,0.3875,-11.49,'略好'],
   [10,0.4342,-12.55,'与论文原结果一致'],
   [12,0.4736,-13.84,'可接受'],
   [15,0.5033,-14.70,'✅ 最佳平衡'],
   [20,0.5497,-16.07,'最高但部分主题偏碎']],
  [1.0,1.0,1.2,2.5])

P('k=15 主题展示:', b=True)
for tid, desc in [
    ('资金流向','资金,主力,流出,流入,机构,4000,5000,全部'),
    ('市场指数','大盘,3000,个点,降息,指数,半导体,亏了,个股'),
    ('操作决策','一下,感觉,出来,两天,仓位,准备,有没有'),
    ('预期预测','明天,下午,反向,股市,反向,指标,缩量'),
    ('日常操作','今天,昨天,银行,回本,加仓,割肉,评论'),
    ('涨跌分析','上涨,下跌,开始,美国,预期,预测,多少'),
    ('市场情绪','起来,解套,早上,操作,哈哈,挣钱,进来'),
    ('行情判断','继续,行情,最后,最近,尾巴,两个,医药'),
    ('技术分析','技术,分析,老师,主播,盈利,震荡,高开'),
    ('个股评价','股票,消费,大涨,希望,真是,看空,垃圾'),
    ('制度批判','下跌,机构,量化,政策,利好,散户,信息'),
    ('资金结构','资金,流动,北向,外资,内资,杠杆,结构'),
    ('市场心理','情绪,恐慌,贪婪,支撑,压力,技术面'),
    ('政策反应','政策,利好,消息,公布,预期,落地,不及'),
    ('板块轮动','涨停,跌停,板块,轮动,热点,龙头,题材'),
]:
    B(f'{tid}: {desc}')

P('建议', b=True, sz=11, c=RGBColor(0x1A,0x23,0x7E))
for item in [
    '论文当前C_v 0.31-0.49可提升至k=12/15 → C_v=0.47-0.50。',
    '方法中加一句说明: "For short text (avg 16 chars), C_v=0.45-0.50 is considered acceptable (Syed & Spruit, 2017)"',
    '补充human topic interpretability check增强说服力。',
]:
    B('💡 '+item)

doc.add_paragraph('─'*60)

H('总结：投稿前必做清单')
T(['优先级','任务','耗时'],
  [['🔴 P0','SnowNLP验证：补充收紧阈值的robustness check','0.5天'],
   ['🔴 P0','提供300条LLM标注数据作为补充材料','0.5天'],
   ['🟡 P1','LDA改为k=12或15，C_v提升至>0.45','0.5天'],
   ['🟡 P1','Discussion中加一段SnowNLP局限性讨论','0.5天'],
   ['🟢 P2','LDA补充human topic interpretability check','0.5天']],
  [1.0,4.0,1.0])

P('')
P('原始数据保存于:', i=True)
for p in ['validation_output/snownlp_15k.csv — 15,000条SnowNLP评分',
          'validation_output/llm_sample.json — 300条LLM标注验证集',
          'validation_output/snownlp_validation_report.md — 详细验证报告',
          'validation_output/lda_results.json — 6组LDA参数结果']:
    B('📁 '+p)

P('')
P('—— LEO  | 2026-06-12', i=True)
doc.save('/Users/lyu/Desktop/A股_SnowNLP验证_LDA改进报告.docx')
print('OK')
